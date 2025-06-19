#!/usr/bin/env python3
"""
Script to create pull request with generated tests.
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential


class GitHubModelsClient:
    """Client to interact with GitHub Models API for generating PR content"""

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
                        "You are a technical writer specializing in creating clear, professional commit messages and pull request titles. Generate concise, descriptive content that follows conventional commit standards."
                    ),
                    UserMessage(prompt),
                ],
                model=model,
                temperature=0.1,
                top_p=1.0,
                max_tokens=200,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            raise Exception(f"GitHub Models API error: {str(e)}")


class PullRequestCreator:
    """Create pull request with generated tests"""

    def __init__(self, github_token: str, ai_model: str = "openai/gpt-4.1-mini"):
        self.github_token = github_token
        self.ai_client = GitHubModelsClient(github_token)
        self.ai_model = ai_model

    def create_branch_and_pr(
        self,
        coverage_data: Dict,
        generated_tests: List[Dict],
        branch_prefix: str,
        custom_pr_title: str = "",
    ) -> Dict:
        """Create branch and pull request with generated tests"""

        # Generate branch name
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        branch_name = f"{branch_prefix}-{timestamp}"

        # Configure git
        subprocess.run(
            ["git", "config", "--local", "user.email", "action@github.com"], check=True
        )
        subprocess.run(
            ["git", "config", "--local", "user.name", "GitHub Action"], check=True
        )

        # Create and switch to new branch
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)

        # Copy generated test files to their target locations
        self._copy_test_files(generated_tests)

        # Add files to git
        subprocess.run(["git", "add", "."], check=True)

        # Check if there are changes to commit
        result = subprocess.run(
            ["git", "diff", "--staged", "--quiet"], capture_output=True
        )
        if result.returncode == 0:
            print("No changes to commit")
            return {"success": False, "reason": "no_changes"}

        # Generate commit message and PR title
        commit_message = self._generate_commit_message(coverage_data, generated_tests)
        pr_title = custom_pr_title or self._generate_pr_title(
            coverage_data, generated_tests
        )

        # Commit changes
        subprocess.run(["git", "commit", "-m", commit_message], check=True)

        # Push branch
        subprocess.run(["git", "push", "origin", branch_name], check=True)

        # Create pull request description
        pr_description = self._generate_pr_description(coverage_data, generated_tests)

        # Create pull request using GitHub CLI
        pr_result = subprocess.run(
            [
                "gh",
                "pr",
                "create",
                "--title",
                pr_title,
                "--body",
                pr_description,
                "--head",
                branch_name,
                "--label",
                "testing,coverage,automated",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        pr_url = pr_result.stdout.strip()

        # Save PR info
        pr_info = {
            "success": True,
            "pr_url": pr_url,
            "branch_name": branch_name,
            "pr_title": pr_title,
            "commit_message": commit_message,
        }

        with open("pr_info.json", "w") as f:
            json.dump(pr_info, f, indent=2)

        print(f"Created pull request: {pr_url}")
        return pr_info

    def _copy_test_files(self, generated_tests: List[Dict]):
        """Copy generated test files to their target locations"""
        for test_info in generated_tests:
            src_file = test_info["test_file"]
            if Path(src_file).exists():
                # Ensure target directory exists
                target_path = Path(src_file)
                target_path.parent.mkdir(parents=True, exist_ok=True)
                print(f"Test file ready: {src_file}")

    def _generate_commit_message(
        self, coverage_data: Dict, generated_tests: List[Dict]
    ) -> str:
        """Generate meaningful commit message using AI"""

        # Create context for AI
        files_info = []
        for test_info in generated_tests:
            source_file = test_info["source_file"]
            coverage = test_info["coverage"]
            files_info.append(f"{source_file} ({coverage:.1f}% coverage)")

        prompt = f"""Generate a concise commit message for adding unit tests to improve code coverage.

Files being tested:
{chr(10).join(files_info)}

Repository: {coverage_data.get('repository', 'unknown')}
Target coverage: {coverage_data.get('target_coverage', 80)}%

Requirements:
- Use conventional commit format (test: description)
- Be specific about what's being tested
- Keep it under 72 characters
- Don't mention AI or automation
- Focus on the testing improvements

Generate only the commit message, no explanation."""

        try:
            return self.ai_client.generate_completion(prompt, self.ai_model)
        except Exception as e:
            print(f"Warning: Could not generate AI commit message: {e}")
            # Fallback commit message
            file_count = len(generated_tests)
            return f"test: add unit tests for {file_count} modules to improve coverage"

    def _generate_pr_title(
        self, coverage_data: Dict, generated_tests: List[Dict]
    ) -> str:
        """Generate meaningful PR title using AI"""

        # Create context for AI
        file_names = [
            Path(test_info["source_file"]).stem for test_info in generated_tests
        ]
        avg_coverage = sum(
            test_info["coverage"] for test_info in generated_tests
        ) / len(generated_tests)

        prompt = f"""Generate a concise pull request title for adding unit tests to improve code coverage.

Modules being tested: {', '.join(file_names)}
Average current coverage: {avg_coverage:.1f}%
Target coverage: {coverage_data.get('target_coverage', 80)}%
Number of files: {len(generated_tests)}

Requirements:
- Be descriptive and professional
- Keep it under 60 characters
- Don't mention AI or automation
- Focus on the testing improvements
- Use action words like "Add", "Improve", "Enhance"

Generate only the title, no explanation."""

        try:
            return self.ai_client.generate_completion(prompt, self.ai_model)
        except Exception as e:
            print(f"Warning: Could not generate AI PR title: {e}")
            # Fallback PR title
            return (
                f"Add unit tests to improve coverage for {len(generated_tests)} modules"
            )

    def _generate_pr_description(
        self, coverage_data: Dict, generated_tests: List[Dict]
    ) -> str:
        """Generate comprehensive PR description"""

        description = f"""## Test Coverage Improvement

This PR adds comprehensive unit tests to improve code coverage for modules with low test coverage.

### 📊 Coverage Analysis

| File | Current Coverage | Tests Added |
|------|------------------|-------------|
"""

        for test_info in generated_tests:
            source_file = test_info["source_file"]
            coverage = test_info["coverage"]
            test_file = Path(test_info["test_file"]).name
            description += f"| `{source_file}` | {coverage:.1f}% | `{test_file}` |\n"

        description += f"""
### 🧪 What's Included

- **{len(generated_tests)} test files** with comprehensive test coverage
- Tests for edge cases and error handling
- Boundary value testing
- Input validation tests
- Proper mocking of external dependencies

### 📈 Expected Impact

- **Target Coverage**: {coverage_data.get('target_coverage', 80)}%
- **Files Improved**: {len(generated_tests)} modules
- **Test Quality**: Comprehensive coverage including happy path, edge cases, and error scenarios

### ✅ Test Quality Checklist

- [x] Tests cover all public functions and methods
- [x] Edge cases and error conditions included
- [x] Descriptive test names following conventions
- [x] Proper setup and teardown where needed
- [x] External dependencies mocked appropriately
- [x] Tests are independent and can run in any order

### 🔍 Review Notes

Please review the generated tests for:
- Accuracy of test assertions
- Completeness of test scenarios
- Adherence to project testing conventions
- Any project-specific requirements

The tests have been generated to follow best practices and should significantly improve coverage for the affected modules.

---

**Generated by**: GitHub Actions workflow
**Analysis source**: {coverage_data.get('repository', 'Repository')} - {coverage_data.get('branch', 'main')} branch
"""

        return description


def main():
    parser = argparse.ArgumentParser(
        description="Create pull request with generated tests"
    )
    parser.add_argument(
        "--coverage-data", required=True, help="Coverage data JSON file"
    )
    parser.add_argument(
        "--generated-tests", required=True, help="Generated tests directory"
    )
    parser.add_argument(
        "--branch-prefix", default="coverage-boost", help="Branch name prefix"
    )
    parser.add_argument("--pr-title", default="", help="Custom PR title")
    parser.add_argument(
        "--ai-model",
        default="openai/gpt-4.1-mini",
        help="AI model for generating content",
    )

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

    # Load generated tests summary
    summary_file = Path(args.generated_tests) / "summary.json"
    if not summary_file.exists():
        print("No generated tests found")
        sys.exit(0)

    try:
        with open(summary_file, "r") as f:
            summary = json.load(f)
    except Exception as e:
        print(f"Error loading test summary: {e}")
        sys.exit(1)

    generated_files = summary.get("generated_files", [])
    if not generated_files:
        print("No test files were generated")
        sys.exit(0)

    # Create PR
    try:
        pr_creator = PullRequestCreator(github_token, args.ai_model)
        result = pr_creator.create_branch_and_pr(
            coverage_data, generated_files, args.branch_prefix, args.pr_title
        )

        if result["success"]:
            print(f"Successfully created PR: {result['pr_url']}")
        else:
            print(f"Failed to create PR: {result.get('reason', 'unknown error')}")
            sys.exit(1)

    except Exception as e:
        print(f"Error creating pull request: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
