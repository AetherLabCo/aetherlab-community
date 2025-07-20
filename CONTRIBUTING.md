# Contributing to AetherLab Community

Thank you for your interest in contributing to AetherLab! We welcome contributions from the community.

## How to Contribute

### Reporting Issues

If you find a bug or have a feature request:

1. Check if the issue already exists in our [issue tracker](https://github.com/AetherLabCo/aetherlab-community/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce (for bugs)
   - Expected vs actual behavior
   - Your environment details (OS, Python version, SDK version)

### Submitting Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Make your changes**:
   - Write clear, concise commit messages
   - Add tests if applicable
   - Update documentation as needed
3. **Test your changes**:
   ```bash
   cd sdks/python
   python -m pytest tests/  # If tests exist
   python examples/python/simple_example.py  # Manual testing
   ```
4. **Submit a pull request**:
   - Describe your changes
   - Reference any related issues
   - Ensure CI tests pass

### Development Setup

1. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/aetherlab-community.git
   cd aetherlab-community
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the SDK in development mode:
   ```bash
   cd sdks/python
   pip install -e .
   ```

### Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code
- Use meaningful variable and function names
- Add type hints where appropriate
- Document functions and classes with docstrings

### Testing

- Add tests for new features
- Ensure existing tests pass
- Test with multiple Python versions if possible

### Documentation

- Update README files as needed
- Add docstrings to new functions/classes
- Update examples if API changes

## Code of Conduct

Please note that this project is released with a Contributor Code of Conduct. By participating in this project you agree to abide by its terms.

## Questions?

Feel free to reach out:
- Open an issue for questions
- Email: support@aetherlab.ai

Thank you for contributing to AetherLab! 