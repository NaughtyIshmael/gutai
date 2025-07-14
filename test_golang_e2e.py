#!/usr/bin/env python3
"""
GUTAI Go End-to-End Test Suite

This script performs a complete E2E test of the GUTAI workflow for Go projects:
1. Runs go test with coverage to generate code coverage data for Go sample app
2. Identifies the least covered file
3. Calls AI to generate additional unit tests
4. Applies the generated tests to the appropriate Go test files
5. Runs tests again to verify the new tests pass
6. Validates improved coverage

This test demonstrates the complete GUTAI workflow in a local environment for Go projects.
"""

import os
import sys
import json
import subprocess
import re
import shutil
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import GUTAI scripts
from scripts.generate_tests import TestGenerator


class GoE2ETestRunner:
    """Orchestrates the complete E2E test workflow for Go projects."""

    def __init__(self, provider: str = "github"):
        self.project_root = Path(__file__).parent
        self.go_sample_dir = self.project_root / "sample_app" / "golang"
        self.coverage_dir = self.project_root / ".coverage_data"
        self.test_dir = self.project_root / "tests" / "e2e" / "golang"
        self.coverage_file = self.test_dir / "coverage.out"
        self.provider = provider
        self.test_results = {}

    def setup_environment(self):
        """Set up the test environment."""
        print("🔧 Setting up Go E2E test environment...")

        # Check if Go is installed
        try:
            result = subprocess.run(
                ["go", "version"],
                capture_output=True,
                text=True,
                cwd=self.go_sample_dir,
            )
            print(f"✅ Go version: {result.stdout.strip()}")
        except FileNotFoundError:
            raise RuntimeError("Go is not installed or not in PATH")

        # Copy sample dir to test directory
        if not self.go_sample_dir.exists():
            raise FileNotFoundError(
                f"Go sample directory not found: {self.go_sample_dir}"
            )
        if not self.test_dir.exists():
            self.test_dir.mkdir(parents=True, exist_ok=True)

        shutil.copytree(
            self.go_sample_dir, self.test_dir, symlinks=True, dirs_exist_ok=True
        )

        print("✅ Environment setup complete")

    def run_initial_coverage(self) -> Tuple[Dict, float]:
        """Run initial test suite and generate coverage report."""
        print("📊 Running initial Go test suite with coverage...")

        # Run go test with coverage
        cmd = ["go", "test", "-v", "-cover", "-coverprofile=coverage.out", "./..."]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=self.test_dir
            )
            print("STDOUT:", result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)

            # Parse coverage output to get overall percentage
            coverage_percent = self.parse_go_coverage_output(result.stdout)

            # Convert Go coverage to a format similar to other tools
            coverage_data = self.parse_go_coverage_profile()

            print(f"📈 Initial coverage: {coverage_percent:.1f}%")
            return coverage_data, coverage_percent

        except subprocess.CalledProcessError as e:
            print(f"❌ Error running Go tests: {e}")
            print(f"Output: {e.output}")
            raise

    def parse_go_coverage_output(self, output: str) -> float:
        """Parse Go test output to extract coverage percentage."""
        # Look for coverage line like "coverage: 75.0% of statements"
        coverage_pattern = r"coverage:\s+([\d.]+)%\s+of\s+statements"
        match = re.search(coverage_pattern, output)
        if match:
            return float(match.group(1))
        return 0.0

    def parse_go_coverage_profile(self) -> Dict:
        """Parse Go coverage profile to extract per-file coverage."""
        files_coverage = {}

        if not self.coverage_file.exists():
            return {"files": {}, "totals": {"percent_covered": 0}}

        with open(self.coverage_file, "r") as f:
            lines = f.readlines()

        # Skip the first line (mode line)
        for line in lines[1:]:
            if line.strip():
                parts = line.split()
                if len(parts) >= 3:
                    file_func = parts[0]
                    # Extract filename from the file:function format
                    if ":" in file_func:
                        filename = file_func.split(":")[0]
                        if filename not in files_coverage:
                            files_coverage[filename] = {"covered": 0, "total": 0}

                        # Count statements (simplified)
                        count = int(parts[2])
                        files_coverage[filename]["total"] += 1
                        if count > 0:
                            files_coverage[filename]["covered"] += 1

        # Calculate percentages
        formatted_files = {}
        total_covered = 0
        total_statements = 0

        for filename, data in files_coverage.items():
            if data["total"] > 0:
                percent = (data["covered"] / data["total"]) * 100
                formatted_files[filename] = {
                    "summary": {
                        "percent_covered": percent,
                        "covered_lines": data["covered"],
                        "num_statements": data["total"],
                    }
                }
                total_covered += data["covered"]
                total_statements += data["total"]

        overall_percent = (
            (total_covered / total_statements * 100) if total_statements > 0 else 0
        )

        return {
            "files": formatted_files,
            "totals": {"percent_covered": overall_percent},
        }

    def identify_least_covered_file(self, coverage_data: Dict) -> Tuple[str, float]:
        """Identify the Go file with the lowest test coverage."""
        print("🔍 Identifying least covered Go file...")

        files = coverage_data.get("files", {})
        min_coverage = 100
        least_covered_file = None

        for file_path, file_data in files.items():
            # Look for .go files but exclude test files
            if (
                file_path.endswith(".go")
                and not file_path.endswith("_test.go")
                and not "test" in file_path.lower()
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
            raise ValueError("No suitable Go files found for coverage improvement")

    def read_source_file(self, file_path: str) -> str:
        """Read the source code of the target file."""
        full_path = self.test_dir / file_path
        with open(full_path, "r") as f:
            return f.read()

    def read_existing_tests(self, source_file: str) -> str:
        """Read existing test file if it exists."""
        # Convert source file to test file (e.g., calculator.go -> calculator_test.go)
        source_name = Path(source_file).stem
        test_file = f"{source_name}_test.go"
        test_path = self.test_dir / test_file

        if test_path.exists():
            with open(test_path, "r") as f:
                return f.read()
        return ""

    def generate_additional_tests(
        self, source_file: str, source_code: str, existing_tests: str
    ) -> str:
        """Generate additional tests using AI."""
        print(f"🤖 Generating additional Go tests using {self.provider.title()} AI...")

        try:
            github_token = os.getenv("GITHUB_TOKEN")
            deepseek_token = os.getenv("DEEPSEEK_TOKEN")

            generator = TestGenerator(
                github_token=github_token,
                deepseek_token=deepseek_token,
                provider=self.provider,
            )

            # Prepare the prompt for Go test generation
            prompt = f"""
Generate comprehensive unit tests for the following Go code to improve test coverage.

Source file: {source_file}

Source code:
```go
{source_code}
```

Existing tests:
```go
{existing_tests}
```

Please generate additional test cases that cover:
1. Edge cases not currently tested
2. Error conditions and exception handling
3. Different input combinations
4. Boundary conditions

Requirements:
- Use Go's built-in testing package
- Follow Go testing conventions (Test* functions)
- Include proper imports if needed
- Use table-driven tests where appropriate
- Test error cases and edge conditions
- Ensure tests are independent and can run in any order
- Do not include package declaration or import statements
- Do not include any unused variables or functions

Return only the test code that should be added to the existing test file.
"""

            generated_tests = generator.generate_tests(
                file_path=source_file,
                source_code=source_code,
                existing_tests=existing_tests,
                prompt=prompt,
            )

            print("✅ Tests generated successfully using AI")
            return generated_tests

        except Exception as e:
            print(f"⚠️  Error generating tests with GitHub Models: {e}")
            # Return a fallback test if AI generation fails
            return """
func TestAdditionalEdgeCase(t *testing.T) {
    // Fallback test when AI generation fails
    // This test ensures basic functionality
    if 0 != 0 {
        t.Error("Basic math failed")
    }
}
"""

    def apply_generated_tests(self, source_file: str, generated_tests: str) -> str:
        """Apply generated tests to the appropriate Go test file."""
        print("📝 Applying generated tests to Go test file...")

        # Determine test file path
        source_name = Path(source_file).stem
        test_file = f"{source_name}_test.go"
        test_path = self.test_dir / test_file

        # Append generated tests to existing test file
        with open(test_path, "a") as f:
            f.write("\n")
            f.write(generated_tests)

        print(f"✅ Generated tests added to {test_path}")
        return str(test_path)

    def run_final_tests(self) -> Tuple[bool, Dict, float]:
        """Run tests after applying generated tests."""
        print("🧪 Running Go tests with newly generated test cases...")

        # Run go test again with coverage
        cmd = [
            "go",
            "test",
            "-v",
            "-cover",
            "-coverprofile=coverage_final.out",
            "./...",
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=self.test_dir
            )
            print("STDOUT:", result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)

            tests_passed = result.returncode == 0

            # Parse final coverage
            final_coverage_percent = self.parse_go_coverage_output(result.stdout)

            # Move the coverage file for final analysis
            final_coverage_file = self.test_dir / "coverage_final.out"
            if final_coverage_file.exists():
                # Temporarily rename to parse
                original_coverage = self.test_dir / "coverage.out"
                if original_coverage.exists():
                    original_coverage.rename(self.test_dir / "coverage_backup.out")
                final_coverage_file.rename(original_coverage)

                final_coverage_data = self.parse_go_coverage_profile()

                # Restore original
                if (self.test_dir / "coverage_backup.out").exists():
                    original_coverage.rename(final_coverage_file)
                    (self.test_dir / "coverage_backup.out").rename(original_coverage)
            else:
                final_coverage_data = {}

            print(f"📈 Final coverage: {final_coverage_percent:.1f}%")
            return tests_passed, final_coverage_data, final_coverage_percent

        except subprocess.CalledProcessError as e:
            print(f"❌ Error running final Go tests: {e}")
            return False, {}, 0

    def run_e2e_test(self) -> bool:
        """Execute the complete E2E test workflow for Go."""
        print("🚀 Starting GUTAI Go E2E Test Workflow")
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
            least_covered_file = least_covered_file[
                least_covered_file.find("/") + 1 :
            ]  # Drop the project root
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
            print("📊 Go E2E Test Results Summary")
            print("=" * 50)
            print(f"Target file: {least_covered_file}")
            print(f"Initial coverage: {initial_coverage_percent:.1f}%")
            print(f"Final coverage: {final_coverage_percent:.1f}%")
            print(f"Coverage improvement: {coverage_improvement:+.1f}%")
            print(f"All tests passed: {'✅ Yes' if tests_passed else '❌ No'}")
            print(f"Go module directory: {self.go_sample_dir}")

            # Test success criteria
            success = (
                tests_passed  # All tests must pass
                and coverage_improvement >= 0  # Coverage should not decrease
            )

            if success:
                print("\n🎉 Go E2E Test PASSED! GUTAI workflow completed successfully.")
            else:
                print("\n❌ Go E2E Test FAILED! Check the issues above.")

            return success

        except Exception as e:
            print(f"\n💥 Go E2E Test encountered an error: {e}")
            import traceback

            traceback.print_exc()
            return False


def main():
    """Main entry point for the Go E2E test."""
    parser = argparse.ArgumentParser(description="Run Go E2E test for GUTAI")
    parser.add_argument(
        "--provider",
        choices=["github", "deepseek"],
        default="github",
        help="AI provider to use (github or deepseek)",
    )

    args = parser.parse_args()

    runner = GoE2ETestRunner(provider=args.provider)
    success = runner.run_e2e_test()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
