import os
import sys
import json
import builtins
import ast
import re
import pytest
from unittest import mock
from pathlib import Path
from types import SimpleNamespace

import scripts.generate_tests as generate_tests


# Helper fixtures and mocks

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
function myFunction() {}
class MyClass {}
function testFunction() {}
"""

@pytest.fixture
def sample_invalid_python_code():
    return "def broken(:\n pass"

@pytest.fixture
def tmp_source_file(tmp_path, sample_python_code):
    file = tmp_path / "sample.py"
    file.write_text(sample_python_code)
    return str(file)

@pytest.fixture
def tmp_js_file(tmp_path, sample_js_code):
    file = tmp_path / "sample.js"
    file.write_text(sample_js_code)
    return str(file)

@pytest.fixture
def mock_github_client():
    client = mock.create_autospec(generate_tests.GitHubModelsClient)
    client.generate_completion.return_value = "mock test code"
    return client

@pytest.fixture
def test_generator_with_mock_client(mock_github_client):
    tg = generate_tests.TestGenerator()
    tg.ai_client = mock_github_client
    return tg


# Tests for GitHubModelsClient

class TestGitHubModelsClient:
    @mock.patch("scripts.generate_tests.ChatCompletionsClient")
    @mock.patch("scripts.generate_tests.AzureKeyCredential")
    def test_init_sets_attributes(self, mock_credential, mock_client):
        token = "fake_token"
        client = generate_tests.GitHubModelsClient(token)
        mock_credential.assert_called_once_with(token)
        mock_client.assert_called_once_with(
            endpoint=client.endpoint,
            credential=mock_credential.return_value,
        )
        assert client.github_token == token
        assert client.client == mock_client.return_value

    def test_generate_completion_success(self):
        client = generate_tests.GitHubModelsClient("token")
        mock_response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="result"))]
        )
        client.client = mock.Mock()
        client.client.complete.return_value = mock_response

        result = client.generate_completion("prompt")
        assert result == "result"
        client.client.complete.assert_called_once()

    def test_generate_completion_raises_on_error(self):
        client = generate_tests.GitHubModelsClient("token")
        client.client = mock.Mock()
        client.client.complete.side_effect = Exception("fail")

        with pytest.raises(Exception) as excinfo:
            client.generate_completion("prompt")
        assert "GitHub Models API error" in str(excinfo.value)


# Tests for SourceCodeAnalyzer

class TestSourceCodeAnalyzer:
    def test_read_file_success(tmp_path, sample_python_code):
        file = tmp_path / "file.py"
        file.write_text(sample_python_code)
        analyzer = generate_tests.SourceCodeAnalyzer(str(file))
        assert analyzer.content == sample_python_code

    def test_read_file_raises_on_missing_file(tmp_path):
        file = tmp_path / "nofile.py"
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
    def test_detect_language_returns_correct_language(tmp_path, filename, expected_language):
        file = tmp_path / filename
        file.write_text("")
        analyzer = generate_tests.SourceCodeAnalyzer(str(file))
        assert analyzer.language == expected_language

    def test_extract_python_elements_returns_classes_and_functions(sample_python_code, tmp_path):
        file = tmp_path / "file.py"
        file.write_text(sample_python_code)
        analyzer = generate_tests.SourceCodeAnalyzer(str(file))
        elements = analyzer.extract_code_elements()
        assert "MyClass" in elements["classes"]
        assert "public_function" in elements["functions"]
        # Private and test functions excluded
        assert "_private_function" not in elements["functions"]
        assert "test_function" not in elements["functions"]

    def test_extract_python_elements_falls_back_on_syntax_error(sample_invalid_python_code, tmp_path):
        file = tmp_path / "file.py"
        file.write_text(sample_invalid_python_code)
        analyzer = generate_tests.SourceCodeAnalyzer(str(file))
        elements = analyzer.extract_code_elements()
        # Should use generic extraction fallback
        assert isinstance(elements, dict)
        assert "functions" in elements
        assert "classes" in elements

    def test_extract_generic_elements_filters_test_names(tmp_js_code, tmp_path):
        file = tmp_path / "file.js"
        file.write_text(tmp_js_code)
        analyzer = generate_tests.SourceCodeAnalyzer(str(file))
        analyzer.language = "javascript"
        elements = analyzer._extract_generic_elements()
        assert "myFunction" in elements["functions"]
        assert "MyClass" in elements["classes"]
        # testFunction should be excluded
        assert "testFunction" not in elements["functions"]


# Tests for TestGenerator

class TestTestGenerator:
    def test_init_with_token_sets_ai_client():
        tg = generate_tests.TestGenerator(github_token="token")
        assert isinstance(tg.ai_client, generate_tests.GitHubModelsClient)

    def test_init_without_token_sets_ai_client_none():
        tg = generate_tests.TestGenerator()
        assert tg.ai_client is None

    def test_generate_tests_returns_mock_when_no_ai_client(tmp_source_file, sample_python_code):
        tg = generate_tests.TestGenerator()
        result = tg.generate_tests(tmp_source_file, sample_python_code)
        assert result.startswith("# Mock test generated")

    def test_generate_tests_uses_custom_prompt(test_generator_with_mock_client, tmp_source_file):
        prompt = "custom prompt"
        result = test_generator_with_mock_client.generate_tests(
            tmp_source_file, "source", prompt=prompt
        )
        test_generator_with_mock_client.ai_client.generate_completion.assert_called_with(
            prompt, test_generator_with_mock_client.ai_model
        )
        assert result == "mock test code"

    def test_generate_tests_uses_default_prompt_and_cleans_code(test_generator_with_mock_client, tmp_source_file):
        source_code = "def foo(): pass"
        # Patch SourceCodeAnalyzer to control elements
        with mock.patch("scripts.generate_tests.SourceCodeAnalyzer") as mock_analyzer_cls:
            mock_analyzer = mock.Mock()
            mock_analyzer.content = source_code
            mock_analyzer.language = "python"
            mock_analyzer.extract_code_elements.return_value = {
                "functions": ["foo"],
                "classes": [],
            }
            mock_analyzer_cls.return_value = mock_analyzer

            test_generator_with_mock_client.ai_client.generate_completion.return_value = "```python\nmock code\n```"

            result = test_generator_with_mock_client.generate_tests(tmp_source_file, source_code)

            assert "```" not in result
            assert result == "mock code"

    def test_generate_tests_for_file_raises_if_file_missing(tmp_path):
        tg = generate_tests.TestGenerator(github_token="token")
        with pytest.raises(Exception) as excinfo:
            tg.generate_tests_for_file(str(tmp_path / "nofile.py"), 50)
        assert "does not exist" in str(excinfo.value)

    def test_generate_tests_for_file_raises_if_no_elements(tmp_path):
        file = tmp_path / "empty.py"
        file.write_text("")
        tg = generate_tests.TestGenerator(github_token="token")
        with mock.patch("scripts.generate_tests.SourceCodeAnalyzer") as mock_analyzer_cls:
            mock_analyzer = mock.Mock()
            mock_analyzer.content = ""
            mock_analyzer.language = "python"
            mock_analyzer.extract_code_elements.return_value = {"functions": [], "classes": []}
            mock_analyzer_cls.return_value = mock_analyzer

            with pytest.raises(Exception) as excinfo:
                tg.generate_tests_for_file(str(file), 50)
            assert "No testable elements" in str(excinfo.value)

    def test_generate_tests_for_file_raises_if_no_ai_client(tmp_source_file):
        tg = generate_tests.TestGenerator()
        with mock.patch("scripts.generate_tests.SourceCodeAnalyzer") as mock_analyzer_cls:
            mock_analyzer = mock.Mock()
            mock_analyzer.content = "code"
            mock_analyzer.language = "python"
            mock_analyzer.extract_code_elements.return_value = {"functions": ["foo"], "classes": []}
            mock_analyzer_cls.return_value = mock_analyzer

            with pytest.raises(Exception) as excinfo:
                tg.generate_tests_for_file(tmp_source_file, 50)
            assert "GitHub token required" in str(excinfo.value)

    def test_generate_tests_for_file_success(tmp_source_file, test_generator_with_mock_client):
        tg = test_generator_with_mock_client
        with mock.patch("scripts.generate_tests.SourceCodeAnalyzer") as mock_analyzer_cls:
            mock_analyzer = mock.Mock()
            mock_analyzer.content = "code"
            mock_analyzer.language = "python"
            mock_analyzer.extract_code_elements.return_value = {"functions": ["foo"], "classes": ["Bar"]}
            mock_analyzer_cls.return_value = mock_analyzer

            tg.ai_client.generate_completion.return_value = "```python\nmock test code\n```"

            result = tg.generate_tests_for_file(tmp_source_file, 75, "pytest")
            assert "mock test code" in result
            assert "```" not in result

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
    def test_detect_test_framework_returns_correct_framework(language, expected_framework):
        tg = generate_tests.TestGenerator()
        assert tg._detect_test_framework(language) == expected_framework

    def test_create_test_generation_prompt_contains_expected_sections():
        tg = generate_tests.TestGenerator()
        source_code = "def foo(): pass"
        elements = {"functions": ["foo"], "classes": ["Bar"]}
        prompt = tg._create_test_generation_prompt(
            source_code, "python", elements, 80.0, "file.py", "pytest"
        )
        assert "Generate comprehensive unit tests" in prompt
        assert "foo" in prompt
        assert "Bar" in prompt
        assert "80.0%" in prompt
        assert "pytest" in prompt
        assert source_code in prompt

    def test_clean_generated_code_removes_markdown_blocks():
        tg = generate_tests.TestGenerator()
        code = "```python\nprint('hello')\n```"
        cleaned = tg._clean_generated_code(code)
        assert "```" not in cleaned
        assert "print('hello')" in cleaned

    def test_determine_test_file_path_creates_dirs_and_returns_path(tmp_path):
        tg = generate_tests.TestGenerator()
        # Python file
        source_file = tmp_path / "module.py"
        source_file.write_text("code")
        test_path = tg.determine_test_file_path(str(source_file))
        assert test_path.endswith("test_module.py")
        assert Path(test_path).parent.exists()

        # JS file
        source_file_js = tmp_path / "file.js"
        source_file_js.write_text("code")
        test_path_js = tg.determine_test_file_path(str(source_file_js))
        assert test_path_js.endswith(".test.js")
        assert Path(test_path_js).parent.exists()

        # Java file
        source_file_java = tmp_path / "MyClass.java"
        source_file_java.write_text("code")
        test_path_java = tg.determine_test_file_path(str(source_file_java))
        assert test_path_java.endswith("TestMyClass.java")
        assert Path(test_path_java).parent.exists()

        # Unknown extension
        source_file_txt = tmp_path / "file.txt"
        source_file_txt.write_text("code")
        test_path_txt = tg.determine_test_file_path(str(source_file_txt))
        assert test_path_txt.endswith("test_file.txt")
        assert Path(test_path_txt).parent.exists()


# Tests for main()

class TestMainFunction:
    @mock.patch("scripts.generate_tests.argparse.ArgumentParser.parse_args")
    @mock.patch("scripts.generate_tests.os.getenv")
    @mock.patch("scripts.generate_tests.open", new_callable=mock.mock_open)
    @mock.patch("scripts.generate_tests.TestGenerator")
    @mock.patch("scripts.generate_tests.Path.mkdir")
    def test_main_exits_if_no_github_token(
        self, mock_mkdir, mock_test_generator_cls, mock_open, mock_getenv, mock_parse_args, capsys
    ):
        mock_getenv.return_value = None
        mock_parse_args.return_value = SimpleNamespace(
            coverage_data="coverage.json",
            max_files=3,
            test_framework="auto",
            ai_model="model",
            output_dir="out",
            output_format="json",
        )
        with pytest.raises(SystemExit):
            generate_tests.main()
        captured = capsys.readouterr()
        assert "GITHUB_TOKEN environment variable is required" in captured.out

    @mock.patch("scripts.generate_tests.argparse.ArgumentParser.parse_args")
    @mock.patch("scripts.generate_tests.os.getenv")
    @mock.patch("scripts.generate_tests.open", new_callable=mock.mock_open)
    @mock.patch("scripts.generate_tests.Path.mkdir")
    def test_main_exits_on_coverage_data_load_error(
        self, mock_mkdir, mock_open, mock_getenv, mock_parse_args, capsys
    ):
        mock_getenv.return_value = "token"
        mock_parse_args.return_value = SimpleNamespace(
            coverage_data="coverage.json",
            max_files=3,
            test_framework="auto",
            ai_model="model",
            output_dir="out",
            output_format="json",
        )
        mock_open.side_effect = Exception("file error")
        with pytest.raises(SystemExit):
            generate_tests.main()
        captured = capsys.readouterr()
        assert "Error loading coverage data" in captured.out

    @mock.patch("scripts.generate_tests.argparse.ArgumentParser.parse_args")
    @mock.patch("scripts.generate_tests.os.getenv")
    @mock.patch("scripts.generate_tests.open", new_callable=mock.mock_open)
    @mock.patch("scripts.generate_tests.TestGenerator")
    @mock.patch("scripts.generate_tests.Path.mkdir")
    def test_main_handles_no_files_to_process(
        self, mock_mkdir, mock_test_generator_cls, mock_open, mock_getenv, mock_parse_args, capsys
    ):
        mock_getenv.return_value = "token"
        mock_parse_args.return_value = SimpleNamespace(
            coverage_data="coverage.json",
            max_files=3,
            test_framework="auto",
            ai_model="model",
            output_dir="out",
            output_format="json",
        )
        coverage_data = {"least_covered_files": []}
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(coverage_data)
        # Patch json.load to return coverage_data
        with mock.patch("json.load", return_value=coverage_data):
            generate_tests.main()
        captured = capsys.readouterr()
        assert "No files to process" in captured.out

    @mock.patch("scripts.generate_tests.argparse.ArgumentParser.parse_args")
    @mock.patch("scripts.generate_tests.os.getenv")
    @mock.patch("scripts.generate_tests.open", new_callable=mock.mock_open)
    @mock.patch("scripts.generate_tests.TestGenerator")
    @mock.patch("scripts.generate_tests.Path.mkdir")
    def test_main_processes_files_successfully(
        self, mock_mkdir, mock_test_generator_cls, mock_open, mock_getenv, mock_parse_args, capsys, tmp_path
    ):
        mock_getenv.return_value = "token"
        mock_parse_args.return_value = SimpleNamespace(
            coverage_data="coverage.json",
            max_files=2,
            test_framework="auto",
            ai_model="model",
            output_dir=str(tmp_path),
            output_format="json",
        )
        files = [
            {"filename": str(tmp_path / "file1.py"), "coverage": 20.0},
            {"filename": str(tmp_path / "file2.py"), "coverage": 30.0},
        ]
        coverage_data = {"least_covered_files": files}
        # Create source files
        for f in files:
            Path(f["filename"]).write_text("def foo(): pass")

        mock_test_generator = mock.Mock()
        mock_test_generator.generate_tests_for_file.return_value = "test code"
        mock_test_generator.determine_test_file_path.side_effect = lambda x: str(tmp_path / f"test_{Path(x).name}")
        mock_test_generator_cls.return_value = mock_test_generator

        with mock.patch("json.load", return_value=coverage_data):
            generate_tests.main()

        captured = capsys.readouterr()
        assert "Processing file 1/2" in captured.out
        assert "Processing file 2/2" in captured.out
        assert "Generated test file" in captured.out
        assert (tmp_path / "test_file1.py").exists()
        assert (tmp_path / "test_file2.py").exists()
        summary_file = tmp_path / "summary.json"
        assert summary_file.exists()
        summary = json.loads(summary_file.read_text())
        assert summary["files_processed"] == 2
        assert summary["tests_generated"] == 2

    @mock.patch("scripts.generate_tests.argparse.ArgumentParser.parse_args")
    @mock.patch("scripts.generate_tests.os.getenv")
    @mock.patch("scripts.generate_tests.open", new_callable=mock.mock_open)
    @mock.patch("scripts.generate_tests.TestGenerator")
    @mock.patch("scripts.generate_tests.Path.mkdir")
    def test_main_continues_on_file_generation_error(
        self, mock_mkdir, mock_test_generator_cls, mock_open, mock_getenv, mock_parse_args, capsys, tmp_path
    ):
        mock_getenv.return_value = "token"
        mock_parse_args.return_value = SimpleNamespace(
            coverage_data="coverage.json",
            max_files=3,
            test_framework="auto",
            ai_model="model",
            output_dir=str(tmp_path),
            output_format="json",
        )
        files = [
            {"filename": str(tmp_path / "file1.py"), "coverage": 20.0},
            {"filename": str(tmp_path / "file2.py"), "coverage": 30.0},
        ]
        coverage_data = {"least_covered_files": files}
        # Create source files
        for f in files:
            Path(f["filename"]).write_text("def foo(): pass")

        mock_test_generator = mock.Mock()
        # First call raises, second returns normally
        def side_effect(file