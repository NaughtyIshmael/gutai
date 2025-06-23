import os
import sys
import json
import ast
import re
import builtins
import pytest
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock, patch

import scripts.generate_tests as generate_tests


@pytest.fixture
def sample_python_code():
    return """
class MyClass:
    def method(self):
        pass

def public_function():
    pass

def _private_function():
    pass

def test_function():
    pass
"""


@pytest.fixture
def sample_js_code():
    return """
function publicFunction() {}
function _privateFunction() {}
class MyClass {}
function testFunction() {}
"""


@pytest.fixture
def sample_invalid_python_code():
    return "def broken_func(:\n    pass"


class TestGitHubModelsClient:
    @patch("scripts.generate_tests.ChatCompletionsClient")
    def test_generate_completion_success(self, mock_client_cls):
        mock_client = mock_client_cls.return_value
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "test code"
        mock_client.complete.return_value = mock_response

        client = generate_tests.GitHubModelsClient("fake_token")
        result = client.generate_completion("prompt")

        mock_client.complete.assert_called_once()
        assert result == "test code"

    @patch("scripts.generate_tests.ChatCompletionsClient")
    def test_generate_completion_raises_exception(self, mock_client_cls):
        mock_client = mock_client_cls.return_value
        mock_client.complete.side_effect = Exception("API error")

        client = generate_tests.GitHubModelsClient("fake_token")
        with pytest.raises(Exception) as excinfo:
            client.generate_completion("prompt")
        assert "GitHub Models API error" in str(excinfo.value)


class TestSourceCodeAnalyzer:
    def test_read_file_success(tmp_path):
        file = tmp_path / "test.py"
        file.write_text("print('hello')")
        analyzer = generate_tests.SourceCodeAnalyzer(str(file))
        assert analyzer.content == "print('hello')"

    def test_read_file_raises_exception(tmp_path):
        file = tmp_path / "nonexistent.py"
        with pytest.raises(Exception) as excinfo:
            generate_tests.SourceCodeAnalyzer(str(file))
        assert "Error reading file" in str(excinfo.value)

    @pytest.mark.parametrize(
        "filename,expected_language",
        [
            ("file.py", "python"),
            ("file.js", "javascript"),
            ("file.jsx", "javascript"),
            ("file.ts", "typescript"),
            ("file.tsx", "typescript"),
            ("file.java", "java"),
            ("file.cpp", "cpp"),
            ("file.cc", "cpp"),
            ("file.cxx", "cpp"),
            ("file.c", "c"),
            ("file.cs", "csharp"),
            ("file.go", "go"),
            ("file.rs", "rust"),
            ("file.rb", "ruby"),
            ("file.php", "php"),
            ("file.unknown", "unknown"),
        ],
    )
    def test_detect_language(filename, expected_language, tmp_path):
        file = tmp_path / filename
        file.write_text("")
        analyzer = generate_tests.SourceCodeAnalyzer(str(file))
        assert analyzer.language == expected_language

    def test_extract_python_elements(sample_python_code, tmp_path):
        file = tmp_path / "test.py"
        file.write_text(sample_python_code)
        analyzer = generate_tests.SourceCodeAnalyzer(str(file))
        elements = analyzer.extract_code_elements()
        assert "MyClass" in elements["classes"]
        assert "public_function" in elements["functions"]
        assert "_private_function" not in elements["functions"]
        assert "test_function" not in elements["functions"]

    def test_extract_python_elements_syntax_error(sample_invalid_python_code, tmp_path):
        file = tmp_path / "broken.py"
        file.write_text(sample_invalid_python_code)
        analyzer = generate_tests.SourceCodeAnalyzer(str(file))
        elements = analyzer.extract_code_elements()
        # Should fallback to generic extraction (empty here)
        assert isinstance(elements, dict)
        assert "classes" in elements
        assert "functions" in elements

    def test_extract_generic_elements_filters_tests(sample_js_code, tmp_path):
        file = tmp_path / "test.js"
        file.write_text(sample_js_code)
        analyzer = generate_tests.SourceCodeAnalyzer(str(file))
        analyzer.language = "javascript"
        elements = analyzer._extract_generic_elements()
        assert "publicFunction" in elements["functions"]
        assert "testFunction" not in elements["functions"]
        assert "MyClass" in elements["classes"]

    def test_extract_generic_elements_duplicates_and_filters(tmp_path):
        content = """
        def func1() {}
        def func1() {}
        class TestClass {}
        class MyClass {}
        """
        file = tmp_path / "test.js"
        file.write_text(content)
        analyzer = generate_tests.SourceCodeAnalyzer(str(file))
        analyzer.language = "javascript"
        elements = analyzer._extract_generic_elements()
        assert elements["functions"].count("func1") == 1
        assert "TestClass" not in elements["classes"]
        assert "MyClass" in elements["classes"]


class TestTestGenerator:
    @patch("scripts.generate_tests.GitHubModelsClient")
    def test_generate_tests_with_ai_client_and_prompt(self, mock_client_cls, sample_python_code, tmp_path):
        mock_client = mock_client_cls.return_value
        mock_client.generate_completion.return_value = "generated test code"

        generator = generate_tests.TestGenerator(github_token="token")
        result = generator.generate_tests(
            file_path=str(tmp_path / "file.py"),
            source_code=sample_python_code,
            prompt="custom prompt",
        )
        mock_client.generate_completion.assert_called_once_with("custom prompt", "openai/gpt-4.1-mini")
        assert result == "generated test code"

    def test_generate_tests_without_ai_client_returns_mock(sample_python_code, tmp_path):
        generator = generate_tests.TestGenerator()
        result = generator.generate_tests(
            file_path=str(tmp_path / "file.py"),
            source_code=sample_python_code,
        )
        assert result.startswith("# Mock test generated")

    @patch("scripts.generate_tests.SourceCodeAnalyzer")
    @patch("scripts.generate_tests.GitHubModelsClient")
    def test_generate_tests_default_prompt(self, mock_client_cls, mock_analyzer_cls, tmp_path):
        mock_client = mock_client_cls.return_value
        mock_client.generate_completion.return_value = "generated test code"

        mock_analyzer = mock_analyzer_cls.return_value
        mock_analyzer.language = "python"
        mock_analyzer.extract_code_elements.return_value = {"functions": ["func"], "classes": ["Cls"]}
        mock_analyzer.content = "code"

        generator = generate_tests.TestGenerator(github_token="token")
        result = generator.generate_tests(
            file_path=str(tmp_path / "file.py"),
            source_code="code",
        )
        assert "generated test code" == result
        mock_client.generate_completion.assert_called_once()

    def test_generate_tests_for_file_file_not_exist(self):
        generator = generate_tests.TestGenerator()
        with pytest.raises(Exception) as excinfo:
            generator.generate_tests_for_file("nonexistent.py", 50)
        assert "Source file does not exist" in str(excinfo.value)

    def test_generate_tests_for_file_no_elements(tmp_path):
        file = tmp_path / "empty.py"
        file.write_text("")

        generator = generate_tests.TestGenerator(github_token="token")
        with patch.object(generate_tests.SourceCodeAnalyzer, "extract_code_elements", return_value={"functions": [], "classes": []}):
            with pytest.raises(Exception) as excinfo:
                generator.generate_tests_for_file(str(file), 50)
            assert "No testable elements found" in str(excinfo.value)

    @patch("scripts.generate_tests.GitHubModelsClient")
    def test_generate_tests_for_file_success(self, mock_client_cls, tmp_path):
        file = tmp_path / "file.py"
        file.write_text("def func(): pass")

        mock_client = mock_client_cls.return_value
        mock_client.generate_completion.return_value = "```python\nprint('test')\n```"

        generator = generate_tests.TestGenerator(github_token="token")
        with patch.object(generate_tests.SourceCodeAnalyzer, "extract_code_elements", return_value={"functions": ["func"], "classes": []}):
            test_code = generator.generate_tests_for_file(str(file), 75, test_framework="pytest")
            assert "print('test')" in test_code
            assert not test_code.startswith("```")

    def test_generate_tests_for_file_no_ai_client_raises(self, tmp_path):
        file = tmp_path / "file.py"
        file.write_text("def func(): pass")

        generator = generate_tests.TestGenerator()
        with patch.object(generate_tests.SourceCodeAnalyzer, "extract_code_elements", return_value={"functions": ["func"], "classes": []}):
            with pytest.raises(Exception) as excinfo:
                generator.generate_tests_for_file(str(file), 75)
            assert "GitHub token required" in str(excinfo.value)

    @pytest.mark.parametrize(
        "language,expected_framework",
        [
            ("python", "pytest"),
            ("javascript", "jest"),
            ("typescript", "jest"),
            ("java", "junit"),
            ("csharp", "nunit"),
            ("go", "testing"),
            ("rust", "builtin"),
            ("ruby", "rspec"),
            ("php", "phpunit"),
            ("unknown", "default"),
        ],
    )
    def test_detect_test_framework(language, expected_framework):
        generator = generate_tests.TestGenerator()
        assert generator._detect_test_framework(language) == expected_framework

    def test_create_test_generation_prompt_contains_expected_parts(self):
        generator = generate_tests.TestGenerator()
        prompt = generator._create_test_generation_prompt(
            source_code="code",
            language="python",
            elements={"functions": ["func1"], "classes": ["Cls1"]},
            coverage_percentage=80.0,
            file_path="file.py",
            test_framework="pytest",
        )
        assert "func1" in prompt
        assert "Cls1" in prompt
        assert "80.0%" in prompt
        assert "pytest" in prompt
        assert "Generate comprehensive unit tests" in prompt

    def test_clean_generated_code_removes_markdown(self):
        generator = generate_tests.TestGenerator()
        code = "```python\nprint('hello')\n```"
        cleaned = generator._clean_generated_code(code)
        assert cleaned == "print('hello')"

        code2 = "```\nprint('hello')\n```"
        cleaned2 = generator._clean_generated_code(code2)
        assert cleaned2 == "print('hello')"

        code3 = "print('hello')"
        cleaned3 = generator._clean_generated_code(code3)
        assert cleaned3 == "print('hello')"

    def test_determine_test_file_path_python(tmp_path):
        source_file = tmp_path / "module.py"
        source_file.write_text("")

        generator = generate_tests.TestGenerator()
        test_path = generator.determine_test_file_path(str(source_file))
        test_path_obj = Path(test_path)

        assert test_path_obj.name == f"test_{source_file.name}"
        assert test_path_obj.parent.exists()

    def test_determine_test_file_path_js(tmp_path):
        for ext in [".js", ".ts", ".jsx", ".tsx"]:
            source_file = tmp_path / f"file{ext}"
            source_file.write_text("")
            generator = generate_tests.TestGenerator()
            test_path = generator.determine_test_file_path(str(source_file))
            test_path_obj = Path(test_path)
            assert test_path_obj.name == f"{source_file.stem}.test{ext}"
            assert test_path_obj.parent.exists()

    def test_determine_test_file_path_java(tmp_path):
        source_file = tmp_path / "MyClass.java"
        source_file.write_text("")
        generator = generate_tests.TestGenerator()
        test_path = generator.determine_test_file_path(str(source_file))
        test_path_obj = Path(test_path)
        assert test_path_obj.name == f"Test{source_file.stem}.java"
        assert test_path_obj.parent.exists()

    def test_determine_test_file_path_generic(tmp_path):
        source_file = tmp_path / "file.xyz"
        source_file.write_text("")
        generator = generate_tests.TestGenerator()
        test_path = generator.determine_test_file_path(str(source_file))
        test_path_obj = Path(test_path)
        assert test_path_obj.name == f"test_{source_file.name}"
        assert test_path_obj.parent.exists()


class TestMainFunction:
    @patch("scripts.generate_tests.os.getenv")
    @patch("scripts.generate_tests.open", new_callable=mock.mock_open, read_data='{"least_covered_files": [{"filename": "file.py", "coverage": 20.0}]}')
    @patch("scripts.generate_tests.Path.mkdir")
    @patch("scripts.generate_tests.TestGenerator")
    @patch("scripts.generate_tests.print")
    def test_main_success(
        self,
        mock_print,
        mock_test_generator_cls,
        mock_mkdir,
        mock_open,
        mock_getenv,
        tmp_path,
    ):
        mock_getenv.return_value = "fake_token"
        mock_test_generator = mock_test_generator_cls.return_value
        mock_test_generator.generate_tests_for_file.return_value = "test code"
        mock_test_generator.determine_test_file_path.return_value = str(tmp_path / "test_file.py")

        test_argv = [
            "generate_tests.py",
            "--coverage-data",
            "coverage.json",
            "--max-files",
            "1",
            "--test-framework",
            "pytest",
            "--ai-model",
            "openai/gpt-4.1-mini",
            "--output-dir",
            str(tmp_path),
            "--output-format",
            "json",
        ]

        with patch.object(sys, "argv", test_argv):
            generate_tests.main()

        mock_test_generator.generate_tests_for_file.assert_called_once_with("file.py", 20.0, "pytest")
        mock_test_generator.determine_test_file_path.assert_called_once_with("file.py")
        mock_print.assert_any_call("\nGeneration complete!")

        summary_file = tmp_path / "summary.json"
        assert summary_file.exists()
        with open(summary_file) as f:
            summary = json.load(f)
        assert summary["files_processed"] == 1
        assert summary["tests_generated"] == 1
        assert summary["generated_files"][0]["source_file"] == "file.py"

    @patch("scripts.generate_tests.os.getenv")
    @patch("scripts.generate_tests.print")
    def test_main_missing_github_token(self, mock_print, mock_getenv):
        mock_getenv.return_value = None
        test_argv = [
            "generate_tests.py",
            "--coverage-data",
            "coverage.json",
        ]
        with patch.object(sys, "argv", test_argv):
            with pytest.raises(SystemExit):
                generate_tests.main()
        mock_print.assert_any_call("Error: GITHUB_TOKEN environment variable is required")

    @patch("scripts.generate_tests.os.getenv")
    @patch("scripts.generate_tests.open", new_callable=mock.mock_open, read_data="invalid json")
    @patch("scripts.generate_tests.print")
    def test_main_invalid_coverage_data(self, mock_print, mock_open, mock_getenv):
        mock_getenv.return_value = "token"
        test_argv = [
            "generate_tests.py",
            "--coverage-data",
            "coverage.json",
        ]
        with patch.object(sys, "argv", test_argv):
            with pytest.raises(SystemExit):
                generate_tests.main()
        mock_print.assert_any_call(mock.ANY)

    @patch("scripts.generate_tests.os.getenv")
    @patch("scripts.generate_tests.open", new_callable=mock.mock_open, read_data='{"least_covered_files": []}')
    @patch("scripts.generate_tests.Path.mkdir")
    @patch("scripts.generate_tests.print")
    def test_main_no_files_to_process(self, mock_print, mock_mkdir, mock_open, mock_getenv, tmp_path):
        mock_getenv.return_value = "token"
        test_argv = [
            "generate_tests.py",
            "--coverage-data",
            "coverage.json",
            "--output-dir",
            str(tmp_path),
        ]
        with patch.object(sys, "argv", test_argv):
            generate_tests.main()
        summary_file = tmp_path / "summary.json"
        assert summary_file.exists()
        with open(summary_file) as f:
            summary = json.load(f)
        assert summary["files_processed"] == 0
        assert summary["tests_generated"] == 0
        mock_print.assert_any_call("No files to process")

    @patch("scripts.generate_tests.os.getenv")
    @patch("scripts.generate_tests.open", new_callable=mock.mock_open, read_data='{"least_covered_files": [{"filename": "file.py", "coverage": 20.0}]}')
    @patch("scripts.generate_tests.Path.mkdir")
    @patch("scripts.generate_tests.TestGenerator")
    @patch("scripts.generate_tests.print")
    def test_main_error_generating_tests_continues(
        self,
        mock_print,
        mock_test_generator_cls,
        mock_mkdir,
        mock_open,
        mock_getenv,
        tmp_path,
    ):
        mock_getenv.return_value = "fake_token"
        mock_test_generator = mock_test_generator_cls.return_value
        mock_test_generator.generate_tests_for_file.side_effect = Exception("generation error")

        test_argv = [
            "generate_tests.py",
            "--coverage-data",
            "coverage.json",
            "--max-files",
            "1",
            "--output-dir",
            str(tmp_path),
        ]

        with patch.object(sys, "argv", test_argv):
            generate_tests.main()

        mock_print.assert_any_call("Error generating tests for file.py: generation error")
        summary_file = tmp_path / "summary.json"
        assert summary_file.exists()
        with open(summary_file) as f:
            summary = json.load(f)
        assert summary["files_processed"] == 0