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
from scripts import generate_tests as gt


class DummyResponseChoice:
    def __init__(self, content):
        self.message = SimpleNamespace(content=content)


class DummyResponse:
    def __init__(self, content):
        self.choices = [DummyResponseChoice(content)]


@pytest.fixture
def dummy_github_client(monkeypatch):
    client_instance = mock.Mock()
    monkeypatch.setattr(gt, "ChatCompletionsClient", lambda *args, **kwargs: client_instance)
    monkeypatch.setattr(gt, "AzureKeyCredential", lambda token: token)
    return client_instance


def test_github_models_client_generate_completion_success(monkeypatch, dummy_github_client):
    dummy_github_client.complete.return_value = DummyResponse("test completion")
    client = gt.GitHubModelsClient("token")
    result = client.generate_completion("prompt")
    assert result == "test completion"
    dummy_github_client.complete.assert_called_once()
    # Check that the messages contain SystemMessage and UserMessage
    messages = dummy_github_client.complete.call_args[1]["messages"]
    assert any(isinstance(m, gt.SystemMessage) for m in messages)
    assert any(isinstance(m, gt.UserMessage) for m in messages)


def test_github_models_client_generate_completion_exception(monkeypatch, dummy_github_client):
    dummy_github_client.complete.side_effect = RuntimeError("fail")
    client = gt.GitHubModelsClient("token")
    with pytest.raises(Exception) as excinfo:
        client.generate_completion("prompt")
    assert "GitHub Models API error" in str(excinfo.value)


def test_source_code_analyzer_read_file_and_detect_language(tmp_path):
    file_py = tmp_path / "file.py"
    file_py.write_text("print('hello')")
    analyzer = gt.SourceCodeAnalyzer(str(file_py))
    assert analyzer.content == "print('hello')"
    assert analyzer.language == "python"

    file_unknown = tmp_path / "file.unknown"
    file_unknown.write_text("data")
    analyzer2 = gt.SourceCodeAnalyzer(str(file_unknown))
    assert analyzer2.language == "unknown"


def test_source_code_analyzer_read_file_error(tmp_path):
    file_path = tmp_path / "nofile.py"
    with pytest.raises(Exception) as excinfo:
        gt.SourceCodeAnalyzer(str(file_path))
    assert "Error reading file" in str(excinfo.value)


def test_extract_python_elements_basic():
    source = """
class MyClass:
    def method(self):
        pass

def public_func():
    pass

def _private_func():
    pass

def test_func():
    pass
"""
    analyzer = gt.SourceCodeAnalyzer.__new__(gt.SourceCodeAnalyzer)
    analyzer.content = source
    analyzer.language = "python"
    elements = analyzer.extract_code_elements()
    assert "MyClass" in elements["classes"]
    assert "public_func" in elements["functions"]
    assert "_private_func" not in elements["functions"]
    assert "test_func" not in elements["functions"]


def test_extract_python_elements_syntax_error_fallback():
    source = "def func(:"
    analyzer = gt.SourceCodeAnalyzer.__new__(gt.SourceCodeAnalyzer)
    analyzer.content = source
    analyzer.language = "python"
    elements = analyzer.extract_code_elements()
    # Should fallback to generic extraction (empty here)
    assert isinstance(elements, dict)
    assert "functions" in elements
    assert "classes" in elements


@pytest.mark.parametrize(
    "source,expected_functions,expected_classes",
    [
        (
            """
            function jsFunc() {}
            class JsClass {}
            """,
            ["jsFunc"],
            ["JsClass"],
        ),
        (
            """
            void cFunc() {}
            struct CStruct {}
            """,
            ["cFunc"],
            ["CStruct"],
        ),
        (
            """
            func goFunc() {}
            interface GoInterface {}
            """,
            ["goFunc"],
            ["GoInterface"],
        ),
        (
            """
            public void javaFunc() {}
            class JavaClass {}
            """,
            ["javaFunc"],
            ["JavaClass"],
        ),
        (
            """
            fn rustFunc() {}
            struct RustStruct {}
            """,
            ["rustFunc"],
            ["RustStruct"],
        ),
        (
            """
            def test_func():
                pass
            class TestClass:
                pass
            """,
            [],
            [],
        ),
    ],
)
def test_extract_generic_elements(source, expected_functions, expected_classes):
    analyzer = gt.SourceCodeAnalyzer.__new__(gt.SourceCodeAnalyzer)
    analyzer.content = source
    analyzer.language = "javascript"  # force generic extraction
    elements = analyzer._extract_generic_elements()
    for func in expected_functions:
        assert func in elements["functions"]
    for cls in expected_classes:
        assert cls in elements["classes"]
    # test and spec names filtered out
    assert all("test" not in f.lower() and "spec" not in f.lower() for f in elements["functions"])
    assert all("test" not in c.lower() and "spec" not in c.lower() for c in elements["classes"])


def test_test_generator_generate_mock_tests():
    tg = gt.TestGenerator()
    result = tg._generate_mock_tests("file.py", "source")
    assert result.startswith("# Mock test generated")


def test_test_generator_generate_tests_with_no_ai_client_returns_mock():
    tg = gt.TestGenerator()
    result = tg.generate_tests("file.py", "source")
    assert result.startswith("# Mock test generated")


def test_test_generator_generate_tests_with_prompt(monkeypatch):
    dummy_client = mock.Mock()
    dummy_client.generate_completion.return_value = "generated code"
    tg = gt.TestGenerator()
    tg.ai_client = dummy_client
    result = tg.generate_tests("file.py", "source", prompt="custom prompt")
    dummy_client.generate_completion.assert_called_once_with("custom prompt", tg.ai_model)
    assert result == "generated code"


def test_test_generator_generate_tests_without_prompt(monkeypatch, tmp_path):
    source_code = "def func(): pass"
    file_path = tmp_path / "file.py"
    file_path.write_text(source_code)
    dummy_client = mock.Mock()
    dummy_client.generate_completion.return_value = "```python\nprint('test')\n```"
    tg = gt.TestGenerator()
    tg.ai_client = dummy_client
    result = tg.generate_tests(str(file_path), source_code)
    dummy_client.generate_completion.assert_called_once()
    # Markdown removed
    assert "```" not in result
    assert "print('test')" in result


def test_test_generator_generate_tests_for_file_success(monkeypatch, tmp_path):
    source_code = "def func(): pass"
    file_path = tmp_path / "file.py"
    file_path.write_text(source_code)

    dummy_client = mock.Mock()
    dummy_client.generate_completion.return_value = "```python\nprint('test')\n```"

    monkeypatch.setattr(gt, "SourceCodeAnalyzer", lambda fp: SimpleNamespace(
        content=source_code,
        language="python",
        extract_code_elements=lambda: {"functions": ["func"], "classes": []},
    ))

    tg = gt.TestGenerator()
    tg.ai_client = dummy_client
    result = tg.generate_tests_for_file(str(file_path), 75.0, "pytest")
    dummy_client.generate_completion.assert_called_once()
    assert "print('test')" in result
    assert "```" not in result


def test_test_generator_generate_tests_for_file_no_file(tmp_path):
    tg = gt.TestGenerator()
    with pytest.raises(Exception) as excinfo:
        tg.generate_tests_for_file(str(tmp_path / "nofile.py"), 50)
    assert "Source file does not exist" in str(excinfo.value)


def test_test_generator_generate_tests_for_file_no_elements(monkeypatch, tmp_path):
    file_path = tmp_path / "file.py"
    file_path.write_text("")

    monkeypatch.setattr(gt, "SourceCodeAnalyzer", lambda fp: SimpleNamespace(
        content="",
        language="python",
        extract_code_elements=lambda: {"functions": [], "classes": []},
    ))

    tg = gt.TestGenerator()
    tg.ai_client = mock.Mock()
    with pytest.raises(Exception) as excinfo:
        tg.generate_tests_for_file(str(file_path), 50)
    assert "No testable elements found" in str(excinfo.value)


def test_test_generator_generate_tests_for_file_no_ai_client(monkeypatch, tmp_path):
    file_path = tmp_path / "file.py"
    file_path.write_text("def func(): pass")

    monkeypatch.setattr(gt, "SourceCodeAnalyzer", lambda fp: SimpleNamespace(
        content="def func(): pass",
        language="python",
        extract_code_elements=lambda: {"functions": ["func"], "classes": []},
    ))

    tg = gt.TestGenerator()
    tg.ai_client = None
    with pytest.raises(Exception) as excinfo:
        tg.generate_tests_for_file(str(file_path), 50)
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
    tg = gt.TestGenerator()
    assert tg._detect_test_framework(language) == expected_framework


def test_test_generator_create_test_generation_prompt():
    tg = gt.TestGenerator()
    source_code = "def func(): pass"
    elements = {"functions": ["func"], "classes": ["MyClass"]}
    prompt = tg._create_test_generation_prompt(
        source_code, "python", elements, 80.0, "file.py", "pytest"
    )
    assert "Generate comprehensive unit tests" in prompt
    assert "func" in prompt
    assert "MyClass" in prompt
    assert "pytest" in prompt
    assert "80.0%" in prompt


def test_test_generator_clean_generated_code():
    tg = gt.TestGenerator()
    code = "```python\nprint('hello')\n```"
    cleaned = tg._clean_generated_code(code)
    assert cleaned == "print('hello')"

    code2 = "```\ncode\n```"
    assert tg._clean_generated_code(code2) == "code"

    code3 = "no markdown"
    assert tg._clean_generated_code(code3) == "no markdown"


def test_test_generator_determine_test_file_path_creates_dirs(tmp_path):
    tg = gt.TestGenerator()

    # Python file
    source_file = tmp_path / "module.py"
    source_file.write_text("def func(): pass")
    test_path = tg.determine_test_file_path(str(source_file))
    p = Path(test_path)
    assert p.name.startswith("test_")
    assert p.parent.exists()

    # JS file
    source_file_js = tmp_path / "file.js"
    source_file_js.write_text("function f(){}")
    test_path_js = tg.determine_test_file_path(str(source_file_js))
    pjs = Path(test_path_js)
    assert pjs.name.endswith(".test.js")
    assert pjs.parent.exists()

    # Java file
    source_file_java = tmp_path / "MyClass.java"
    source_file_java.write_text("class MyClass {}")
    test_path_java = tg.determine_test_file_path(str(source_file_java))
    pjava = Path(test_path_java)
    assert pjava.name.startswith("TestMyClass")
    assert pjava.parent.exists()

    # Unknown extension
    source_file_txt = tmp_path / "file.txt"
    source_file_txt.write_text("data")
    test_path_txt = tg.determine_test_file_path(str(source_file_txt))
    ptxt = Path(test_path_txt)
    assert ptxt.name.startswith("test_")
    assert ptxt.parent.exists()


@mock.patch.dict(os.environ, {"GITHUB_TOKEN": "token"})
def test_main_no_coverage_data_file(tmp_path, capsys):
    coverage_file = tmp_path / "coverage.json"
    coverage_file.write_text("not json")
    sys_argv = [
        "prog",
        "--coverage-data",
        str(coverage_file),
    ]
    with mock.patch.object(sys, "argv", sys_argv):
        with pytest.raises(SystemExit):
            gt.main()
    captured = capsys.readouterr()
    assert "Error loading coverage data" in captured.out


@mock.patch.dict(os.environ, {"GITHUB_TOKEN": "token"})
def test_main_no_least_covered_files(tmp_path, capsys):
    coverage_file = tmp_path / "coverage.json"
    coverage_file.write_text(json.dumps({"least_covered_files": []}))
    output_dir = tmp_path / "out"
    sys_argv = [
        "prog",
        "--coverage-data",
        str(coverage_file),
        "--output-dir",
        str(output_dir),
    ]
    with mock.patch.object(sys, "argv", sys_argv):
        gt.main()
    captured = capsys.readouterr()
    assert "No files to process" in captured.out
    summary_file = output_dir / "summary.json"
    assert summary_file.exists()
    summary = json.loads(summary_file.read_text())
    assert summary["files_processed"] == 0


@mock.patch.dict(os.environ, {"GITHUB_TOKEN": "token"})
def test_main_process_files(tmp_path, monkeypatch, capsys):
    source_file = tmp_path / "file.py"
    source_file.write_text("def func(): pass")

    coverage_data = {
        "least_covered_files": [
            {"filename": str(source_file), "coverage": 10.0},
        ]
    }
    coverage_file = tmp_path / "coverage.json"
    coverage_file.write_text(json.dumps(coverage_data))

    # Patch SourceCodeAnalyzer to avoid actual file reading
    monkeypatch.setattr(gt, "SourceCodeAnalyzer", lambda fp: SimpleNamespace(
        content="def func(): pass",
        language="python",
        extract_code_elements=lambda: {"functions": ["func"], "classes": []},
    ))

    # Patch GitHubModelsClient to avoid real API calls
    class DummyAIClient:
        def generate_completion(self, prompt, model):
            return "print('test')"

    monkeypatch.setattr(gt, "GitHubModelsClient", lambda token: DummyAIClient())

    sys_argv = [
        "prog",
        "--coverage-data",
        str(coverage_file),
        "--output-dir",
        str(tmp_path / "out"),
        "--max-files",
        "1",
    ]
    with mock.patch.object(sys, "argv", sys_argv):
        gt.main()

    captured = capsys.readouterr()
    assert "Processing file 1/1" in captured.out
    out_dir = tmp_path / "out"
    summary_file = out_dir / "summary.json"
    assert summary_file.exists()
    summary = json.loads(summary_file.read_text())
    assert summary["files_processed"] == 1
    assert summary["tests_generated"] == 1
    assert len(summary["generated_files"]) == 1
    assert "test_file.py" in summary["generated_files"][0]["test_file"] or "test_file.py" in summary["generated_files"][0]["test_file"]


@mock.patch.dict(os.environ, {}, clear=True)
def test_main_missing_github_token(monkeypatch, capsys):
    sys_argv = [
        "prog",
        "--coverage-data",
        "dummy.json",
    ]
    with mock.patch.object(sys, "argv", sys_argv):
        with pytest.raises(SystemExit):
            gt.main()
    captured = capsys.readouterr()
    assert "GITHUB_TOKEN environment variable is required" in captured.out


def test_main_handles_generation_error(tmp_path, monkeypatch, capsys):
    source_file = tmp_path / "file.py"
    source_file.write_text("def func(): pass")

    coverage_data = {
        "least_covered_files": [
            {"filename": str(source_file), "coverage": 10.0},
            {"filename": "nonexistent.py", "coverage": 5.0},
        ]
    }
    coverage_file = tmp_path / "coverage.json"
    coverage_file.write_text(json.dumps(coverage_data))

    monkeypatch.setattr(gt, "SourceCodeAnalyzer", lambda fp: SimpleNamespace(
        content="def func(): pass",
        language="python",
        extract_code_elements=lambda: {"functions": ["func"], "classes": []},
    ))

    class DummyAIClient:
        def generate_completion(self, prompt, model):
            raise Exception("API failure")

    monkeypatch.setattr(gt, "GitHubModelsClient", lambda token: DummyAIClient())

    sys_argv = [
        "prog",
        "--coverage-data",
        str(coverage_file),
        "--output-dir",
        str(tmp_path / "out"),
        "--max-files",
        "3",
    ]
    with mock.patch.object(sys, "argv", sys_argv):
        gt.main()
    captured = capsys.readouterr()
    assert "Error generating tests for" in captured.out