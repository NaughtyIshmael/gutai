# Contributing to GUTAI

We welcome contributions! This document outlines how to contribute to the project.

## 🚀 Quick Start

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Test your changes
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 🛠️ Development Setup

### Prerequisites

- Python 3.11+
- Git
- GitHub CLI (for testing PR creation)

### Setup

```bash
git clone https://github.com/your-org/gutai
cd gutai
pip install -r requirements.txt
```

### Testing

```bash
# Test script compilation
python -m py_compile scripts/*.py

# Test with example data
python scripts/get_coverage_data.py --org octocat --repo Hello-World --limit 1

# Validate action.yml
gh action validate action.yml
```

## 📝 Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Include type hints where appropriate

## 🧪 Testing

- Test your changes with different programming languages
- Verify the action works with both public and private repositories
- Test error handling scenarios
- Ensure generated tests are syntactically correct

## 📋 Pull Request Guidelines

- Use descriptive PR titles
- Include a detailed description of changes
- Reference any related issues
- Update documentation if needed
- Ensure all tests pass

## 🐛 Bug Reports

Please include:

- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Relevant logs or error messages

## 💡 Feature Requests

Please include:

- Clear description of the feature
- Use case and motivation
- Proposed implementation approach
- Any potential drawbacks

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 📞 Support

- 📖 [Documentation](https://github.com/your-org/gutai/wiki)
- 🐛 [Issues](https://github.com/your-org/gutai/issues)
- 💬 [Discussions](https://github.com/your-org/gutai/discussions)
