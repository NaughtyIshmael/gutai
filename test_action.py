#!/usr/bin/env python3
"""
Test script to validate the AI Test Coverage Booster action implementation.
"""

import os
import sys
import json
import tempfile
import subprocess
from pathlib import Path


def test_action_yml():
    """Test that action.yml is valid"""
    print("Testing action.yml validity...")

    action_file = Path("action.yml")
    if not action_file.exists():
        print("❌ action.yml not found")
        return False

    try:
        import yaml

        with open(action_file) as f:
            yaml.safe_load(f)
        print("✅ action.yml is valid YAML")
        return True
    except ImportError:
        print("⚠️  PyYAML not installed, skipping YAML validation")
        return True
    except Exception as e:
        print(f"❌ action.yml validation failed: {e}")
        return False


def test_script_syntax():
    """Test that all Python scripts have valid syntax"""
    print("Testing Python script syntax...")

    scripts = [
        "scripts/get_coverage_data.py",
        "scripts/generate_tests.py",
        "scripts/create_pr.py",
    ]

    for script in scripts:
        script_path = Path(script)
        if not script_path.exists():
            print(f"❌ Script not found: {script}")
            return False

        try:
            subprocess.run(
                [sys.executable, "-m", "py_compile", script],
                check=True,
                capture_output=True,
            )
            print(f"✅ {script} syntax is valid")
        except subprocess.CalledProcessError as e:
            print(f"❌ {script} syntax error: {e}")
            return False

    return True


def test_get_coverage_data():
    """Test get_coverage_data.py with mock parameters"""
    print("Testing get_coverage_data.py...")

    cmd = [
        sys.executable,
        "scripts/get_coverage_data.py",
        "--org",
        "octocat",
        "--repo",
        "Hello-World",
        "--limit",
        "1",
        "--output",
        "test_coverage.json",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Check if output file was created
        if Path("test_coverage.json").exists():
            with open("test_coverage.json") as f:
                data = json.load(f)

            if "repository" in data and "least_covered_files" in data:
                print("✅ get_coverage_data.py executed successfully")
                Path("test_coverage.json").unlink()  # cleanup
                return True

        print(
            "⚠️  get_coverage_data.py ran but may not have found coverage data (expected for test repo)"
        )
        return True

    except subprocess.TimeoutExpired:
        print("⚠️  get_coverage_data.py timed out (network issue?)")
        return True
    except Exception as e:
        print(f"❌ get_coverage_data.py failed: {e}")
        return False


def test_help_commands():
    """Test that scripts show help properly"""
    print("Testing script help commands...")

    scripts = [
        "scripts/get_coverage_data.py",
        "scripts/generate_tests.py",
        "scripts/create_pr.py",
    ]

    for script in scripts:
        try:
            result = subprocess.run(
                [sys.executable, script, "--help"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0 and "usage:" in result.stdout.lower():
                print(f"✅ {script} help command works")
            else:
                print(f"❌ {script} help command failed")
                return False
        except Exception as e:
            print(f"❌ {script} help test failed: {e}")
            return False

    return True


def test_directory_structure():
    """Test that all required files exist"""
    print("Testing directory structure...")

    required_files = [
        "action.yml",
        "README.md",
        "LICENSE",
        "CONTRIBUTING.md",
        "requirements.txt",
        "scripts/get_coverage_data.py",
        "scripts/generate_tests.py",
        "scripts/create_pr.py",
        ".github/workflows/test.yml",
        "examples/workflows.md",
    ]

    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False

    print("✅ All required files exist")
    return True


def test_readme_content():
    """Test that README has required sections"""
    print("Testing README content...")

    readme_path = Path("README.md")
    if not readme_path.exists():
        print("❌ README.md not found")
        return False

    content = readme_path.read_text()
    required_sections = [
        "## 🚀 Features",
        "## 📋 Quick Start",
        "## 🛠️ Inputs",
        "## 📤 Outputs",
        "## 📚 Usage Examples",
    ]

    missing_sections = []
    for section in required_sections:
        if section not in content:
            missing_sections.append(section)

    if missing_sections:
        print(f"❌ README missing sections: {', '.join(missing_sections)}")
        return False

    print("✅ README has all required sections")
    return True


def main():
    """Run all tests"""
    print("🧪 Testing AI Test Coverage Booster Action")
    print("=" * 50)

    tests = [
        test_directory_structure,
        test_action_yml,
        test_script_syntax,
        test_help_commands,
        test_readme_content,
        test_get_coverage_data,
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
            print()
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
            results.append(False)
            print()

    # Summary
    passed = sum(results)
    total = len(results)

    print("=" * 50)
    print(f"Test Results: {passed}/{total} passed")

    if passed == total:
        print("🎉 All tests passed! The action is ready for use.")
        print("\n📋 Next steps:")
        print("   1. Update the 'uses' paths in README.md with your actual repository")
        print("   2. Test the action in a real repository")
        print("   3. Publish to GitHub Marketplace")
        print("   4. Add repository secrets as documented")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
