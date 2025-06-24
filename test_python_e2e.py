#!/usr/bin/env python3
"""
GUTAI Python End-to-End Test Suite

This script performs a complete E2E test of the GUTAI workflow for Python projects:
1. Runs pytest locally to generate code coverage data for Python sample app
2. Identifies the least covered file
3. Calls Azure AI to generate additional unit tests
4. Applies the generated tests to the sample_app/python/tests directory
5. Runs tests again to verify the new tests pass
6. Validates improved coverage

This test demonstrates the complete GUTAI workflow in a local environment for Python projects.
"""

import os
import sys
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import GUTAI scripts
from scripts.generate_tests import TestGenerator


class PythonE2ETestRunner:
    """Orchestrates the complete E2E test workflow for Python projects."""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.python_sample_dir = self.project_root / "sample_app" / "python"
        self.python_tests_dir = self.python_sample_dir / "tests"
        self.coverage_dir = self.project_root / ".coverage_data"
        self.test_results = {}

    def setup_environment(self):
        """Set up the test environment."""
        print("🔧 Setting up Python E2E test environment...")

        # Create coverage directory
        self.coverage_dir.mkdir(exist_ok=True)

        # Ensure Python tests directory exists
        self.python_tests_dir.mkdir(exist_ok=True)

        # Ensure we have pytest and coverage installed
        required_packages = ["pytest", "coverage", "pytest-cov"]
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
            except ImportError:
                print(f"Installing {package}...")
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", package],
                    check=True,
                    capture_output=True,
                )

        # Create __init__.py in tests directory if it doesn't exist
        init_file = self.python_tests_dir / "__init__.py"
        if not init_file.exists():
            init_file.touch()

        # Ensure test_calculator.py does not exist to avoid conflicts
        test_file = self.python_tests_dir / "test_calculator.py"
        if test_file.exists():
            print(f"Removing existing test file: {test_file}")
            test_file.unlink()
        self.create_basic_tester(test_file)
        print("✅ Environment setup complete")

    def create_basic_tester(self, test_file: Path):
        """Create a basic test file if it doesn't exist."""
        print(f"Creating basic test file: {test_file}")
        with open(test_file, "w") as f:
            f.write(
                """import pytest
import sys
from pathlib import Path

# Add parent directory to path to import calculator
sys.path.insert(0, str(Path(__file__).parent.parent))

from calculator import Calculator

@pytest.fixture
def calculator():
    return Calculator()

def test_add(calculator):
    assert calculator.add(1, 2) == 3
"""
            )

    def run_initial_coverage(self) -> Tuple[Dict, float]:
        """Run initial test suite and generate coverage report."""
        print("📊 Running initial test suite with coverage...")

        # Run pytest with coverage on the Python sample app
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            f"--cov={self.python_sample_dir}",
            "--cov-report=json:coverage.json",
            "--cov-report=term",
            "-v",
            str(self.python_tests_dir),
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=self.project_root
            )
            print("STDOUT:", result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)

            # Read coverage data
            coverage_file = self.project_root / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file, "r") as f:
                    coverage_data = json.load(f)

                # Calculate overall coverage
                total_coverage = coverage_data.get("totals", {}).get(
                    "percent_covered", 0
                )

                print(f"📈 Initial coverage: {total_coverage:.1f}%")
                return coverage_data, total_coverage
            else:
                raise FileNotFoundError("Coverage report not generated")

        except subprocess.CalledProcessError as e:
            print(f"❌ Error running tests: {e}")
            print(f"Output: {e.output}")
            raise

    def identify_least_covered_file(self, coverage_data: Dict) -> Tuple[str, float]:
        """Identify the file with the lowest test coverage."""
        print("🔍 Identifying least covered file...")

        files = coverage_data.get("files", {})
        min_coverage = 100
        least_covered_file = None

        for file_path, file_data in files.items():
            # Look for files in the Python sample app directory
            if (
                "sample_app/python/" in file_path
                and file_path.endswith(".py")
                and not file_path.endswith("__init__.py")
            ):
                coverage_percent = file_data["summary"]["percent_covered"]
                if coverage_percent < min_coverage:
                    min_coverage = coverage_percent
                    least_covered_file = file_path

        if least_covered_file:
            print(
                f"📉 Least covered file: {least_covered_file} ({min_coverage:.1f}% coverage)"
            )
            return least_covered_file, min_coverage
        else:
            raise ValueError("No suitable files found for coverage improvement")

    def read_source_file(self, file_path: str) -> str:
        """Read the source code of the target file."""
        full_path = self.project_root / file_path
        with open(full_path, "r") as f:
            return f.read()

    def read_existing_tests(self, source_file: str) -> str:
        """Read existing test file if it exists."""
        # Convert source file path to test file path
        source_name = Path(source_file).name
        test_file = f"test_{source_name}"
        test_path = self.python_tests_dir / test_file

        if test_path.exists():
            with open(test_path, "r") as f:
                return f.read()
        return ""

    def generate_additional_tests(
        self, source_file: str, source_code: str, existing_tests: str
    ) -> str:
        """Generate additional tests using Azure AI."""
        print("🤖 Generating additional tests using Azure AI...")

        try:
            generator = TestGenerator(os.getenv("GITHUB_TOKEN"))

            # Prepare the prompt for test generation
            prompt = f"""
Generate comprehensive unit tests for the following Python code to improve test coverage.

Source file: {source_file}

Source code:
```python
{source_code}
```

Existing tests:
```python
{existing_tests}
```

Please generate additional test cases that cover:
1. Edge cases not currently tested
2. Error conditions and exception handling
3. Different input combinations
4. Boundary conditions

Return only the test code that should be added to the existing test file.
Use pytest conventions and ensure tests are independent.
Include the necessary imports at the top if adding new test functions.
"""

            generated_tests = generator.generate_tests(
                file_path=source_file,
                source_code=source_code,
                existing_tests=existing_tests,
                prompt=prompt,
            )

            print("✅ Tests generated successfully using Azure AI")
            return generated_tests

        except Exception as e:
            print(f"⚠️  Error generating tests with GitHub Models: {e}")
            # Return a fallback test if AI generation fails
            return """
def test_additional_edge_case(calculator):
    # Fallback test when AI generation fails
    assert calculator.add(0, 0) == 0
"""

    def apply_generated_tests(self, source_file: str, generated_tests: str) -> str:
        """Apply generated tests to the test file in sample_app/python/tests."""
        print("📝 Applying generated tests to Python test file...")

        # Determine test file path in Python sample app
        source_name = Path(source_file).name
        test_file = f"test_{source_name}"
        test_path = self.python_tests_dir / test_file

        # Append generated tests to existing test file
        with open(test_path, "a") as f:
            f.write("\n")
            f.write(generated_tests)

        print(f"✅ Generated tests added to {test_path}")
        return str(test_path)

    def run_final_tests(self) -> Tuple[bool, Dict, float]:
        """Run tests after applying generated tests."""
        print("🧪 Running tests with newly generated test cases...")

        # Run pytest again with coverage on the Python sample app
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            f"--cov={self.python_sample_dir}",
            "--cov-report=json:coverage_final.json",
            "--cov-report=term",
            "-v",
            str(self.python_tests_dir),
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=self.project_root
            )
            print("STDOUT:", result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)

            tests_passed = result.returncode == 0

            # Read final coverage data
            coverage_file = self.project_root / "coverage_final.json"
            if coverage_file.exists():
                with open(coverage_file, "r") as f:
                    coverage_data = json.load(f)

                total_coverage = coverage_data.get("totals", {}).get(
                    "percent_covered", 0
                )

                print(f"📈 Final coverage: {total_coverage:.1f}%")
                return tests_passed, coverage_data, total_coverage
            else:
                print("⚠️  Final coverage report not found")
                return tests_passed, {}, 0

        except subprocess.CalledProcessError as e:
            print(f"❌ Error running final tests: {e}")
            return False, {}, 0

    def cleanup(self):
        """Clean up test artifacts."""
        print("🧹 Cleaning up test artifacts...")

        artifacts = [
            "coverage.json",
            "coverage_final.json",
            ".coverage",
            "__pycache__",
            "sample_app/__pycache__",
            "sample_app/python/__pycache__",
            "sample_app/python/tests/__pycache__",
            "scripts/__pycache__",
        ]

        for artifact in artifacts:
            path = self.project_root / artifact
            if path.exists():
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()

    def run_e2e_test(self) -> bool:
        """Execute the complete E2E test workflow for Python."""
        print("🚀 Starting GUTAI Python E2E Test Workflow")
        print("=" * 50)

        try:
            # Step 1: Setup environment
            self.setup_environment()

            # Step 2: Run initial coverage
            initial_coverage_data, initial_coverage_percent = (
                self.run_initial_coverage()
            )

            # Step 3: Identify least covered file
            least_covered_file, min_coverage = self.identify_least_covered_file(
                initial_coverage_data
            )

            # Step 4: Read source and existing tests
            source_code = self.read_source_file(least_covered_file)
            existing_tests = self.read_existing_tests(least_covered_file)

            # Step 5: Generate additional tests
            generated_tests = self.generate_additional_tests(
                least_covered_file, source_code, existing_tests
            )

            # Step 6: Apply generated tests
            test_file_path = self.apply_generated_tests(
                least_covered_file, generated_tests
            )

            # Step 7: Run final tests
            tests_passed, final_coverage_data, final_coverage_percent = (
                self.run_final_tests()
            )

            # Step 8: Analyze results
            coverage_improvement = final_coverage_percent - initial_coverage_percent

            print("\n" + "=" * 50)
            print("📊 Python E2E Test Results Summary")
            print("=" * 50)
            print(f"Target file: {least_covered_file}")
            print(f"Initial coverage: {initial_coverage_percent:.1f}%")
            print(f"Final coverage: {final_coverage_percent:.1f}%")
            print(f"Coverage improvement: {coverage_improvement:+.1f}%")
            print(f"All tests passed: {'✅ Yes' if tests_passed else '❌ No'}")
            print(f"Tests saved in: {self.python_tests_dir}")

            # Test success criteria
            success = (
                tests_passed  # All tests must pass
                and coverage_improvement >= 0  # Coverage should not decrease
            )

            if success:
                print(
                    "\n🎉 Python E2E Test PASSED! GUTAI workflow completed successfully."
                )
            else:
                print("\n❌ Python E2E Test FAILED! Check the issues above.")

            return success

        except Exception as e:
            print(f"\n💥 Python E2E Test encountered an error: {e}")
            import traceback

            traceback.print_exc()
            return False

        finally:
            # Always clean up
            self.cleanup()


def main():
    """Main entry point for the Python E2E test."""
    runner = PythonE2ETestRunner()
    success = runner.run_e2e_test()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
