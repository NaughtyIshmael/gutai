# Example workflows for using GUTAI

## Basic Usage

```yaml
name: Weekly Coverage Boost
on:
  schedule:
    - cron: "0 9 * * 1" # Every Monday at 9 AM
  workflow_dispatch:

jobs:
  boost-coverage:
    runs-on: ubuntu-latest
    steps:
      - name: Boost Test Coverage
        uses: NaughtyIshmael/gutai@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          max-files: 3
          target-coverage: 80
```

## Using DeepSeek Provider

```yaml
name: Coverage Boost with DeepSeek
on:
  schedule:
    - cron: "0 10 * * 1" # Every Monday at 10 AM
  workflow_dispatch:

permissions:
  contents: write
  pull-requests: write

jobs:
  boost-coverage-deepseek:
    runs-on: ubuntu-latest
    steps:
      - name: Boost Test Coverage with DeepSeek
        uses: NaughtyIshmael/gutai@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          deepseek-token: ${{ secrets.DEEPSEEK_TOKEN }}
          ai-provider: "deepseek"
          max-files: 3
          target-coverage: 80
          branch: "coverage-boost-deepseek"
```

## Multi-Provider Comparison

```yaml
name: AI Provider Comparison
on:
  workflow_dispatch:

permissions:
  contents: write
  pull-requests: write
  models: read

jobs:
  test-github-models:
    runs-on: ubuntu-latest
    name: "GitHub Models"
    steps:
      - name: Generate Tests with GitHub Models
        uses: NaughtyIshmael/gutai@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          ai-provider: "github"
          max-files: 2
          target-coverage: 75
          branch: "coverage-boost-github"
          pr-title: "🤖 AI Tests (GitHub Models)"

  test-deepseek:
    runs-on: ubuntu-latest
    name: "DeepSeek"
    steps:
      - name: Generate Tests with DeepSeek
        uses: NaughtyIshmael/gutai@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          deepseek-token: ${{ secrets.DEEPSEEK_TOKEN }}
          ai-provider: "deepseek"
          max-files: 2
          target-coverage: 75
          branch: "coverage-boost-deepseek"
          pr-title: "🤖 AI Tests (DeepSeek)"
```

## Advanced Configuration

```yaml
name: Advanced Coverage Improvement
on:
  workflow_dispatch:
    inputs:
      max_files:
        description: "Number of files to process"
        required: false
        default: "3"
      target_coverage:
        description: "Target coverage threshold"
        required: false
        default: "80"

jobs:
  coverage-boost:
    runs-on: ubuntu-latest
    steps:
      - name: Boost Coverage with Custom Settings
        uses: NaughtyIshmael/gutai@v1
        with:
          codecov-token: ${{ secrets.CODECOV_TOKEN }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
          max-files: ${{ github.event.inputs.max_files }}
          target-coverage: ${{ github.event.inputs.target_coverage }}
          languages: "python,javascript,typescript"
          exclude-patterns: "migrations/*,vendor/*,node_modules/*"
          test-framework: "pytest"
          pr-title: "Improve test coverage for core modules"
```

## Integration with Existing CI/CD

```yaml
name: CI/CD with Coverage Boost
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: npm test
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  boost-coverage:
    needs: test
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Boost Test Coverage
        uses: NaughtyIshmael/gutai@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          max-files: 2
          create-pr: true
```

## Python Project Example

```yaml
name: Python Coverage Boost
on:
  schedule:
    - cron: "0 2 * * 0" # Weekly

jobs:
  boost-python-coverage:
    runs-on: ubuntu-latest
    steps:
      - name: Boost Python Test Coverage
        uses: NaughtyIshmael/gutai@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          languages: "python"
          test-framework: "pytest"
          exclude-patterns: "migrations/*,settings/*,venv/*"
          max-files: 5
          target-coverage: 85
```

## JavaScript/TypeScript Project Example

```yaml
name: JavaScript Coverage Boost
on:
  workflow_dispatch:

jobs:
  boost-js-coverage:
    runs-on: ubuntu-latest
    steps:
      - name: Boost JavaScript Test Coverage
        uses: NaughtyIshmael/gutai@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          languages: "javascript,typescript"
          test-framework: "jest"
          exclude-patterns: "dist/*,build/*,node_modules/*"
          max-files: 4
```
