#!/usr/bin/env python3
"""
Script to generate unit tests using GitHub Models AI.
"""

import os
import sys
import json
import argparse
import ast
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential


class GitHubModelsClient:
    """Client to interact with GitHub Models API"""

    def __init__(self, github_token: str):
        self.github_token = github_token
        self.endpoint = "https://models.github.ai/inference"
        self.client = ChatCompletionsClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(github_token),
        )

    def generate_completion(
        self, prompt: str, model: str = "openai/gpt-4.1-mini"
    ) -> str:
        """Generate AI completion using GitHub Models"""
        try:
            response = self.client.complete(
                messages=[
                    SystemMessage(
                        "You are an expert software engineer specializing in writing comprehensive unit tests. Generate clean, well-documented, and thorough test cases that follow best practices for the given programming language. Do not include any explanatory text, just return the test code."
                    ),
                    UserMessage(prompt),
                ],
                model=model,
                temperature=0.2,
                top_p=1.0,
                max_tokens=4096,
            )

            return response.choices[0].message.content

        except Exception as e:
            raise Exception(f"GitHub Models API error: {str(e)}")


class SourceCodeAnalyzer:
    """Analyze source code to understand structure"""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.content = self._read_file()
        self.language = self._detect_language()

    def _read_file(self) -> str:
        """Read the source file content"""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise Exception(f"Error reading file {self.file_path}: {e}")

    def _detect_language(self) -> str:
        """Detect programming language from file extension"""
        extension = self.file_path.suffix.lower()
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".cxx": "cpp",
            ".c": "c",
            ".cs": "csharp",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php",
        }
        return language_map.get(extension, "unknown")

    def extract_code_elements(self) -> Dict[str, List[str]]:
        """Extract functions and classes from the source code"""
        if self.language == "python":
            return self._extract_python_elements()
        else:
            return self._extract_generic_elements()

    def _extract_python_elements(self) -> Dict[str, List[str]]:
        """Extract Python functions and classes using AST"""
        try:
            tree = ast.parse(self.content)

            classes = []
            functions = []

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    if not node.name.startswith("_") and not node.name.startswith(
                        "test_"
                    ):
                        functions.append(node.name)

            return {"classes": classes, "functions": functions}
        except SyntaxError:
            return self._extract_generic_elements()

    def _extract_generic_elements(self) -> Dict[str, List[str]]:
        """Extract functions and classes using regex patterns"""
        functions = []
        classes = []

        # Function patterns for different languages
        function_patterns = [
            r"def\s+(\w+)\s*\(",  # Python
            r"function\s+(\w+)\s*\(",  # JavaScript
            r"(\w+)\s*\([^)]*\)\s*{",  # C-style
            r"func\s+(\w+)\s*\(",  # Go
            r"fn\s+(\w+)\s*\(",  # Rust
            r"public\s+\w+\s+(\w+)\s*\(",  # Java/C#
        ]

        # Class patterns
        class_patterns = [
            r"class\s+(\w+)",  # Python, JS, Java, C#
            r"struct\s+(\w+)",  # C, Go, Rust
            r"interface\s+(\w+)",  # TypeScript, Java, C#
        ]

        for pattern in function_patterns:
            matches = re.findall(pattern, self.content, re.MULTILINE)
            functions.extend(matches)

        for pattern in class_patterns:
            matches = re.findall(pattern, self.content, re.MULTILINE)
            classes.extend(matches)

        # Remove duplicates and filter out test-related names
        functions = list(
            set(
                [
                    f
                    for f in functions
                    if not any(test_word in f.lower() for test_word in ["test", "spec"])
                ]
            )
        )
        classes = list(
            set(
                [
                    c
                    for c in classes
                    if not any(test_word in c.lower() for test_word in ["test", "spec"])
                ]
            )
        )

        return {"classes": classes, "functions": functions}


class TestGenerator:
    """Generate unit tests for source code files"""

    def __init__(
        self, github_token: Optional[str] = None, ai_model: str = "openai/gpt-4.1-mini"
    ):
        self.ai_model = ai_model
        if github_token:
            self.ai_client = GitHubModelsClient(github_token)
        else:
            self.ai_client = None

    def generate_tests(
        self,
        file_path: str,
        source_code: str,
        existing_tests: str = "",
        prompt: Optional[str] = None,
    ) -> str:
        """Generate tests with custom prompt (for E2E testing)"""
        if not self.ai_client:
            # Return mock tests if no AI client available
            return self._generate_mock_tests(file_path, source_code)

        if prompt:
            # Use custom prompt
            test_code = self.ai_client.generate_completion(prompt, self.ai_model)
        else:
            # Use default prompt generation
            analyzer = SourceCodeAnalyzer(file_path)
            analyzer.content = source_code
            elements = analyzer.extract_code_elements()
            prompt = self._create_test_generation_prompt(
                source_code, analyzer.language, elements, 50, file_path, "pytest"
            )
            test_code = self.ai_client.generate_completion(prompt, self.ai_model)

        return self._clean_generated_code(test_code)

    def _generate_mock_tests(self, file_path: str, source_code: str) -> str:
        """Generate mock tests for demonstration purposes"""
        return "# Mock test generated for demonstration\npass\n"

    def generate_tests_for_file(
        self, file_path: str, coverage_percentage: float, test_framework: str = "auto"
    ) -> str:
        """Generate comprehensive unit tests for a source file"""
        print(f"Analyzing source file: {file_path}")

        if not Path(file_path).exists():
            raise Exception(f"Source file does not exist: {file_path}")

        analyzer = SourceCodeAnalyzer(file_path)
        elements = analyzer.extract_code_elements()

        print(
            f"Found {len(elements['functions'])} functions and {len(elements['classes'])} classes"
        )

        # Determine test framework
        if test_framework == "auto":
            test_framework = self._detect_test_framework(analyzer.language)

        # Create prompt for test generation
        prompt = self._create_test_generation_prompt(
            analyzer.content,
            analyzer.language,
            elements,
            coverage_percentage,
            file_path,
            test_framework,
        )

        print("Generating tests using GitHub Models...")
        if not self.ai_client:
            raise Exception("GitHub token required for AI test generation")
        test_code = self.ai_client.generate_completion(prompt, self.ai_model)

        # Clean up the response (remove markdown formatting if present)
        test_code = self._clean_generated_code(test_code)

        return test_code

    def _detect_test_framework(self, language: str) -> str:
        """Detect appropriate test framework for the language"""
        framework_map = {
            "python": "pytest",
            "javascript": "jest",
            "typescript": "jest",
            "java": "junit",
            "csharp": "nunit",
            "go": "testing",
            "rust": "builtin",
            "ruby": "rspec",
            "php": "phpunit",
        }
        return framework_map.get(language, "default")

    def _create_test_generation_prompt(
        self,
        source_code: str,
        language: str,
        elements: Dict[str, List[str]],
        coverage_percentage: float,
        file_path: str,
        test_framework: str,
    ) -> str:
        """Create a detailed prompt for test generation"""

        prompt = f"""Generate comprehensive unit tests for the following {language} source code file: {file_path}

Current test coverage: {coverage_percentage:.1f}%
Test framework: {test_framework}

Requirements:
1. Cover all public functions and methods
2. Include edge cases and error conditions
3. Test different input scenarios
4. Add boundary value testing
5. Test error handling and exceptions
6. Use {test_framework} conventions
7. Include descriptive test names
8. Add setup/teardown if needed
9. Mock external dependencies appropriately

Functions to test: {', '.join(elements['functions']) if elements['functions'] else 'None found'}
Classes to test: {', '.join(elements['classes']) if elements['classes'] else 'None found'}

SOURCE CODE:
```{language}
{source_code}
```

Generate only the test code with proper imports and structure. Do not include explanations or markdown formatting."""

        return prompt

    def _clean_generated_code(self, code: str) -> str:
        """Clean up generated code by removing markdown formatting"""
        # Remove markdown code blocks
        code = re.sub(r"^```\w*\n", "", code, flags=re.MULTILINE)
        code = re.sub(r"\n```$", "", code, flags=re.MULTILINE)
        code = re.sub(r"^```$", "", code, flags=re.MULTILINE)

        return code.strip()

    def determine_test_file_path(self, source_file_path: str) -> str:
        """Determine where the test file should be placed"""
        source_path = Path(source_file_path)

        # Common test directory patterns based on language
        if source_path.suffix == ".py":
            # Python: tests/test_filename.py or test_filename.py
            patterns = [
                Path("tests") / f"test_{source_path.name}",
                source_path.parent / f"test_{source_path.name}",
                source_path.parent / "tests" / f"test_{source_path.name}",
            ]
        elif source_path.suffix in [".js", ".ts", ".jsx", ".tsx"]:
            # JavaScript/TypeScript: __tests__/filename.test.js or filename.test.js
            test_name = f"{source_path.stem}.test{source_path.suffix}"
            patterns = [
                source_path.parent / "__tests__" / test_name,
                source_path.parent / test_name,
                Path("tests") / test_name,
            ]
        elif source_path.suffix == ".java":
            # Java: src/test/java/package/TestClass.java
            patterns = [
                Path("src/test/java") / f"Test{source_path.stem}.java",
                source_path.parent / f"Test{source_path.stem}.java",
            ]
        else:
            # Generic: tests/test_filename.ext
            patterns = [
                Path("tests") / f"test_{source_path.name}",
                source_path.parent / f"test_{source_path.name}",
            ]

        # Use the first pattern and create directory if needed
        chosen_path = patterns[0]
        chosen_path.parent.mkdir(parents=True, exist_ok=True)
        return str(chosen_path)


def main():
    parser = argparse.ArgumentParser(description="Generate unit tests using AI")
    parser.add_argument(
        "--coverage-data", required=True, help="JSON file with coverage data"
    )
    parser.add_argument(
        "--max-files", type=int, default=3, help="Maximum number of files to process"
    )
    parser.add_argument(
        "--test-framework", default="auto", help="Test framework to use"
    )
    parser.add_argument(
        "--ai-model", default="openai/gpt-4.1-mini", help="AI model to use"
    )
    parser.add_argument(
        "--output-dir", default="generated_tests", help="Output directory"
    )
    parser.add_argument("--output-format", default="json", help="Output format")

    args = parser.parse_args()

    # Get GitHub token
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("Error: GITHUB_TOKEN environment variable is required")
        sys.exit(1)

    # Load coverage data
    try:
        with open(args.coverage_data, "r") as f:
            coverage_data = json.load(f)
    except Exception as e:
        print(f"Error loading coverage data: {e}")
        sys.exit(1)

    least_covered_files = coverage_data.get("least_covered_files", [])

    if not least_covered_files:
        print("No files to process")
        # Create empty summary
        summary = {"files_processed": 0, "tests_generated": 0, "generated_files": []}

        output_dir = Path(args.output_dir)
        output_dir.mkdir(exist_ok=True)

        with open(output_dir / "summary.json", "w") as f:
            json.dump(summary, f, indent=2)

        return

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize test generator
    test_generator = TestGenerator(github_token, args.ai_model)

    generated_files = []

    # Process each file
    for i, file_data in enumerate(least_covered_files[: args.max_files]):
        filename = file_data["filename"]
        coverage = file_data["coverage"]

        print(
            f"\nProcessing file {i+1}/{min(len(least_covered_files), args.max_files)}: {filename}"
        )
        print(f"Current coverage: {coverage:.1f}%")

        try:
            # Generate tests
            test_code = test_generator.generate_tests_for_file(
                filename, coverage, args.test_framework
            )

            # Determine test file path
            test_file_path = test_generator.determine_test_file_path(filename)

            # Save test file
            with open(test_file_path, "w", encoding="utf-8") as f:
                f.write(test_code)

            generated_files.append(
                {
                    "source_file": filename,
                    "test_file": test_file_path,
                    "coverage": coverage,
                }
            )

            print(f"Generated test file: {test_file_path}")

        except Exception as e:
            print(f"Error generating tests for {filename}: {e}")
            continue

    # Save summary
    summary = {
        "files_processed": len(generated_files),
        "tests_generated": len(generated_files),
        "generated_files": generated_files,
        "output_directory": str(output_dir),
        "ai_model": args.ai_model,
        "test_framework": args.test_framework,
    }

    with open(output_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nGeneration complete!")
    print(f"Generated tests for {len(generated_files)} files")
    print(f"Summary saved to: {output_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
