# AI Provider Integration Guide

GUTAI now supports multiple AI providers for generating unit tests. This guide explains how to configure and use different AI providers.

## Supported Providers

### 1. GitHub Models (Default)

- **Provider ID**: `github`
- **Environment Variable**: `GITHUB_TOKEN`
- **Models**: Uses GitHub's AI models for code generation
- **Setup**: Set your GitHub token in the `GITHUB_TOKEN` environment variable

### 2. DeepSeek

- **Provider ID**: `deepseek`
- **Environment Variable**: `DEEPSEEK_TOKEN`
- **Models**: Uses DeepSeek's AI models (OpenAI-compatible API)
- **Setup**: Set your DeepSeek API token in the `DEEPSEEK_TOKEN` environment variable

## Configuration

### Setting up Environment Variables

#### For GitHub Models:

```bash
export GITHUB_TOKEN="your_github_token_here"
```

#### For DeepSeek:

```bash
export DEEPSEEK_TOKEN="your_deepseek_api_token_here"
```

### Getting API Tokens

#### GitHub Token:

1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Generate a new token with appropriate permissions
3. Copy the token and set it as `GITHUB_TOKEN`

#### DeepSeek Token:

1. Visit [DeepSeek Platform](https://platform.deepseek.com/)
2. Create an account and navigate to API settings
3. Generate an API key
4. Copy the token and set it as `DEEPSEEK_TOKEN`

## Usage

### Command Line Interface

#### Using the test generation script directly:

```bash
# Use GitHub Models (default)
python scripts/generate_tests.py --provider github

# Use DeepSeek
python scripts/generate_tests.py --provider deepseek
```

#### Running E2E tests:

##### Python E2E tests:

```bash
# Use GitHub Models (default)
python test_python_e2e.py --provider github

# Use DeepSeek
python test_python_e2e.py --provider deepseek
```

##### Go E2E tests:

```bash
# Use GitHub Models (default)
python test_golang_e2e.py --provider github

# Use DeepSeek
python test_golang_e2e.py --provider deepseek
```

#### Using the shell script:

```bash
# Run Python E2E tests with GitHub Models (default)
./run_e2e_test.sh python

# Run Python E2E tests with DeepSeek
./run_e2e_test.sh python deepseek

# Run Go E2E tests with GitHub Models (default)
./run_e2e_test.sh golang

# Run Go E2E tests with DeepSeek
./run_e2e_test.sh golang deepseek
```

### In GitHub Actions

You can configure different providers in your GitHub Actions workflow:

```yaml
# .github/workflows/test.yml
name: GUTAI Tests

on: [push, pull_request]

jobs:
  test-github-provider:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run GUTAI with GitHub Models
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          ./run_e2e_test.sh python github

  test-deepseek-provider:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run GUTAI with DeepSeek
        env:
          DEEPSEEK_TOKEN: ${{ secrets.DEEPSEEK_TOKEN }}
        run: |
          ./run_e2e_test.sh python deepseek
```

## API Differences

### GitHub Models

- Uses GitHub's native AI model endpoints
- Authentication via GitHub token
- Model selection handled automatically

### DeepSeek

- Uses OpenAI-compatible API endpoints
- Authentication via API key
- Supports advanced language models optimized for code generation

## Error Handling

If an AI provider fails to generate tests, GUTAI will:

1. Log the error message
2. Fall back to a basic test template
3. Continue with the workflow

Common issues and solutions:

### Authentication Errors

- **GitHub**: Ensure your `GITHUB_TOKEN` has the necessary permissions
- **DeepSeek**: Verify your `DEEPSEEK_TOKEN` is valid and has API access

### Rate Limiting

- **GitHub**: Check your API rate limits in GitHub settings
- **DeepSeek**: Monitor your API usage on the DeepSeek platform

### Network Issues

- Ensure your environment has internet access
- Check if your firewall allows outbound HTTPS connections

## Best Practices

1. **Token Security**: Never commit API tokens to your repository. Use environment variables or secure secret management.

2. **Provider Selection**: Choose providers based on:

   - Model quality for your specific use case
   - API rate limits and pricing
   - Integration requirements

3. **Fallback Strategy**: Always test with fallback scenarios when AI generation fails.

4. **Monitoring**: Monitor your API usage and costs across different providers.

## Troubleshooting

### Debug Mode

Enable verbose logging by setting the environment variable:

```bash
export GUTAI_DEBUG=1
```

### Testing Connectivity

Test your provider configuration:

```bash
# Test GitHub provider
python -c "from scripts.generate_tests import TestGenerator; print('GitHub OK' if TestGenerator.test_github_connection() else 'GitHub Failed')"

# Test DeepSeek provider
python -c "from scripts.generate_tests import TestGenerator; print('DeepSeek OK' if TestGenerator.test_deepseek_connection() else 'DeepSeek Failed')"
```

## Contributing

When adding new AI providers:

1. Implement the provider client in `scripts/generate_tests.py`
2. Add provider selection logic in `TestGenerator`
3. Update all E2E test runners to support the new provider
4. Add documentation and examples
5. Update the shell scripts and GitHub Actions examples

For more information, see [CONTRIBUTING.md](CONTRIBUTING.md).
