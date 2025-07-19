# Contributing to AetherLab Community

First off, thank you for considering contributing to AetherLab Community! It's people like you that make AetherLab such a great tool for the AI community.

## Code of Conduct

By participating in this project, you are expected to uphold our Code of Conduct:

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples to demonstrate the steps**
- **Describe the behavior you observed and what behavior you expected**
- **Include screenshots if applicable**
- **Include your environment details** (OS, Python/Node version, etc.)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- **Use a clear and descriptive title**
- **Provide a detailed description of the proposed enhancement**
- **Provide specific examples to demonstrate the enhancement**
- **Describe the current behavior and the expected behavior**
- **Explain why this enhancement would be useful**

### Pull Requests

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code follows the existing code style
6. Issue that pull request!

## Development Setup

### Python SDK Development

```bash
# Clone your fork
git clone https://github.com/your-username/aetherlab-community.git
cd aetherlab-community/sdks/python

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run linting
flake8 .
black --check .
```

### JavaScript SDK Development

```bash
# Clone your fork
git clone https://github.com/your-username/aetherlab-community.git
cd aetherlab-community/sdks/javascript

# Install dependencies
npm install

# Run tests
npm test

# Run linting
npm run lint

# Build
npm run build
```

## Style Guides

### Git Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

### Python Style Guide

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use [Black](https://github.com/psf/black) for code formatting
- Use type hints where possible
- Write docstrings for all public functions and classes

### JavaScript Style Guide

- Follow the [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- Use ESLint for linting
- Use Prettier for code formatting
- Write JSDoc comments for all public functions and classes

### Documentation Style Guide

- Use Markdown for documentation
- Reference functions and classes in backticks: `function_name()`
- Include code examples for all new features
- Keep line length to 80 characters where possible

## Testing

### Python Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=aetherlab

# Run specific test file
pytest tests/test_client.py
```

### JavaScript Tests

```bash
# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch
```

## Documentation

- Update the README.md with details of changes to the interface
- Update the docs/ folder with any new functionality
- Ensure all examples are tested and working

## Release Process

1. Update version numbers in relevant files
2. Update CHANGELOG.md
3. Create a pull request with the changes
4. After merge, tag the release
5. Publish to package repositories (PyPI/npm)

## Questions?

Feel free to open an issue with your question or reach out on our Discord server.

## Recognition

Contributors will be recognized in our CONTRIBUTORS.md file and on our website.

Thank you for contributing to AetherLab! 🎉 