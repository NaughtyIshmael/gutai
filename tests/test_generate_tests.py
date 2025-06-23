import os
import sys
import json
import ast
import re
import builtins
import pytest
from pathlib import Path
from unittest import mock
from types import SimpleNamespace

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
def sample_generic_code():
    return """
function myFunction() {
    // do something
}

class MyClass {
}

struct MyStruct {
}

interface MyInterface {
}
"""


@pytest.fixture
def tmp_source_file(tmp_path, sample_python_code):
    file = tmp_path / "sample.py"
    file.write_text(sample_python_code)
    return str(file)


@pytest.fixture
def tmp_generic_file(tmp_path, sample_generic_code):
    file = tmp_path / "sample.js"
    file.write_text(sample_generic_code)
    return str(file)


class TestGitHubModelsClient:
    def test_generate_completion_success(self):
        client = generate_tests.GitHubModelsClient("fake_token")
        # Mock the client's complete method
        mock_response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="test code"))]
        )
        client.client.complete = mock.Mock(return_value=mock_response)
        result = client.generate_completion("prompt")
        assert result == "test code"
        client.client.complete.assert_called_once()

    def test_generate_completion_raises_exception(self):
        client = generate_tests.GitHubModelsClient("fake_token")
        client.client.complete = mock.Mock(side_effect=Exception("API error"))
        with pytest.raises(Exception) as excinfo:
            client.generate_completion("prompt")
        assert "GitHub Models API error" in str(excinfo.value)


class TestSourceCodeAnalyzer:
    def test_read_file_success(tmp_path, sample_python_code):
        file = tmp_path / "file.py"
        file.write_text(sample_python_code)
        analyzer = generate_tests.SourceCodeAnalyzer(str(file))
        assert sample_python_code.strip() in analyzer.content

    def test_read_file_error(tmp_path):
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
    def test_detect_language(self, tmp_path, filename, expected_language):
        file = tmp_path / filename
        file.write_text("")
        analyzer = generate_tests.SourceCodeAnalyzer(str(file))
        assert analyzer.language == expected_language

    def test_extract_python_elements(sample_python_code):
        analyzer = generate_tests.SourceCodeAnalyzer.__new__(generate_tests.SourceCodeAnalyzer)
        analyzer.language = "python"
        analyzer.content = sample_python_code
        elements = analyzer.extract_code_elements()
        assert "MyClass" in elements["classes"]
        assert "public_function" in elements["functions"]
        assert "_private_function" not in elements["functions"]
        assert "test_function" not in elements["functions"]

    def test_extract_python_elements_syntax_error():
        analyzer = generate_tests.SourceCodeAnalyzer.__new__(generate_tests.SourceCodeAnalyzer)
        analyzer.language = "python"
        analyzer.content = "def broken(:"
        elements = analyzer.extract_code_elements()
        # Should fallback to generic extraction
        assert "functions" in elements
        assert "classes" in elements

    def test_extract_generic_elements(sample_generic_code):
        analyzer = generate_tests.SourceCodeAnalyzer.__new__(generate_tests.SourceCodeAnalyzer)
        analyzer.language = "javascript"
        analyzer.content = sample_generic_code
        elements = analyzer.extract_code_elements()
        assert "myFunction" in elements["functions"]
        assert "MyClass" in elements["classes"]
        assert "MyStruct" in elements["classes"]
        assert "MyInterface" in elements["classes"]

    def test_extract_generic_elements_filters_tests():
        content = """
        function testFunction() {}
        class TestClass {}
        """
        analyzer = generate_tests.SourceCodeAnalyzer.__new__(generate_tests.SourceCodeAnalyzer)
        analyzer.language = "javascript"
        analyzer.content = content
        elements = analyzer.extract_code_elements()
        assert "testFunction" not in elements["functions"]
        assert "TestClass" not in elements["classes"]


class TestTestGenerator:
    def test_init_with_token_sets_ai_client(self):
        gen = generate_tests.TestGenerator(github_token="token")
        assert gen.ai_client is not None
        assert isinstance(gen.ai_client, generate_tests.GitHubModelsClient)

    def test_init_without_token_sets_ai_client_none(self):
        gen = generate_tests.TestGenerator()
        assert gen.ai_client is None

    def test_generate_tests_with_no_ai_client_returns_mock(tmp_source_file, sample_python_code):
        gen = generate_tests.TestGenerator()
        result = gen.generate_tests(tmp_source_file, sample_python_code)
        assert result.startswith("# Mock test generated")

    def test_generate_tests_with_custom_prompt_calls_ai_client(monkeypatch):
        gen = generate_tests.TestGenerator(github_token="token")
        gen.ai_client.generate_completion = mock.Mock(return_value="generated code")
        result = gen.generate_tests("file.py", "code", prompt="custom prompt")
        gen.ai_client.generate_completion.assert_called_once_with("custom prompt", gen.ai_model)
        assert result == "generated code"

    def test_generate_tests_default_prompt(monkeypatch, tmp_source_file, sample_python_code):
        gen = generate_tests.TestGenerator(github_token="token")
        gen.ai_client.generate_completion = mock.Mock(return_value="```python\ngenerated code\n```")

        # Patch SourceCodeAnalyzer to avoid file reading
        monkeypatch.setattr(generate_tests, "SourceCodeAnalyzer", lambda fp: SimpleNamespace(
            content=sample_python_code,
            language="python",
            extract_code_elements=lambda: {"functions": ["func1"], "classes": ["Class1"]}
        ))

        result = gen.generate_tests(tmp_source_file, sample_python_code)
        assert "generated code" in result
        assert not result.startswith("```")

    def test_generate_tests_for_file_file_not_exist(tmp_path):
        gen = generate_tests.TestGenerator(github_token="token")
        with pytest.raises(Exception) as excinfo:
            gen.generate_tests_for_file(str(tmp_path / "nofile.py"), 50)
        assert "Source file does not exist" in str(excinfo.value)

    def test_generate_tests_for_file_no_elements(tmp_path):
        file = tmp_path / "empty.py"
        file.write_text("")
        gen = generate_tests.TestGenerator(github_token="token")

        # Patch SourceCodeAnalyzer to return no elements
        monkeypatch = mock.Mock()
        monkeypatch.return_value = SimpleNamespace(
            content="",
            language="python",
            extract_code_elements=lambda: {"functions": [], "classes": []},
        )
        with mock.patch("scripts.generate_tests.SourceCodeAnalyzer", monkeypatch):
            with pytest.raises(Exception) as excinfo:
                gen.generate_tests_for_file(str(file), 50)
            assert "No testable elements found" in str(excinfo.value)

    def test_generate_tests_for_file_auto_framework(monkeypatch, tmp_source_file, sample_python_code):
        gen = generate_tests.TestGenerator(github_token="token")
        # Patch SourceCodeAnalyzer
        monkeypatcher = mock.Mock()
        monkeypatcher.return_value = SimpleNamespace(
            content=sample_python_code,
            language="python",
            extract_code_elements=lambda: {"functions": ["func1"], "classes": ["Class1"]},
        )
        with mock.patch("scripts.generate_tests.SourceCodeAnalyzer", monkeypatcher):
            # Patch ai_client.generate_completion
            gen.ai_client.generate_completion = mock.Mock(return_value="```python\ntest code\n```")
            result = gen.generate_tests_for_file(tmp_source_file, 75, test_framework="auto")
            assert "test code" in result
            gen.ai_client.generate_completion.assert_called_once()
            # Test framework detected as pytest
            assert gen._detect_test_framework("python") == "pytest"

    def test_generate_tests_for_file_no_ai_client_raises(monkeypatch, tmp_source_file, sample_python_code):
        gen = generate_tests.TestGenerator()
        monkeypatcher = mock.Mock()
        monkeypatcher.return_value = SimpleNamespace(
            content=sample_python_code,
            language="python",
            extract_code_elements=lambda: {"functions": ["func1"], "classes": ["Class1"]},
        )
        with mock.patch("scripts.generate_tests.SourceCodeAnalyzer", monkeypatcher):
            with pytest.raises(Exception) as excinfo:
                gen.generate_tests_for_file(tmp_source_file, 50)
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
        gen = generate_tests.TestGenerator()
        assert gen._detect_test_framework(language) == expected_framework

    def test_create_test_generation_prompt_includes_elements(tmp_source_file):
        gen = generate_tests.TestGenerator()
        source_code = "def foo(): pass"
        elements = {"functions": ["foo"], "classes": ["Bar"]}
        prompt = gen._create_test_generation_prompt(
            source_code, "python", elements, 80.0, tmp_source_file, "pytest"
        )
        assert "foo" in prompt
        assert "Bar" in prompt
        assert "80.0%" in prompt
        assert "pytest" in prompt
        assert tmp_source_file in prompt

    def test_clean_generated_code_removes_markdown():
        gen = generate_tests.TestGenerator()
        code = "```python\nprint('hello')\n```"
        cleaned = gen._clean_generated_code(code)
        assert cleaned == "print('hello')"

        code2 = "```\ncode\n```"
        cleaned2 = gen._clean_generated_code(code2)
        assert cleaned2 == "code"

        code3 = "no markdown"
        cleaned3 = gen._clean_generated_code(code3)
        assert cleaned3 == "no markdown"

    def test_determine_test_file_path_creates_dirs(tmp_path):
        gen = generate_tests.TestGenerator()
        # Python file
        source_file = tmp_path / "module.py"
        source_file.write_text("print('hi')")
        test_path = gen.determine_test_file_path(str(source_file))
        assert test_path.endswith("tests/test_module.py") or test_path.endswith(f"test_module.py")
        assert Path(test_path).parent.exists()

        # JS file
        source_file_js = tmp_path / "app.js"
        source_file_js.write_text("function foo(){}")
        test_path_js = gen.determine_test_file_path(str(source_file_js))
        assert test_path_js.endswith(".test.js")
        assert Path(test_path_js).parent.exists()

        # Java file
        source_file_java = tmp_path / "MyClass.java"
        source_file_java.write_text("public class MyClass {}")
        test_path_java = gen.determine_test_file_path(str(source_file_java))
        assert test_path_java.endswith("TestMyClass.java")
        assert Path(test_path_java).parent.exists()

        # Unknown extension
        source_file_txt = tmp_path / "file.txt"
        source_file_txt.write_text("some content")
        test_path_txt = gen.determine_test_file_path(str(source_file_txt))
        assert test_path_txt.endswith("tests/test_file.txt")
        assert Path(test_path_txt).parent.exists()


class TestMainFunction:
    @mock.patch("scripts.generate_tests.os.getenv")
    @mock.patch("scripts.generate_tests.open", new_callable=mock.mock_open, read_data='{"least_covered_files": []}')
    @mock.patch("scripts.generate_tests.Path.mkdir")
    @mock.patch("scripts.generate_tests.json.dump")
    def test_main_no_github_token(self, mock_json_dump, mock_mkdir, mock_open, mock_getenv):
        mock_getenv.return_value = None
        testargs = ["prog", "--coverage-data", "coverage.json"]
        with mock.patch.object(sys, "argv", testargs):
            with pytest.raises(SystemExit) as e:
                generate_tests.main()
            assert e.value.code == 1

    @mock.patch("scripts.generate_tests.os.getenv")
    @mock.patch("scripts.generate_tests.open", new_callable=mock.mock_open, read_data='{"least_covered_files": []}')
    @mock.patch("scripts.generate_tests.Path.mkdir")
    @mock.patch("scripts.generate_tests.json.dump")
    def test_main_no_files_to_process(self, mock_json_dump, mock_mkdir, mock_open, mock_getenv):
        mock_getenv.return_value = "token"
        testargs = ["prog", "--coverage-data", "coverage.json"]
        with mock.patch.object(sys, "argv", testargs):
            generate_tests.main()
        mock_json_dump.assert_called()
        mock_mkdir.assert_called()

    @mock.patch("scripts.generate_tests.os.getenv")
    @mock.patch("scripts.generate_tests.open", new_callable=mock.mock_open)
    @mock.patch("scripts.generate_tests.Path.mkdir")
    @mock.patch("scripts.generate_tests.json.dump")
    @mock.patch("scripts.generate_tests.TestGenerator.generate_tests_for_file")
    @mock.patch("scripts.generate_tests.TestGenerator.determine_test_file_path")
    def test_main_process_files_success(
        self,
        mock_determine_path,
        mock_generate_tests_for_file,
        mock_json_dump,
        mock_mkdir,
        mock_open,
        mock_getenv,
    ):
        mock_getenv.return_value = "token"
        coverage_data = {
            "least_covered_files": [
                {"filename": "file1.py", "coverage": 20.0},
                {"filename": "file2.py", "coverage": 30.0},
            ]
        }
        # Setup open to read coverage data JSON
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(coverage_data)
        # Setup generate_tests_for_file to return test code
        mock_generate_tests_for_file.side_effect = ["test code 1", "test code 2"]
        # Setup determine_test_file_path to return test file paths
        mock_determine_path.side_effect = ["tests/test_file1.py", "tests/test_file2.py"]

        testargs = [
            "prog",
            "--coverage-data",
            "coverage.json",
            "--max-files",
            "2",
            "--test-framework",
            "pytest",
            "--output-dir",
            "outdir",
            "--output-format",
            "json",
        ]
        with mock.patch.object(sys, "argv", testargs):
            with mock.patch("builtins.open", mock.mock_open()) as m_open:
                generate_tests.main()

        assert mock_generate_tests_for_file.call_count == 2
        assert mock_determine_path.call_count == 2
        assert mock_json_dump.called
        assert mock_mkdir.called

    @mock.patch("scripts.generate_tests.os.getenv")
    @mock.patch("scripts.generate_tests.open", new_callable=mock.mock_open)
    def test_main_coverage_data_load_error(self, mock_open, mock_getenv):
        mock_getenv.return_value = "token"
        mock_open.side_effect = Exception("file error")
        testargs = ["prog", "--coverage-data", "coverage.json"]
        with mock.patch.object(sys, "argv", testargs):
            with pytest.raises(SystemExit) as e:
                generate_tests.main()
            assert e.value.code == 1

    @mock.patch("scripts.generate_tests.os.getenv")
    @mock.patch("scripts.generate_tests.open", new_callable=mock.mock_open)
    @mock.patch("scripts.generate_tests.Path.mkdir")
    @mock.patch("scripts.generate_tests.json.dump")
    @mock.patch("scripts.generate_tests.TestGenerator.generate_tests_for_file")
    @mock.patch("scripts.generate_tests.TestGenerator.determine_test_file_path")
    def test_main_handles_generate_tests_exception(
        self,
        mock_determine_path,
        mock_generate_tests_for_file,
        mock_json_dump,
        mock_mkdir,
        mock_open,
        mock_getenv,
    ):
        mock_getenv.return_value = "token"
        coverage_data = {
            "least_covered_files": [
                {"filename": "file1.py", "coverage": 20.0},
                {"filename": "file2.py", "coverage": 30.0},
            ]
        }
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(coverage_data)
        # Raise exception on first call, succeed on second
        mock_generate_tests_for_file.side_effect = [Exception("fail"), "test code 2"]
        mock_determine_path.side_effect = ["tests/test_file1.py", "tests/test_file2.py"]

        testargs = ["prog", "--coverage-data", "coverage.json", "--max-files", "2"]
        with mock.patch.object(sys, "argv", testargs):
            with mock.patch("builtins.open", mock.mock_open()) as m_open:
                generate_tests.main()

        assert mock_generate_tests_for_file.call_count == 2
        assert mock_determine_path.call_count == 1  # Only called for second file
        assert mock_json_dump.called