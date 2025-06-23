import os
import sys
import json
import ast
import re
import builtins
import tempfile
import shutil
from pathlib import Path
from unittest import mock
import pytest

import scripts.generate_tests as gen


class DummyResponseChoice:
    def __init__(self, content):
        self.message = mock.Mock()
        self.message.content = content


class DummyResponse:
    def __init__(self, content):
        self.choices = [DummyResponseChoice(content)]


@pytest.fixture
def temp_source_file():
    temp_dir = tempfile.mkdtemp()
    file_path = Path(temp_dir) / "example.py"
    file_path.write_text(
        "class MyClass:\n"
        "    def method(self):\n"
        "        pass\n"
        "def func():\n"
        "    pass\n"
        "def _private():\n"
        "    pass\n"
        "def test_func():\n"
        "    pass\n"
    )
    yield str(file_path)
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_generic_source_file():
    temp_dir = tempfile.mkdtemp()
    file_path = Path(temp_dir) / "example.js"
    file_path.write_text(
        "function myFunction() {}\n"
        "class MyClass {}\n"
        "function testFunction() {}\n"
        "class TestClass {}\n"
    )
    yield str(file_path)
    shutil.rmtree(temp_dir)


@pytest.fixture
def dummy_github_client():
    client = gen.GitHubModelsClient.__new__(gen.GitHubModelsClient)
    client.github_token = "dummy"
    client.endpoint = "https://models.github.ai/inference"
    client.client = mock.Mock()
    return client


@pytest.mark.parametrize("model", [None, "custom-model"])
def test_github_models_client_generate_completion_success(monkeypatch, dummy_github_client, model):
    expected_content = "test code"
    dummy_github_client.client.complete.return_value = DummyResponse(expected_content)

    prompt = "prompt text"
    model_name = model or "openai/gpt-4.1-mini"
    result = dummy_github_client.generate_completion(prompt, model=model_name)
    dummy_github_client.client.complete.assert_called_once()
    assert expected_content == result


def test_github_models_client_generate_completion_raises(monkeypatch, dummy_github_client):
    dummy_github_client.client.complete.side_effect = Exception("API failure")
    with pytest.raises(Exception, match="GitHub Models API error: API failure"):
        dummy_github_client.generate_completion("prompt")


def test_source_code_analyzer_read_file_and_detect_language(temp_source_file):
    analyzer = gen.SourceCodeAnalyzer(temp_source_file)
    assert "class MyClass" in analyzer.content
    assert analyzer.language == "python"


def test_source_code_analyzer_read_file_error(tmp_path):
    file_path = tmp_path / "nofile.py"
    with pytest.raises(Exception, match="Error reading file"):
        gen.SourceCodeAnalyzer(str(file_path))


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
        ("file.c", "c"),
        ("file.cs", "csharp"),
        ("file.go", "go"),
        ("file.rs", "rust"),
        ("file.rb", "ruby"),
        ("file.php", "php"),
        ("file.unknown", "unknown"),
    ],
)
def test_source_code_analyzer_detect_language(tmp_path, filename, expected_language):
    file_path = tmp_path / filename
    file_path.write_text("")
    analyzer = gen.SourceCodeAnalyzer(str(file_path))
    assert analyzer.language == expected_language


def test_extract_python_elements_filters_private_and_test(temp_source_file):
    analyzer = gen.SourceCodeAnalyzer(temp_source_file)
    elements = analyzer.extract_code_elements()
    assert "MyClass" in elements["classes"]
    assert "func" in elements["functions"]
    assert "_private" not in elements["functions"]
    assert "test_func" not in elements["functions"]


def test_extract_python_elements_syntax_error_triggers_generic(tmp_path):
    file_path = tmp_path / "bad.py"
    file_path.write_text("def foo(:\n pass")  # invalid syntax
    analyzer = gen.SourceCodeAnalyzer(str(file_path))
    elements = analyzer.extract_code_elements()
    # Should fallback to generic extraction (empty because no valid patterns)
    assert isinstance(elements, dict)
    assert "functions" in elements and "classes" in elements


def test_extract_generic_elements_filters_tests(temp_generic_source_file):
    analyzer = gen.SourceCodeAnalyzer(temp_generic_source_file)
    elements = analyzer._extract_generic_elements()
    assert "myFunction" in elements["functions"]
    assert "MyClass" in elements["classes"]
    assert all("test" not in f.lower() for f in elements["functions"])
    assert all("test" not in c.lower() for c in elements["classes"])


@pytest.fixture
def test_generator_with_mock_client(monkeypatch):
    tg = gen.TestGenerator(github_token="token")
    mock_client = mock.Mock()
    mock_client.generate_completion.return_value = "generated test code"
    tg.ai_client = mock_client
    return tg


def test_generate_tests_returns_mock_when_no_ai_client(temp_source_file):
    tg = gen.TestGenerator()
    result = tg.generate_tests(temp_source_file, "source code")
    assert result.startswith("# Mock test generated")


def test_generate_tests_with_custom_prompt_calls_ai_client(test_generator_with_mock_client):
    prompt = "custom prompt"
    result = test_generator_with_mock_client.generate_tests(
        "file.py", "source", prompt=prompt
    )
    test_generator_with_mock_client.ai_client.generate_completion.assert_called_with(
        prompt, test_generator_with_mock_client.ai_model
    )
    assert result == "generated test code"


def test_generate_tests_default_prompt_calls_ai_client(monkeypatch, test_generator_with_mock_client, temp_source_file):
    source_code = Path(temp_source_file).read_text()
    # Patch SourceCodeAnalyzer to avoid reading file again
    monkeypatch.setattr(gen, "SourceCodeAnalyzer", lambda fp: gen.SourceCodeAnalyzer(temp_source_file))
    result = test_generator_with_mock_client.generate_tests(temp_source_file, source_code)
    assert result == "generated test code"


def test_generate_tests_for_file_success(monkeypatch, tmp_path):
    # Prepare source file
    source_file = tmp_path / "file.py"
    source_file.write_text("def func(): pass\nclass C: pass\n")
    # Patch GitHubModelsClient to avoid real API calls
    tg = gen.TestGenerator(github_token="token")
    mock_client = mock.Mock()
    mock_client.generate_completion.return_value = "```python\ndef test_func(): pass\n```"
    tg.ai_client = mock_client

    result = tg.generate_tests_for_file(str(source_file), 75.0, "pytest")
    assert "def test_func()" in result
    # Markdown code block removed
    assert not result.startswith("```")


def test_generate_tests_for_file_no_file_raises(tmp_path):
    tg = gen.TestGenerator(github_token="token")
    with pytest.raises(Exception, match="Source file does not exist"):
        tg.generate_tests_for_file(str(tmp_path / "nofile.py"), 50)


def test_generate_tests_for_file_no_elements_raises(tmp_path):
    source_file = tmp_path / "empty.py"
    source_file.write_text("# no functions or classes")
    tg = gen.TestGenerator(github_token="token")
    with pytest.raises(Exception, match="No testable elements found"):
        tg.generate_tests_for_file(str(source_file), 50)


def test_generate_tests_for_file_no_ai_client_raises(tmp_path):
    source_file = tmp_path / "file.py"
    source_file.write_text("def func(): pass\n")
    tg = gen.TestGenerator()
    with pytest.raises(Exception, match="GitHub token required"):
        tg.generate_tests_for_file(str(source_file), 50)


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
    tg = gen.TestGenerator()
    assert tg._detect_test_framework(language) == expected_framework


def test_create_test_generation_prompt_includes_all_parts():
    tg = gen.TestGenerator()
    source_code = "def foo(): pass"
    elements = {"functions": ["foo"], "classes": ["Bar"]}
    prompt = tg._create_test_generation_prompt(
        source_code, "python", elements, 80.0, "file.py", "pytest"
    )
    assert "def foo()" not in prompt  # source code included, but not function def alone
    assert "foo" in prompt
    assert "Bar" in prompt
    assert "80.0%" in prompt
    assert "pytest" in prompt
    assert "Generate comprehensive unit tests" in prompt


@pytest.mark.parametrize(
    "input_code,expected",
    [
        ("```python\ndef test(): pass\n```", "def test(): pass"),
        ("```\ncode\n```", "code"),
        ("code without markdown", "code without markdown"),
    ],
)
def test_clean_generated_code_removes_markdown(input_code, expected):
    tg = gen.TestGenerator()
    cleaned = tg._clean_generated_code(input_code)
    assert cleaned == expected


def test_determine_test_file_path_creates_dirs_and_returns_path(tmp_path):
    tg = gen.TestGenerator()
    # Python file
    source_file = tmp_path / "module.py"
    source_file.write_text("")
    test_path = tg.determine_test_file_path(str(source_file))
    assert test_path.endswith("test_module.py")
    assert Path(test_path).parent.exists()

    # JS file
    source_file_js = tmp_path / "app.js"
    source_file_js.write_text("")
    test_path_js = tg.determine_test_file_path(str(source_file_js))
    assert test_path_js.endswith(".test.js")
    assert Path(test_path_js).parent.exists()

    # Java file
    source_file_java = tmp_path / "MyClass.java"
    source_file_java.write_text("")
    test_path_java = tg.determine_test_file_path(str(source_file_java))
    assert test_path_java.endswith("TestMyClass.java")
    assert Path(test_path_java).parent.exists()

    # Unknown extension
    source_file_txt = tmp_path / "file.txt"
    source_file_txt.write_text("")
    test_path_txt = tg.determine_test_file_path(str(source_file_txt))
    assert test_path_txt.endswith("test_file.txt")
    assert Path(test_path_txt).parent.exists()


@mock.patch.dict(os.environ, {"GITHUB_TOKEN": "token"})
@mock.patch("builtins.open", new_callable=mock.mock_open, read_data=json.dumps({"least_covered_files": []}))
@mock.patch("pathlib.Path.mkdir")
def test_main_no_files_to_process(mock_mkdir, mock_open, capsys):
    test_args = [
        "generate_tests.py",
        "--coverage-data",
        "coverage.json",
    ]
    with mock.patch.object(sys, "argv", test_args):
        gen.main()
    captured = capsys.readouterr()
    assert "No files to process" in captured.out
    mock_mkdir.assert_called()


@mock.patch.dict(os.environ, {}, clear=True)
def test_main_missing_github_token_exits(capsys):
    test_args = [
        "generate_tests.py",
        "--coverage-data",
        "coverage.json",
    ]
    with mock.patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit):
            gen.main()
    captured = capsys.readouterr()
    assert "GITHUB_TOKEN environment variable is required" in captured.out


@mock.patch.dict(os.environ, {"GITHUB_TOKEN": "token"})
@mock.patch("builtins.open", new_callable=mock.mock_open, read_data="not json")
def test_main_invalid_coverage_data_exits(mock_open, capsys):
    test_args = [
        "generate_tests.py",
        "--coverage-data",
        "coverage.json",
    ]
    with mock.patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit):
            gen.main()
    captured = capsys.readouterr()
    assert "Error loading coverage data" in captured.out


@mock.patch.dict(os.environ, {"GITHUB_TOKEN": "token"})
@mock.patch("builtins.open", new_callable=mock.mock_open)
@mock.patch("pathlib.Path.mkdir")
@mock.patch("scripts.generate_tests.TestGenerator.generate_tests_for_file")
@mock.patch("scripts.generate_tests.TestGenerator.determine_test_file_path")
def test_main_process_files_success(
    mock_determine_path,
    mock_generate_tests,
    mock_mkdir,
    mock_open,
    capsys,
):
    coverage_data = {
        "least_covered_files": [
            {"filename": "file1.py", "coverage": 20.0},
            {"filename": "file2.py", "coverage": 30.0},
        ]
    }
    mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(coverage_data)
    mock_generate_tests.side_effect = ["test code 1", "test code 2"]
    mock_determine_path.side_effect = ["tests/test_file1.py", "tests/test_file2.py"]

    test_args = [
        "generate_tests.py",
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
    with mock.patch.object(sys, "argv", test_args):
        with mock.patch("builtins.open", mock.mock_open()) as m_open:
            gen.main()

    captured = capsys.readouterr()
    assert "Processing file 1/2: file1.py" in captured.out
    assert "Processing file 2/2: file2.py" in captured.out
    assert "Generated test file: tests/test_file1.py" in captured.out
    assert "Generated test file: tests/test_file2.py" in captured.out
    assert "Generation complete!" in captured.out


@mock.patch.dict(os.environ, {"GITHUB_TOKEN": "token"})
@mock.patch("builtins.open", new_callable=mock.mock_open)
@mock.patch("pathlib.Path.mkdir")
@mock.patch("scripts.generate_tests.TestGenerator.generate_tests_for_file")
@mock.patch("scripts.generate_tests.TestGenerator.determine_test_file_path")
def test_main_process_files_with_error_continues(
    mock_determine_path,
    mock_generate_tests,
    mock_mkdir,
    mock_open,
    capsys,
):
    coverage_data = {
        "least_covered_files": [
            {"filename": "file1.py", "coverage": 20.0},
            {"filename": "file2.py", "coverage": 30.0},
        ]
    }
    mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(coverage_data)
    # First call raises, second returns test code
    mock_generate_tests.side_effect = [Exception("fail"), "test code 2"]
    mock_determine_path.side_effect = ["tests/test_file1.py", "tests/test_file2.py"]

    test_args = [
        "generate_tests.py",
        "--coverage-data",
        "coverage.json",
        "--max-files",
        "2",
    ]
    with mock.patch.object(sys, "argv", test_args):
        with mock.patch("builtins.open", mock.mock_open()) as m_open:
            gen.main()

    captured = capsys.readouterr()
    assert "Error generating tests for file1.py: fail" in captured.out
    assert "Generated test file: tests/test_file2.py" in captured.out


def test_test_generator_generate_mock_tests_returns_expected():
    tg = gen.TestGenerator()
    result = tg._generate_mock_tests("file.py", "source")
    assert result.startswith("# Mock test generated")


def test_source_code_analyzer_extract_code_elements_unknown_language(tmp_path):
    file_path = tmp_path / "file.unknown"
    file_path.write_text("some random content")
    analyzer = gen.SourceCodeAnalyzer(str(file_path))
    elements = analyzer.extract_code_elements()
    assert isinstance(elements, dict)
    assert "functions" in elements and "classes" in elements


def test_source_code_analyzer_extract_generic_elements_filters_duplicates(tmp_path):
    file_path = tmp_path / "file.js"
    file_path.write_text(
        "function foo() {}\nfunction foo() {}\nclass Bar {}\nclass Bar {}\n"
    )
    analyzer = gen.SourceCodeAnalyzer(str(file_path))
    elements = analyzer._extract_generic_elements()
    assert elements["functions"].count("foo") == 1
    assert elements["classes"].count("Bar") == 1


def test_source_code_analyzer_extract_generic_elements_filters_test_names(tmp_path):
    file_path = tmp_path / "file.js"
    file_path.write_text(
        "function testFunc() {}\nclass TestClass {}\nfunction specFunc() {}\nclass SpecClass {}\n"
    )
    analyzer = gen.SourceCodeAnalyzer(str(file_path))
    elements = analyzer._extract_generic_elements()
    assert "testFunc" not in elements["functions"]
    assert "specFunc" not in elements["functions"]
    assert "TestClass" not in elements["classes"]
    assert "SpecClass" not in elements["classes"]