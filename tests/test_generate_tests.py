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

import scripts.generate_tests as gen


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
    return "def broken(:\n    pass"


class TestGitHubModelsClient:
    @patch("scripts.generate_tests.ChatCompletionsClient")
    def test_generate_completion_success(self, mock_client_cls):
        mock_client = mock_client_cls.return_value
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "test code"
        mock_client.complete.return_value = mock_response

        client = gen.GitHubModelsClient("token")
        result = client.generate_completion("prompt")
        assert result == "test code"
        mock_client.complete.assert_called_once()

    @patch("scripts.generate_tests.ChatCompletionsClient")
    def test_generate_completion_raises_exception(self, mock_client_cls):
        mock_client = mock_client_cls.return_value
        mock_client.complete.side_effect = RuntimeError("fail")

        client = gen.GitHubModelsClient("token")
        with pytest.raises(Exception) as excinfo:
            client.generate_completion("prompt")
        assert "GitHub Models API error" in str(excinfo.value)


class TestSourceCodeAnalyzer:
    def test_read_file_success(tmp_path):
        file = tmp_path / "file.py"
        file.write_text("content")
        analyzer = gen.SourceCodeAnalyzer(str(file))
        assert analyzer.content == "content"

    def test_read_file_failure(tmp_path):
        file = tmp_path / "file.py"
        # Do not create file to cause error
        with pytest.raises(Exception) as excinfo:
            gen.SourceCodeAnalyzer(str(file))
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
        analyzer = gen.SourceCodeAnalyzer(str(file))
        assert analyzer.language == expected_language

    def test_extract_python_elements(sample_python_code, tmp_path):
        file = tmp_path / "file.py"
        file.write_text(sample_python_code)
        analyzer = gen.SourceCodeAnalyzer(str(file))
        elements = analyzer.extract_code_elements()
        assert "MyClass" in elements["classes"]
        assert "public_function" in elements["functions"]
        assert "_private_function" not in elements["functions"]
        assert "test_function" not in elements["functions"]

    def test_extract_python_elements_syntax_error(sample_invalid_python_code, tmp_path):
        file = tmp_path / "file.py"
        file.write_text(sample_invalid_python_code)
        analyzer = gen.SourceCodeAnalyzer(str(file))
        # Should fallback to generic extraction (empty)
        elements = analyzer.extract_code_elements()
        assert isinstance(elements, dict)
        assert "functions" in elements
        assert "classes" in elements

    def test_extract_generic_elements(sample_js_code, tmp_path):
        file = tmp_path / "file.js"
        file.write_text(sample_js_code)
        analyzer = gen.SourceCodeAnalyzer(str(file))
        elements = analyzer.extract_code_elements()
        assert "MyClass" in elements["classes"]
        assert "publicFunction" in elements["functions"]
        assert "testFunction" not in elements["functions"]

    def test_extract_generic_elements_filters_duplicates(tmp_path):
        content = """
        function func1() {}
        function func1() {}
        class Class1 {}
        class Class1 {}
        """
        file = tmp_path / "file.js"
        file.write_text(content)
        analyzer = gen.SourceCodeAnalyzer(str(file))
        elements = analyzer.extract_code_elements()
        assert elements["functions"].count("func1") == 1
        assert elements["classes"].count("Class1") == 1


class TestTestGenerator:
    def test_init_with_token_creates_ai_client(self):
        tg = gen.TestGenerator(github_token="token")
        assert isinstance(tg.ai_client, gen.GitHubModelsClient)

    def test_init_without_token_sets_ai_client_none(self):
        tg = gen.TestGenerator()
        assert tg.ai_client is None

    def test_generate_tests_returns_mock_when_no_ai_client(self, tmp_path):
        tg = gen.TestGenerator()
        result = tg.generate_tests("file.py", "source code")
        assert result.startswith("# Mock test generated")

    @patch.object(gen.GitHubModelsClient, "generate_completion", return_value="generated code")
    def test_generate_tests_with_prompt_uses_custom_prompt(self, mock_gen_completion, tmp_path):
        tg = gen.TestGenerator(github_token="token")
        result = tg.generate_tests("file.py", "source code", prompt="custom prompt")
        assert result == "generated code"
        mock_gen_completion.assert_called_once_with("custom prompt", tg.ai_model)

    @patch.object(gen.GitHubModelsClient, "generate_completion", return_value="```python\ncode\n```")
    def test_generate_tests_without_prompt_creates_prompt_and_cleans_code(self, mock_gen_completion, tmp_path):
        file = tmp_path / "file.py"
        file.write_text("def func(): pass")
        tg = gen.TestGenerator(github_token="token")
        result = tg.generate_tests(str(file), "def func(): pass")
        assert "```" not in result
        mock_gen_completion.assert_called_once()

    def test_generate_tests_for_file_file_not_exist_raises(self):
        tg = gen.TestGenerator()
        with pytest.raises(Exception) as excinfo:
            tg.generate_tests_for_file("nonexistent.py", 50)
        assert "Source file does not exist" in str(excinfo.value)

    def test_generate_tests_for_file_no_elements_raises(self, tmp_path):
        file = tmp_path / "empty.py"
        file.write_text("")
        tg = gen.TestGenerator(github_token="token")
        with pytest.raises(Exception) as excinfo:
            tg.generate_tests_for_file(str(file), 50)
        assert "No testable elements found" in str(excinfo.value)

    @patch.object(gen.GitHubModelsClient, "generate_completion", return_value="```python\ncode\n```")
    def test_generate_tests_for_file_success(self, mock_gen_completion, tmp_path):
        content = """
def func1():
    pass

class Class1:
    pass
"""
        file = tmp_path / "file.py"
        file.write_text(content)
        tg = gen.TestGenerator(github_token="token")
        result = tg.generate_tests_for_file(str(file), 75, "pytest")
        assert "code" in result
        mock_gen_completion.assert_called_once()

    def test_generate_tests_for_file_no_ai_client_raises(self, tmp_path):
        content = """
def func1():
    pass
"""
        file = tmp_path / "file.py"
        file.write_text(content)
        tg = gen.TestGenerator()
        with pytest.raises(Exception) as excinfo:
            tg.generate_tests_for_file(str(file), 75)
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
    def test_detect_test_framework(self, language, expected_framework):
        tg = gen.TestGenerator()
        assert tg._detect_test_framework(language) == expected_framework

    def test_create_test_generation_prompt_contains_expected_parts(self):
        tg = gen.TestGenerator()
        prompt = tg._create_test_generation_prompt(
            "source code",
            "python",
            {"functions": ["func1"], "classes": ["Class1"]},
            80.0,
            "file.py",
            "pytest",
        )
        assert "Generate comprehensive unit tests" in prompt
        assert "func1" in prompt
        assert "Class1" in prompt
        assert "80.0%" in prompt
        assert "pytest" in prompt

    def test_clean_generated_code_removes_markdown(self):
        tg = gen.TestGenerator()
        code = "```python\nprint('hi')\n```"
        cleaned = tg._clean_generated_code(code)
        assert "```" not in cleaned
        assert "print('hi')" in cleaned

    def test_determine_test_file_path_python(tmp_path):
        file = tmp_path / "module.py"
        file.write_text("")
        tg = gen.TestGenerator()
        test_path = tg.determine_test_file_path(str(file))
        p = Path(test_path)
        assert p.name.startswith("test_")
        assert p.suffix == ".py"
        assert p.parent.exists()

    def test_determine_test_file_path_js(tmp_path):
        file = tmp_path / "module.js"
        file.write_text("")
        tg = gen.TestGenerator()
        test_path = tg.determine_test_file_path(str(file))
        p = Path(test_path)
        assert p.name.endswith(".test.js")
        assert p.parent.exists()

    def test_determine_test_file_path_java(tmp_path):
        file = tmp_path / "MyClass.java"
        file.write_text("")
        tg = gen.TestGenerator()
        test_path = tg.determine_test_file_path(str(file))
        p = Path(test_path)
        assert p.name.startswith("TestMyClass")
        assert p.suffix == ".java"
        assert p.parent.exists()

    def test_determine_test_file_path_generic(tmp_path):
        file = tmp_path / "file.xyz"
        file.write_text("")
        tg = gen.TestGenerator()
        test_path = tg.determine_test_file_path(str(file))
        p = Path(test_path)
        assert p.name.startswith("test_")
        assert p.suffix == ".xyz"
        assert p.parent.exists()


class TestMainFunction:
    @patch("scripts.generate_tests.argparse.ArgumentParser.parse_args")
    @patch("scripts.generate_tests.os.getenv")
    @patch("scripts.generate_tests.open", new_callable=mock.mock_open)
    @patch("scripts.generate_tests.Path.mkdir")
    @patch("scripts.generate_tests.TestGenerator")
    def test_main_successful_run(
        self, mock_tg_cls, mock_mkdir, mock_open_func, mock_getenv, mock_parse_args, tmp_path
    ):
        # Setup environment and args
        mock_getenv.return_value = "token"
        mock_parse_args.return_value = mock.Mock(
            coverage_data=str(tmp_path / "coverage.json"),
            max_files=2,
            test_framework="auto",
            ai_model="model",
            output_dir=str(tmp_path / "out"),
            output_format="json",
        )
        coverage_data = {
            "least_covered_files": [
                {"filename": str(tmp_path / "file1.py"), "coverage": 10.0},
                {"filename": str(tmp_path / "file2.py"), "coverage": 20.0},
            ]
        }
        # Write coverage file
        coverage_file = tmp_path / "coverage.json"
        coverage_file.write_text(json.dumps(coverage_data))
        # Write source files
        (tmp_path / "file1.py").write_text("def func1(): pass")
        (tmp_path / "file2.py").write_text("def func2(): pass")

        # Mock TestGenerator instance and methods
        mock_tg = mock_tg_cls.return_value
        mock_tg.generate_tests_for_file.side_effect = [
            "test code 1",
            "test code 2",
        ]
        mock_tg.determine_test_file_path.side_effect = [
            str(tmp_path / "test_file1.py"),
            str(tmp_path / "test_file2.py"),
        ]

        # Mock open for writing test files and summary
        m_open = mock_open_func()
        # Patch open to handle writing test files and summary.json
        with patch("builtins.open", mock_open_func):
            gen.main()

        # Check calls to generate_tests_for_file
        assert mock_tg.generate_tests_for_file.call_count == 2
        # Check calls to determine_test_file_path
        assert mock_tg.determine_test_file_path.call_count == 2
        # Check that test files were written
        handle = mock_open_func()
        handle.write.assert_any_call("test code 1")
        handle.write.assert_any_call("test code 2")
        # Check summary file written
        assert mock_open_func.call_args_list[-1][0][0].endswith("summary.json")

    @patch("scripts.generate_tests.os.getenv", return_value=None)
    @patch("scripts.generate_tests.sys.exit")
    def test_main_exits_without_token(self, mock_exit, mock_getenv):
        with patch("builtins.print") as mock_print:
            gen.main()
        mock_print.assert_any_call("Error: GITHUB_TOKEN environment variable is required")
        mock_exit.assert_called_once_with(1)

    @patch("scripts.generate_tests.os.getenv", return_value="token")
    @patch("scripts.generate_tests.open", new_callable=mock.mock_open)
    @patch("scripts.generate_tests.json.load", side_effect=Exception("fail"))
    @patch("scripts.generate_tests.sys.exit")
    @patch("scripts.generate_tests.argparse.ArgumentParser.parse_args")
    def test_main_exits_on_coverage_load_fail(
        self, mock_parse_args, mock_exit, mock_json_load, mock_open_func, mock_getenv
    ):
        mock_parse_args.return_value = mock.Mock(
            coverage_data="coverage.json",
            max_files=1,
            test_framework="auto",
            ai_model="model",
            output_dir="out",
            output_format="json",
        )
        with patch("builtins.print") as mock_print:
            gen.main()
        mock_print.assert_any_call("Error loading coverage data: fail")
        mock_exit.assert_called_once_with(1)

    @patch("scripts.generate_tests.os.getenv", return_value="token")
    @patch("scripts.generate_tests.open", new_callable=mock.mock_open)
    @patch("scripts.generate_tests.json.load")
    @patch("scripts.generate_tests.Path.mkdir")
    @patch("scripts.generate_tests.argparse.ArgumentParser.parse_args")
    def test_main_no_files_to_process(
        self, mock_parse_args, mock_mkdir, mock_json_load, mock_open_func, mock_getenv, tmp_path
    ):
        mock_parse_args.return_value = mock.Mock(
            coverage_data=str(tmp_path / "coverage.json"),
            max_files=1,
            test_framework="auto",
            ai_model="model",
            output_dir=str(tmp_path / "out"),
            output_format="json",
        )
        mock_json_load.return_value = {"least_covered_files": []}

        with patch("builtins.print") as mock_print:
            gen.main()

        mock_print.assert_any_call("No files to process")
        # Check that summary.json was written
        mock_open_func.assert_called_with(Path(tmp_path / "out") / "summary.json", "w")

    @patch("scripts.generate_tests.os.getenv", return_value="token")
    @patch("scripts.generate_tests.open", new_callable=mock.mock_open)
    @patch("scripts.generate_tests.json.load")
    @patch("scripts.generate_tests.Path.mkdir")
    @patch("scripts.generate_tests.TestGenerator")
    @patch("scripts.generate_tests.argparse.ArgumentParser.parse_args")
    def test_main_handles_generation_error_and_continues(
        self,
        mock_parse_args,
        mock_tg_cls,
        mock_mkdir,
        mock_json_load,
        mock_open_func,
        mock_getenv,
        tmp_path,
    ):
        mock_parse_args.return_value = mock.Mock(
            coverage_data=str(tmp_path / "coverage.json"),
            max_files=2,
            test_framework="auto",
            ai_model="model",
            output_dir=str(tmp_path / "out"),
            output_format="json",
        )
        coverage_data = {
            "least_covered_files": [
                {"filename": str(tmp_path / "file1.py"), "coverage": 10.0},
                {"filename": str(tmp_path / "file2.py"), "coverage": 20.0},
            ]
        }
        coverage_file = tmp_path / "coverage.json"
        coverage_file.write_text(json.dumps(coverage_data))
        (tmp_path / "file1.py").write_text("def func1(): pass")
        (tmp_path / "file2.py").write_text("def func2(): pass")

        mock_tg = mock_tg_cls.return_value
        # First call raises, second succeeds
        def side_effect_generate_tests_for_file(filename, coverage, framework="auto"):
            if "file1.py" in filename:
                raise Exception("fail generation")
            return "test code 2"

        mock_tg.generate_tests_for_file.side_effect = side_effect_generate_tests_for_file
        mock_tg.determine_test_file_path.return_value = str(tmp_path / "test_file2.py")

        with patch("builtins.print") as mock_print:
            gen.main()

        mock_print.assert_any_call("Error generating tests for " + str(tmp_path / "file1.py") + ": fail generation")
        mock_print.assert_any_call("Generated test file: " + str(tmp_path / "test_file2.py"))