#!/usr/bin/env python3
"""
Script to fetch coverage data from Codecov API and identify files with low coverage.
"""

import os
import sys
import json
import requests  # Still needed for Codecov API
import argparse
import fnmatch
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class CodecovClient:
    """Client to interact with Codecov API"""

    def __init__(
        self, github_org: str, github_repo: str, codecov_token: Optional[str] = None
    ):
        self.github_org = github_org
        self.github_repo = github_repo
        self.codecov_token = codecov_token
        self.base_url = "https://api.codecov.io"

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make authenticated request to Codecov API"""
        headers = {}
        if self.codecov_token:
            headers["Authorization"] = f"Bearer {self.codecov_token}"

        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, headers=headers, params=params or {})

        if response.status_code != 200:
            print(
                f"Warning: Could not fetch coverage data from Codecov: {response.status_code}"
            )
            print(f"This might be normal for repositories without coverage reports")
            return {}

        return response.json()

    def get_file_coverage(self, branch: str = "main") -> List[Dict]:
        """Get coverage data for individual files"""
        endpoint = f"/repos/{self.github_org}/{self.github_repo}/file"
        params = {"branch": branch}
        data = self._make_request(endpoint, params)

        if "files" in data:
            return data["files"]
        return []


def detect_project_languages() -> List[str]:
    """Auto-detect programming languages in the project"""
    language_extensions = {
        "python": [".py"],
        "javascript": [".js", ".jsx"],
        "typescript": [".ts", ".tsx"],
        "java": [".java"],
        "csharp": [".cs"],
        "cpp": [".cpp", ".cc", ".cxx", ".c++"],
        "c": [".c"],
        "go": [".go"],
        "rust": [".rs"],
        "ruby": [".rb"],
        "php": [".php"],
    }

    detected_languages = set()

    # Scan current directory for source files
    for root, dirs, files in os.walk("."):
        # Skip common directories
        dirs[:] = [
            d
            for d in dirs
            if d
            not in {
                ".git",
                "node_modules",
                "vendor",
                "__pycache__",
                ".venv",
                "venv",
                "dist",
                "build",
            }
        ]

        for file in files:
            file_path = Path(root) / file
            extension = file_path.suffix.lower()

            for lang, exts in language_extensions.items():
                if extension in exts:
                    detected_languages.add(lang)

    return list(detected_languages)


def filter_source_files(
    files: List[Dict], languages: List[str], exclude_patterns: List[str]
) -> List[Dict]:
    """Filter files to only include relevant source code files"""
    if not languages:
        languages = detect_project_languages()

    # Language to extension mapping
    language_extensions = {
        "python": [".py"],
        "javascript": [".js", ".jsx"],
        "typescript": [".ts", ".tsx"],
        "java": [".java"],
        "csharp": [".cs"],
        "cpp": [".cpp", ".cc", ".cxx", ".c++"],
        "c": [".c"],
        "go": [".go"],
        "rust": [".rs"],
        "ruby": [".rb"],
        "php": [".php"],
    }

    # Get all extensions for selected languages
    valid_extensions = []
    for lang in languages:
        valid_extensions.extend(language_extensions.get(lang, []))

    source_files = []
    for file_data in files:
        filename = file_data.get("name", "")

        # Check if file should be excluded
        excluded = False
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(filename.lower(), pattern.lower()):
                excluded = True
                break

        if excluded:
            continue

        # Only include files with valid extensions
        if any(filename.endswith(ext) for ext in valid_extensions):
            source_files.append(file_data)

    return source_files


def calculate_coverage_percentage(file_data: Dict) -> float:
    """Calculate coverage percentage from file data"""
    totals = file_data.get("totals", {})

    if "coverage" in totals and totals["coverage"] is not None:
        return float(totals["coverage"])

    lines = totals.get("lines", 0)
    hits = totals.get("hits", 0)

    if lines > 0:
        return (hits / lines) * 100

    return 0.0


def identify_least_covered_files(
    files: List[Dict], target_coverage: float, limit: int
) -> List[Tuple[str, float]]:
    """Identify files with coverage below target threshold"""
    file_coverage = []

    for file_data in files:
        filename = file_data.get("name", "")
        coverage = calculate_coverage_percentage(file_data)

        # Only include files below target coverage
        if coverage < target_coverage:
            file_coverage.append((filename, coverage))

    # Sort by coverage percentage (ascending)
    file_coverage.sort(key=lambda x: x[1])

    return file_coverage[:limit]


def scan_local_files(
    languages: List[str],
    exclude_patterns: List[str],
    target_coverage: float,
) -> List[Tuple[str, float]]:
    """Fallback: return all source files when no coverage data is available"""
    if not languages:
        languages = detect_project_languages()

    language_extensions = {
        "python": [".py"],
        "javascript": [".js", ".jsx"],
        "typescript": [".ts", ".tsx"],
        "java": [".java"],
        "csharp": [".cs"],
        "cpp": [".cpp", ".cc", ".cxx", ".c++"],
        "c": [".c"],
        "go": [".go"],
        "rust": [".rs"],
        "ruby": [".rb"],
        "php": [".php"],
    }

    valid_extensions = []
    for lang in languages:
        valid_extensions.extend(language_extensions.get(lang, []))

    source_files = []

    for root, dirs, files in os.walk("."):
        # Skip common directories
        dirs[:] = [
            d
            for d in dirs
            if d
            not in {
                ".git",
                "node_modules",
                "vendor",
                "__pycache__",
                ".venv",
                "venv",
                "dist",
                "build",
            }
        ]

        for file in files:
            file_path = Path(root) / file
            relative_path = str(file_path.relative_to("."))

            # Check if file should be excluded
            excluded = False
            for pattern in exclude_patterns:
                if fnmatch.fnmatch(relative_path.lower(), pattern.lower()):
                    excluded = True
                    break

            if excluded:
                continue

            # Only include files with valid extensions
            if any(file.endswith(ext) for ext in valid_extensions):
                # Assume 0% coverage for files without coverage data
                source_files.append((relative_path, 0.0))

    # Sort by filename for consistency
    source_files.sort()

    return source_files[]


def main():
    parser = argparse.ArgumentParser(
        description="Get coverage data and identify least covered files"
    )
    parser.add_argument("--org", required=True, help="GitHub organization name")
    parser.add_argument("--repo", required=True, help="GitHub repository name")
    parser.add_argument("--branch", default="main", help="Branch name")
    parser.add_argument(
        "--limit", type=int, default=5, help="Maximum number of files to identify"
    )
    parser.add_argument(
        "--target-coverage", type=float, default=80.0, help="Target coverage threshold"
    )
    parser.add_argument(
        "--exclude-patterns", default="", help="Comma-separated exclude patterns"
    )
    parser.add_argument(
        "--languages", default="", help="Comma-separated list of languages"
    )
    parser.add_argument("--output", help="Output file for results")

    args = parser.parse_args()

    # Parse inputs
    exclude_patterns = [
        p.strip() for p in args.exclude_patterns.split(",") if p.strip()
    ]
    languages = [l.strip() for l in args.languages.split(",") if l.strip()]

    # Get tokens from environment
    codecov_token = os.getenv("CODECOV_TOKEN")

    print(f"Analyzing coverage for {args.org}/{args.repo} (branch: {args.branch})")
    print(f"Target coverage: {args.target_coverage}%")
    print(f"Languages: {languages if languages else 'auto-detect'}")

    try:
        # Try to get coverage data from Codecov
        client = CodecovClient(args.org, args.repo, codecov_token)
        files = client.get_file_coverage(branch=args.branch)

        if files:
            print(f"Found {len(files)} files with coverage data from Codecov")
            source_files = filter_source_files(files, languages, exclude_patterns)
            print(f"Filtered to {len(source_files)} relevant source files")
            least_covered = identify_least_covered_files(
                source_files, args.target_coverage, args.limit
            )
        else:
            print("No coverage data available from Codecov, scanning local files...")
            least_covered = scan_local_files(
                languages, exclude_patterns, args.target_coverage
            )

        if least_covered:
            print(
                f"\nFiles with coverage below {args.target_coverage}% (showing top {len(least_covered)}):"
            )
            for filename, coverage in least_covered:
                print(f"  {filename}: {coverage:.1f}% coverage")
        else:
            print(f"\nNo files found with coverage below {args.target_coverage}%")

        # Prepare output data
        output_data = {
            "repository": f"{args.org}/{args.repo}",
            "branch": args.branch,
            "target_coverage": args.target_coverage,
            "languages": languages if languages else detect_project_languages(),
            "exclude_patterns": exclude_patterns,
            "total_files_analyzed": len(files) if files else "unknown",
            "least_covered_files": [
                {"filename": filename, "coverage": coverage}
                for filename, coverage in least_covered
            ],
            "has_coverage_data": bool(files),
        }

        # Save output
        output_file = args.output or "coverage_data.json"
        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2)

        print(f"\nResults saved to {output_file}")

    except Exception as e:
        print(f"Error: {e}")
        # Create empty output file on error
        output_data = {
            "repository": f"{args.org}/{args.repo}",
            "branch": args.branch,
            "target_coverage": args.target_coverage,
            "languages": languages,
            "exclude_patterns": exclude_patterns,
            "total_files_analyzed": 0,
            "least_covered_files": [],
            "has_coverage_data": False,
            "error": str(e),
        }

        output_file = args.output or "coverage_data.json"
        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2)

        sys.exit(1)


if __name__ == "__main__":
    main()
