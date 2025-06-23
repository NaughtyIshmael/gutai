import os
import sys
import json
import ast
import re
import builtins
import pytest
from unittest import mock
from pathlib import Path
from types import SimpleNamespace

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
    return "def broken(:\n pass"


@pytest.fixture
def temp_source_file(tmp_path, sample_python_code):
    file_path = tmp_path / "sample.py"
    file_path.write_text(sample_python_code)
    return str(file_path)


@pytest.fixture
def temp_js_file(tmp_path, sample_js_code):
    file_path = tmp_path / "sample.js"
    file_path.write_text(sample_js_code)
    return str(file_path)


@pytest.fixture
def temp_invalid_py_file(tmp_path, sample_invalid_python_code):
    file_path = tmp_path / "broken.py"
    file_path.write_text(sample_invalid_python_code)
    return str(file_path)


@pytest.fixture
def github_token():
    return "fake_token"


class DummyResponse:
    def __init__(self, content):
        self.choices = [SimpleNamespace(message=SimpleNamespace(content=content))]


class DummyClient:
    def __init__(self, response_content=None, raise_exc=False):
        self.response_content = response_content or "test code"
        self.raise_exc = raise_exc

    def complete(self, **kwargs):
        if self.raise_exc:
            raise RuntimeError("API failure")
        return DummyResponse(self.response_content)


def test_github_models_client_generate_completion_success(monkeypatch, github_token):
    dummy_client = DummyClient(response_content="generated test code")
    monkeypatch.setattr(gen.ChatCompletionsClient, "__init__", lambda self, **kwargs: None)
    monkeypatch.setattr(gen.ChatCompletionsClient, "complete", dummy_client.complete)

    client = gen.GitHubModelsClient(github_token)
    client.client = dummy_client  # override client with dummy

    result = client.generate_completion("prompt text")
    assert result == "generated test code"


def test_github_models_client_generate_completion_exception(monkeypatch, github_token):
    dummy_client = DummyClient(raise_exc=True)
    monkeypatch.setattr(gen.ChatCompletionsClient, "__init__", lambda self, **kwargs: None)
    monkeypatch.setattr(gen.ChatCompletionsClient, "complete", dummy_client.complete)

    client = gen.GitHubModelsClient(github_token)
    client.client = dummy_client  # override client with dummy

    with pytest.raises(Exception) as excinfo:
        client.generate_completion("prompt text")
    assert "GitHub Models API error" in str(excinfo.value)


def test_source_code_analyzer_read_file_and_detect_language(tmp_path, sample_python_code):
    file_path = tmp_path / "test.py"
    file_path.write_text(sample_python_code)

    analyzer = gen.SourceCodeAnalyzer(str(file_path))
    assert analyzer.content == sample_python_code
    assert analyzer.language == "python"


def test_source_code_analyzer_read_file_error(tmp_path):
    file_path = tmp_path / "nonexistent.py"
    with pytest.raises(Exception) as excinfo:
        gen.SourceCodeAnalyzer(str(file_path))
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
    file_path.write_text("dummy content")
    analyzer = gen.SourceCodeAnalyzer(str(file_path))
    assert analyzer.language == expected_language


def test_extract_python_elements(sample_python_code):
    analyzer = gen.SourceCodeAnalyzer.__new__(gen.SourceCodeAnalyzer)
    analyzer.content = sample_python_code
    analyzer.language = "python"
    elements = analyzer.extract_code_elements()
    assert "MyClass" in elements["classes"]
    assert "public_function" in elements["functions"]
    assert "_private_function" not in elements["functions"]
    assert "test_function" not in elements["functions"]


def test_extract_python_elements_syntax_error(sample_invalid_python_code):
    analyzer = gen.SourceCodeAnalyzer.__new__(gen.SourceCodeAnalyzer)
    analyzer.content = sample_invalid_python_code
    analyzer.language = "python"
    elements = analyzer.extract_code_elements()
    # Should fallback to generic extraction (likely empty)
    assert isinstance(elements, dict)
    assert "functions" in elements and "classes" in elements


def test_extract_generic_elements(sample_js_code):
    analyzer = gen.SourceCodeAnalyzer.__new__(gen.SourceCodeAnalyzer)
    analyzer.content = sample_js_code
    analyzer.language = "javascript"
    elements = analyzer.extract_code_elements()
    assert "publicFunction" in elements["functions"]
    assert "MyClass" in elements["classes"]
    # testFunction should be excluded
    assert "testFunction" not in elements["functions"]


def test_test_generator_generate_mock_tests_returns_mock():
    tg = gen.TestGenerator()
    result = tg._generate_mock_tests("file.py", "source code")
    assert result.startswith("# Mock test generated")


def test_test_generator_generate_tests_with_no_ai_client_returns_mock(tmp_path):
    tg = gen.TestGenerator()
    source_code = "def foo(): pass"
    result = tg.generate_tests("file.py", source_code)
    assert "# Mock test generated" in result


def test_test_generator_generate_tests_with_prompt(monkeypatch, github_token):
    tg = gen.TestGenerator(github_token)
    dummy_client = DummyClient(response_content="generated test code")
    tg.ai_client = dummy_client

    prompt = "custom prompt"
    result = tg.generate_tests("file.py", "source code", prompt=prompt)
    assert result == "generated test code"


def test_test_generator_generate_tests_default_prompt(monkeypatch, github_token, sample_python_code, tmp_path):
    file_path = tmp_path / "sample.py"
    file_path.write_text(sample_python_code)

    tg = gen.TestGenerator(github_token)
    dummy_client = DummyClient(response_content="generated test code")
    tg.ai_client = dummy_client

    # Patch SourceCodeAnalyzer to use our file_path and content
    with mock.patch.object(gen.SourceCodeAnalyzer, "__init__", lambda self, fp: None):
        with mock.patch.object(gen.SourceCodeAnalyzer, "extract_code_elements", return_value={"functions": ["public_function"], "classes": ["MyClass"]}):
            with mock.patch.object(gen.SourceCodeAnalyzer, "content", sample_python_code):
                analyzer = gen.SourceCodeAnalyzer.__new__(gen.SourceCodeAnalyzer)
                analyzer.file_path = Path(file_path)
                analyzer.content = sample_python_code
                analyzer.language = "python"
                tg.ai_client = dummy_client
                result = tg.generate_tests(str(file_path), sample_python_code)
                assert result == "generated test code"


def test_test_generator_generate_tests_for_file_success(monkeypatch, github_token, sample_python_code, tmp_path):
    file_path = tmp_path / "sample.py"
    file_path.write_text(sample_python_code)

    tg = gen.TestGenerator(github_token)
    dummy_client = DummyClient(response_content="generated test code")
    tg.ai_client = dummy_client

    # Patch SourceCodeAnalyzer.extract_code_elements to return functions and classes
    with mock.patch.object(gen.SourceCodeAnalyzer, "extract_code_elements", return_value={"functions": ["public_function"], "classes": ["MyClass"]}):
        test_code = tg.generate_tests_for_file(str(file_path), 75.0, "pytest")
        assert test_code == "generated test code"


def test_test_generator_generate_tests_for_file_no_file(tmp_path, github_token):
    tg = gen.TestGenerator(github_token)
    with pytest.raises(Exception) as excinfo:
        tg.generate_tests_for_file("nonexistent.py", 50.0)
    assert "Source file does not exist" in str(excinfo.value)


def test_test_generator_generate_tests_for_file_no_elements(tmp_path, github_token):
    file_path = tmp_path / "empty.py"
    file_path.write_text("")

    tg = gen.TestGenerator(github_token)
    with mock.patch.object(gen.SourceCodeAnalyzer, "extract_code_elements", return_value={"functions": [], "classes": []}):
        with pytest.raises(Exception) as excinfo:
            tg.generate_tests_for_file(str(file_path), 50.0)
        assert "No testable elements found" in str(excinfo.value)


def test_test_generator_generate_tests_for_file_no_ai_client(tmp_path, sample_python_code):
    file_path = tmp_path / "sample.py"
    file_path.write_text(sample_python_code)

    tg = gen.TestGenerator()  # no token => no ai_client
    with mock.patch.object(gen.SourceCodeAnalyzer, "extract_code_elements", return_value={"functions": ["func"], "classes": ["Cls"]}):
        with pytest.raises(Exception) as excinfo:
            tg.generate_tests_for_file(str(file_path), 50.0)
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
def test_test_generator_detect_test_framework(language, expected_framework):
    tg = gen.TestGenerator()
    assert tg._detect_test_framework(language) == expected_framework


def test_test_generator_create_test_generation_prompt(sample_python_code):
    tg = gen.TestGenerator()
    elements = {"functions": ["foo", "bar"], "classes": ["MyClass"]}
    prompt = tg._create_test_generation_prompt(
        sample_python_code,
        "python",
        elements,
        80.0,
        "file.py",
        "pytest",
    )
    assert "Generate comprehensive unit tests" in prompt
    assert "foo, bar" in prompt
    assert "MyClass" in prompt
    assert "80.0%" in prompt
    assert "pytest" in prompt


@pytest.mark.parametrize(
    "code_with_md,expected",
    [
        ("```python\nprint('hi')\n```", "print('hi')"),
        ("```\ncode\n```", "code"),
        ("code without md", "code without md"),
    ],
)
def test_test_generator_clean_generated_code(code_with_md, expected):
    tg = gen.TestGenerator()
    cleaned = tg._clean_generated_code(code_with_md)
    assert cleaned == expected


@pytest.mark.parametrize(
    "source_file,expected_suffixes",
    [
        ("module.py", ["tests/test_module.py", "test_module.py", "tests/test_module.py"]),
        ("module.js", ["__tests__/module.test.js", "module.test.js", "tests/module.test.js"]),
        ("module.ts", ["__tests__/module.test.ts", "module.test.ts", "tests/module.test.ts"]),
        ("module.java", ["src/test/java/Testmodule.java", "Testmodule.java"]),
        ("module.unknown", ["tests/test_module.unknown", "test_module.unknown"]),
    ],
)
def test_test_generator_determine_test_file_path(tmp_path, source_file, expected_suffixes):
    source_path = tmp_path / source_file
    source_path.write_text("dummy")
    tg = gen.TestGenerator()
    test_file_path = tg.determine_test_file_path(str(source_path))
    # The returned path should be one of the expected patterns
    assert any(test_file_path.endswith(suffix) or test_file_path.endswith(suffix.replace("/", os.sep)) for suffix in expected_suffixes)
    # The directory should exist
    assert Path(test_file_path).parent.exists()


def test_main_no_github_token(monkeypatch, tmp_path):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(sys, "argv", ["generate_tests.py", "--coverage-data", "coverage.json"])

    with pytest.raises(SystemExit) as excinfo:
        gen.main()
    assert excinfo.value.code == 1


def test_main_invalid_coverage_file(monkeypatch, tmp_path):
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    coverage_file = tmp_path / "coverage.json"
    coverage_file.write_text("invalid json")

    monkeypatch.setattr(sys, "argv", ["generate_tests.py", "--coverage-data", str(coverage_file)])

    with pytest.raises(SystemExit) as excinfo:
        gen.main()
    assert excinfo.value.code == 1


def test_main_no_files_to_process(monkeypatch, tmp_path):
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    coverage_file = tmp_path / "coverage.json"
    coverage_file.write_text(json.dumps({"least_covered_files": []}))

    output_dir = tmp_path / "generated_tests"

    monkeypatch.setattr(sys, "argv", ["generate_tests.py", "--coverage-data", str(coverage_file), "--output-dir", str(output_dir)])

    # Should not raise, creates summary.json with zero files processed
    gen.main()

    summary_file = output_dir / "summary.json"
    assert summary_file.exists()
    summary = json.loads(summary_file.read_text())
    assert summary["files_processed"] == 0
    assert summary["tests_generated"] == 0


def test_main_process_files(monkeypatch, tmp_path):
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    source_file = tmp_path / "sample.py"
    source_file.write_text("def foo(): pass")

    coverage_data = {
        "least_covered_files": [
            {"filename": str(source_file), "coverage": 10.0},
        ]
    }
    coverage_file = tmp_path / "coverage.json"
    coverage_file.write_text(json.dumps(coverage_data))

    output_dir = tmp_path / "generated_tests"

    monkeypatch.setattr(sys, "argv", ["generate_tests.py", "--coverage-data", str(coverage_file), "--output-dir", str(output_dir), "--max-files", "1"])

    # Patch TestGenerator.generate_tests_for_file to return dummy test code
    with mock.patch.object(gen.TestGenerator, "generate_tests_for_file", return_value="# test code"):
        with mock.patch.object(gen.TestGenerator, "determine_test_file_path", return_value=str(output_dir / "test_sample.py")):
            gen.main()

    # Check generated test file exists and contains expected content
    test_file = output_dir / "test_sample.py"
    assert test_file.exists()
    content = test_file.read_text()
    assert content == "# test code"

    # Check summary file
    summary_file = output_dir / "summary.json"
    assert summary_file.exists()
    summary = json.loads(summary_file.read_text())
    assert summary["files_processed"] == 1
    assert summary["tests_generated"] == 1
    assert summary["generated_files"][0]["source_file"] == str(source_file)


def test_main_process_files_with_generation_error(monkeypatch, tmp_path):
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    source_file = tmp_path / "sample.py"
    source_file.write_text("def foo(): pass")

    coverage_data = {
        "least_covered_files": [
            {"filename": str(source_file), "coverage": 10.0},
            {"filename": "nonexistent.py", "coverage": 5.0},
        ]
    }
    coverage_file = tmp_path / "coverage.json"
    coverage_file.write_text(json.dumps(coverage_data))

    output_dir = tmp_path / "generated_tests"

    monkeypatch.setattr(sys, "argv", ["generate_tests.py", "--coverage-data", str(coverage_file), "--output-dir", str(output_dir), "--max-files", "10"])

    # Patch TestGenerator.generate_tests_for_file to raise on nonexistent file
    def side_effect(file_path, coverage, framework):
        if not Path(file_path).exists():
            raise Exception("File not found")
        return "# test code"

    with mock.patch.object(gen.TestGenerator, "generate_tests_for_file", side_effect=side_effect):
        with mock.patch.object(gen.TestGenerator, "determine_test_file_path", return_value=str(output_dir / "test_sample.py")):
            gen.main()

    # Check summary file
    summary_file = output_dir / "summary.json"
    assert summary_file.exists()
    summary = json.loads(summary_file.read_text())
    # Only one file processed successfully
    assert summary["files_processed"] == 1
    assert summary["tests_generated"] == 1


def test_source_code_analyzer_extract_generic_elements_filters_tests():
    content = """
def foo() {}
function bar() {}
class MyClass {}
class TestClass {}
def test_func() {}
def spec_func() {}
"""
    analyzer = gen.SourceCodeAnalyzer.__new__(gen.SourceCodeAnalyzer)
    analyzer.content = content
    analyzer.language = "javascript"
    elements = analyzer._extract_generic_elements()
    assert "foo" in elements["functions"]
    assert "bar" in elements["functions"]
    assert "MyClass" in elements["classes"]
    assert "TestClass" not in elements["classes"]
    assert "test_func" not in elements["functions"]
    assert "spec_func" not in elements["functions"]