# GUTAI End-to-End Testing Guide

This guide explains how to run the comprehensive E2E test that validates the complete GUTAI workflow.

## Overview

The E2E test (`test_e2e.py`) performs a complete simulation of the GUTAI workflow:

1. **Setup Environment** - Installs required dependencies (pytest, coverage, pytest-cov)
2. **Run Initial Coverage** - Executes pytest with coverage on sample code
3. **Identify Least Covered File** - Analyzes coverage data to find files needing improvement
4. **Generate Tests with AI** - Uses GitHub Models (or mock generation) to create new tests
5. **Apply Generated Tests** - Adds the new tests to the existing test suite
6. **Run Final Tests** - Validates that new tests pass and coverage improved
7. **Report Results** - Shows coverage improvement and test success metrics

## Sample Application

The E2E test includes a sample calculator application with:

- **Source Code**: `sample_app/calculator.py` - A feature-rich calculator with math operations
- **Initial Tests**: `tests/test_calculator.py` - Basic tests covering ~56% of the code
- **Generated Tests**: Additional tests created by AI to achieve 100% coverage

## Running the E2E Test

### Option 1: Direct Execution

```bash
python3 test_e2e.py
```

### Option 2: Using the Shell Script

```bash
./run_e2e_test.sh
```

### Option 3: With GitHub Models Integration

Set your GitHub token to test real AI generation:

```bash
export GITHUB_TOKEN="your_github_token_here"
python3 test_e2e.py
```

## Expected Results

A successful E2E test will show:

```
🚀 Starting GUTAI E2E Test Workflow
==================================================
🔧 Setting up E2E test environment...
✅ Environment setup complete
📊 Running initial test suite with coverage...
📈 Initial coverage: 55.7%
🔍 Identifying least covered file...
📉 Least covered file: sample_app/calculator.py (55.7% coverage)
🤖 Generating additional tests using GitHub Models...
✅ Tests generated successfully
📝 Applying generated tests to test file...
✅ Generated tests added to tests/test_calculator.py
🧪 Running tests with newly generated test cases...
📈 Final coverage: 100.0%

==================================================
📊 E2E Test Results Summary
==================================================
Target file: sample_app/calculator.py
Initial coverage: 55.7%
Final coverage: 100.0%
Coverage improvement: +44.3%
All tests passed: ✅ Yes

🎉 E2E Test PASSED! GUTAI workflow completed successfully.
```

## Test Components

### 1. Calculator Module (`sample_app/calculator.py`)

Features tested:

- Basic arithmetic operations (add, subtract, multiply, divide)
- Advanced operations (power, square root, factorial)
- Utility functions (fibonacci, prime checking, GCD)
- Statistics calculations (mean, median, mode)
- Error handling and edge cases

### 2. Generated Test Cases

The AI generates comprehensive tests including:

- Edge case testing (zero, negative numbers, large values)
- Error condition validation (division by zero, negative square root)
- Boundary condition testing
- Input validation
- State management testing (calculator history)

### 3. Coverage Analysis

The test measures:

- Line coverage percentage
- Coverage improvement delta
- Test execution success rate
- Generated test quality

## Mock vs Real AI Generation

### With GitHub Token

- Uses real GitHub Models API
- Generates contextual, intelligent test cases
- Provides actual AI-powered test improvement

### Without GitHub Token (Mock Mode)

- Uses predefined mock tests
- Still demonstrates the complete workflow
- Shows infrastructure working correctly

## Cleanup

The E2E test automatically cleans up:

- Coverage report files (`coverage.json`, `coverage_final.json`)
- Python cache directories (`__pycache__`)
- Temporary test artifacts

## Integration with CI/CD

Add to your workflow:

```yaml
- name: Run GUTAI E2E Test
  run: |
    python3 test_e2e.py
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Customization

You can modify the E2E test for your own projects by:

1. **Replacing Sample App**: Update `sample_app/` with your code
2. **Updating Test Patterns**: Modify test file detection logic
3. **Adjusting Coverage Thresholds**: Change success criteria
4. **Adding Test Frameworks**: Support additional testing tools

## Troubleshooting

### Common Issues

1. **Missing Dependencies**: Ensure pytest, coverage, and pytest-cov are installed
2. **Python Path Issues**: Make sure the project root is in PYTHONPATH
3. **File Permissions**: Ensure scripts have proper execution permissions
4. **GitHub Token**: For real AI testing, verify your token has proper scopes

### Debug Mode

Enable verbose output:

```bash
export DEBUG=1
python3 test_e2e.py
```

## Success Criteria

The E2E test passes when:

- ✅ All generated tests execute successfully
- ✅ Coverage does not decrease
- ✅ No syntax errors in generated code
- ✅ Complete workflow executes without errors

This E2E test validates that GUTAI can successfully identify low-coverage files, generate meaningful tests, and improve overall code coverage automatically!
