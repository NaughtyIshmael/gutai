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


class DummyResponseChoice:
    def __init__(self, content):
        self.message = SimpleNamespace(content=content)


class DummyResponse:
    def __init__(self, content):
        self.choices = [DummyResponseChoice(content)]


@pytest.fixture
def dummy_github_token():
    return "dummy_token"


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
class MyClass {}
function publicFunction() {}
function _privateFunction() {}
function testFunction() {}
"""


@pytest.fixture
def temp_source_file(tmp_path, sample_python_code):
    file = tmp_path / "sample.py"
    file.write_text(sample_python_code)
    return str(file)


@pytest.fixture
def temp_js_file(tmp_path, sample_js_code):
    file = tmp_path / "sample.js"
    file.write_text(sample_js_code)
    return str(file)


class TestGitHubModelsClient:
    def test_generate_completion_success(self, dummy_github_token):
        client = gen.GitHubModelsClient(dummy_github_token)
        with mock.patch.object(client.client, "complete", return_value=DummyResponse("test code")) as mock_complete:
            result = client.generate_completion("prompt text")
            assert result == "test code"
            mock_complete.assert_called_once()
            args, kwargs = mock_complete.call_args
            assert any(isinstance(m, gen.SystemMessage) for m in kwargs["messages"])
            assert any(isinstance(m, gen.UserMessage) for m in kwargs["messages"])

    def test_generate_completion_raises_exception(self, dummy_github_token):
        client = gen.GitHubModelsClient(dummy_github_token)
        with mock.patch.object(client.client, "complete", side_effect=Exception("API error")):
            with pytest.raises(Exception) as excinfo:
                client.generate_completion("prompt")
            assert "GitHub Models API error" in str(excinfo.value)


class TestSourceCodeAnalyzer:
    def test_read_file_success(self, tmp_path, sample_python_code):
        file = tmp_path / "file.py"
        file.write_text(sample_python_code)
        analyzer = gen.SourceCodeAnalyzer(str(file))
        assert analyzer.content == sample_python_code

    def test_read_file_failure(self, tmp_path):
        file = tmp_path / "nonexistent.py"
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
    def test_detect_language(self, tmp_path, filename, expected_language):
        file = tmp_path / filename
        file.write_text("")
        analyzer = gen.SourceCodeAnalyzer(str(file))
        assert analyzer.language == expected_language

    def test_extract_python_elements(self, tmp_path, sample_python_code):
        file = tmp_path / "file.py"
        file.write_text(sample_python_code)
        analyzer = gen.SourceCodeAnalyzer(str(file))
        elements = analyzer.extract_code_elements()
        assert "MyClass" in elements["classes"]
        assert "public_function" in elements["functions"]
        # Private and test functions should be excluded
        assert "_private_function" not in elements["functions"]
        assert "test_function" not in elements["functions"]

    def test_extract_python_elements_syntax_error(self, tmp_path):
        file = tmp_path / "file.py"
        file.write_text("def foo(:\n pass")  # invalid syntax
        analyzer = gen.SourceCodeAnalyzer(str(file))
        elements = analyzer.extract_code_elements()
        # Should fallback to generic extraction (empty here)
        assert isinstance(elements, dict)
        assert "functions" in elements
        assert "classes" in elements

    def test_extract_generic_elements_filters_tests(self):
        content = """
        def real_function() {}
        function testFunction() {}
        class RealClass {}
        class TestClass {}
        """
        analyzer = gen.SourceCodeAnalyzer("file.js")
        analyzer.content = content
        analyzer.language = "javascript"
        elements = analyzer._extract_generic_elements()
        assert "real_function" in elements["functions"]
        assert "testFunction" not in elements["functions"]
        assert "RealClass" in elements["classes"]
        assert "TestClass" not in elements["classes"]


class TestTestGenerator:
    def test_init_with_token_creates_client(self, dummy_github_token):
        tg = gen.TestGenerator(dummy_github_token)
        assert tg.ai_client is not None
        assert isinstance(tg.ai_client, gen.GitHubModelsClient)

    def test_init_without_token_sets_client_none(self):
        tg = gen.TestGenerator()
        assert tg.ai_client is None

    def test_generate_tests_returns_mock_when_no_ai_client(self, tmp_path):
        tg = gen.TestGenerator()
        code = "def foo(): pass"
        result = tg.generate_tests("file.py", code)
        assert "# Mock test" in result

    def test_generate_tests_with_prompt_calls_ai_client(self, dummy_github_token):
        tg = gen.TestGenerator(dummy_github_token)
        prompt = "custom prompt"
        with mock.patch.object(tg.ai_client, "generate_completion", return_value="test code") as mock_gen:
            result = tg.generate_tests("file.py", "code", prompt=prompt)
            assert result == "test code"
            mock_gen.assert_called_once_with(prompt, tg.ai_model)

    def test_generate_tests_without_prompt_creates_prompt_and_calls_ai(self, dummy_github_token, tmp_path, sample_python_code):
        file = tmp_path / "file.py"
        file.write_text(sample_python_code)
        tg = gen.TestGenerator(dummy_github_token)
        with mock.patch.object(gen.SourceCodeAnalyzer, "extract_code_elements", return_value={"functions": ["public_function"], "classes": ["MyClass"]}):
            with mock.patch.object(tg.ai_client, "generate_completion", return_value="```python\ntest code\n```"):
                result = tg.generate_tests(str(file), sample_python_code)
                assert "test code" in result  # markdown removed

    def test__generate_mock_tests_returns_expected_string(self):
        tg = gen.TestGenerator()
        result = tg._generate_mock_tests("file.py", "code")
        assert result.startswith("# Mock test")

    def test_generate_tests_for_file_success(self, dummy_github_token, tmp_path, sample_python_code):
        file = tmp_path / "file.py"
        file.write_text(sample_python_code)
        tg = gen.TestGenerator(dummy_github_token)
        with mock.patch.object(gen.SourceCodeAnalyzer, "extract_code_elements", return_value={"functions": ["public_function"], "classes": ["MyClass"]}):
            with mock.patch.object(tg.ai_client, "generate_completion", return_value="```python\ntest code\n```"):
                result = tg.generate_tests_for_file(str(file), 75.0, "pytest")
                assert "test code" in result

    def test_generate_tests_for_file_no_file_raises(self):
        tg = gen.TestGenerator("token")
        with pytest.raises(Exception) as excinfo:
            tg.generate_tests_for_file("nonexistent.py", 50)
        assert "does not exist" in str(excinfo.value)

    def test_generate_tests_for_file_no_elements_raises(self, dummy_github_token, tmp_path):
        file = tmp_path / "file.py"
        file.write_text("pass")
        tg = gen.TestGenerator(dummy_github_token)
        with mock.patch.object(gen.SourceCodeAnalyzer, "extract_code_elements", return_value={"functions": [], "classes": []}):
            with pytest.raises(Exception) as excinfo:
                tg.generate_tests_for_file(str(file), 50)
            assert "No testable elements" in str(excinfo.value)

    def test_generate_tests_for_file_no_ai_client_raises(self, tmp_path, sample_python_code):
        file = tmp_path / "file.py"
        file.write_text(sample_python_code)
        tg = gen.TestGenerator()
        with mock.patch.object(gen.SourceCodeAnalyzer, "extract_code_elements", return_value={"functions": ["f"], "classes": ["C"]}):
            with pytest.raises(Exception) as excinfo:
                tg.generate_tests_for_file(str(file), 50)
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
    def test__detect_test_framework(self, language, expected_framework):
        tg = gen.TestGenerator()
        assert tg._detect_test_framework(language) == expected_framework

    def test__create_test_generation_prompt_contains_expected_parts(self):
        tg = gen.TestGenerator()
        prompt = tg._create_test_generation_prompt(
            "code",
            "python",
            {"functions": ["foo"], "classes": ["Bar"]},
            80.0,
            "file.py",
            "pytest",
        )
        assert "Generate comprehensive unit tests" in prompt
        assert "foo" in prompt
        assert "Bar" in prompt
        assert "80.0%" in prompt
        assert "pytest" in prompt
        assert "code" in prompt

    def test__clean_generated_code_removes_markdown(self):
        tg = gen.TestGenerator()
        code = "```python\nprint('hello')\n```"
        cleaned = tg._clean_generated_code(code)
        assert "```" not in cleaned
        assert "print('hello')" in cleaned

    @pytest.mark.parametrize(
        "source_file,expected_suffixes",
        [
            ("file.py", ["tests/test_file.py", "test_file.py", "tests/test_file.py"]),
            ("file.js", ["__tests__/file.test.js", "file.test.js", "tests/file.test.js"]),
            ("file.ts", ["__tests__/file.test.ts", "file.test.ts", "tests/file.test.ts"]),
            ("file.java", ["src/test/java/Testfile.java", "Testfile.java"]),
            ("file.unknown", ["tests/test_file.unknown", "test_file.unknown"]),
        ],
    )
    def test_determine_test_file_path_creates_dir_and_returns_path(self, tmp_path, source_file, expected_suffixes):
        file_path = tmp_path / source_file
        file_path.write_text("code")
        tg = gen.TestGenerator()
        # Patch mkdir to track calls
        with mock.patch.object(Path, "mkdir") as mock_mkdir:
            result = tg.determine_test_file_path(str(file_path))
            # Check that returned path ends with one of expected suffixes
            assert any(result.endswith(suffix) for suffix in expected_suffixes)
            # mkdir should be called at least once
            mock_mkdir.assert_called()

    def test_determine_test_file_path_creates_nested_dirs(self, tmp_path):
        file_path = tmp_path / "file.py"
        file_path.write_text("code")
        tg = gen.TestGenerator()
        # Remove tests directory if exists
        test_dir = tmp_path / "tests"
        if test_dir.exists():
            for child in test_dir.iterdir():
                child.unlink()
            test_dir.rmdir()
        # Should create tests directory
        result = tg.determine_test_file_path(str(file_path))
        assert Path(result).parent.exists()


class TestMainFunction:
    def setup_method(self):
        self.env_patcher = mock.patch.dict(os.environ, {"GITHUB_TOKEN": "token"})
        self.env_patcher.start()
        self.tmp_dir = Path("test_output_dir")
        if self.tmp_dir.exists():
            for f in self.tmp_dir.iterdir():
                f.unlink()
            self.tmp_dir.rmdir()

    def teardown_method(self):
        self.env_patcher.stop()
        if self.tmp_dir.exists():
            for f in self.tmp_dir.iterdir():
                f.unlink()
            self.tmp_dir.rmdir()

    def test_main_exits_if_no_github_token(self, monkeypatch):
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        testargs = [
            "prog",
            "--coverage-data",
            "coverage.json",
        ]
        monkeypatch.setattr(sys, "argv", testargs)
        with pytest.raises(SystemExit) as e:
            gen.main()
        assert e.value.code == 1

    def test_main_exits_if_coverage_data_load_fails(self, monkeypatch, tmp_path):
        monkeypatch.setenv("GITHUB_TOKEN", "token")
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{ invalid json }")
        monkeypatch.setattr(sys, "argv", ["prog", "--coverage-data", str(bad_file)])
        with pytest.raises(SystemExit) as e:
            gen.main()
        assert e.value.code == 1

    def test_main_no_files_to_process_creates_empty_summary(self, monkeypatch, tmp_path):
        monkeypatch.setenv("GITHUB_TOKEN", "token")
        coverage_file = tmp_path / "coverage.json"
        coverage_file.write_text(json.dumps({"least_covered_files": []}))
        output_dir = tmp_path / "out"
        monkeypatch.setattr(sys, "argv", ["prog", "--coverage-data", str(coverage_file), "--output-dir", str(output_dir)])
        gen.main()
        summary_file = output_dir / "summary.json"
        assert summary_file.exists()
        summary = json.loads(summary_file.read_text())
        assert summary["files_processed"] == 0
        assert summary["tests_generated"] == 0

    def test_main_processes_files_successfully(self, monkeypatch, tmp_path):
        monkeypatch.setenv("GITHUB_TOKEN", "token")
        source_file = tmp_path / "file.py"
        source_file.write_text("def foo(): pass")
        coverage_data = {
            "least_covered_files": [
                {"filename": str(source_file), "coverage": 20.0}
            ]
        }
        coverage_file = tmp_path / "coverage.json"
        coverage_file.write_text(json.dumps(coverage_data))
        output_dir = tmp_path / "out"
        monkeypatch.setattr(sys, "argv", ["prog", "--coverage-data", str(coverage_file), "--output-dir", str(output_dir)])

        # Patch TestGenerator to avoid real AI calls
        with mock.patch.object(gen.TestGenerator, "generate_tests_for_file", return_value="# test code"):
            with mock.patch.object(gen.TestGenerator, "determine_test_file_path", return_value=str(output_dir / "test_file.py")):
                gen.main()
                test_file = output_dir / "test_file.py"
                assert test_file.exists()
                content = test_file.read_text()
                assert "# test code" in content
                summary_file = output_dir / "summary.json"
                assert summary_file.exists()
                summary = json.loads(summary_file.read_text())
                assert summary["files_processed"] == 1
                assert summary["tests_generated"] == 1
                assert summary["generated_files"][0]["source_file"] == str(source_file)

    def test_main_handles_generation_errors_and_continues(self, monkeypatch, tmp_path):
        monkeypatch.setenv("GITHUB_TOKEN", "token")
        source_file1 = tmp_path / "file1.py"
        source_file1.write_text("def foo(): pass")
        source_file2 = tmp_path / "file2.py"
        source_file2.write_text("def bar(): pass")
        coverage_data = {
            "least_covered_files": [
                {"filename": str(source_file1), "coverage": 20.0},
                {"filename": str(source_file2), "coverage": 30.0},
            ]
        }
        coverage_file = tmp_path / "coverage.json"
        coverage_file.write_text(json.dumps(coverage_data))
        output_dir = tmp_path / "out"
        monkeypatch.setattr(sys, "argv", ["prog", "--coverage-data", str(coverage_file), "--output-dir", str(output_dir)])

        def side_effect(file_path, coverage, test_framework="auto"):
            if "file1" in file_path:
                raise Exception("Generation error")
            return "# test code"

        with mock.patch.object(gen.TestGenerator, "generate_tests_for_file", side_effect=side_effect):
            with mock.patch.object(gen.TestGenerator, "determine_test_file_path", return_value=str(output_dir / "test_file.py")):
                gen.main()
                summary_file = output_dir / "summary.json"
                assert summary_file.exists()
                summary = json.loads(summary_file.read_text())
                # Only one file processed successfully
                assert summary["files_processed"] == 1
                assert summary["tests_generated"] == 1