# Publishing AetherLab Python SDK to PyPI

This guide explains how to publish the AetherLab Python SDK to PyPI.

## Prerequisites

1. PyPI account (create at https://pypi.org/account/register/)
2. Test PyPI account (create at https://test.pypi.org/account/register/)
3. API tokens for both PyPI and Test PyPI
4. Python build tools installed

## Setup

1. Install required tools:
```bash
pip install --upgrade pip setuptools wheel twine build
```

2. Create `~/.pypirc` file with your credentials:
```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = <your-pypi-token>

[testpypi]
username = __token__
password = <your-testpypi-token>
```

## Building the Package

1. Clean previous builds:
```bash
cd sdks/python
rm -rf dist/ build/ *.egg-info/
```

2. Build the package:
```bash
python -m build
```

This creates:
- `dist/aetherlab-0.1.0.tar.gz` (source distribution)
- `dist/aetherlab-0.1.0-py3-none-any.whl` (wheel distribution)

## Testing the Package

1. Upload to Test PyPI first:
```bash
python -m twine upload --repository testpypi dist/*
```

2. Test installation from Test PyPI:
```bash
pip install --index-url https://test.pypi.org/simple/ --no-deps aetherlab
```

3. Verify it works:
```python
from aetherlab import AetherLabClient
print(AetherLabClient.__doc__)
```

## Publishing to PyPI

Once tested, publish to the real PyPI:

```bash
python -m twine upload dist/*
```

## Verification

After publishing, verify the package:

```bash
pip install aetherlab
python -c "import aetherlab; print(aetherlab.__version__)"
```

## Version Management

To release a new version:

1. Update version in:
   - `aetherlab/__init__.py`
   - `setup.py`
   - `pyproject.toml`

2. Commit changes:
```bash
git add -A
git commit -m "Bump version to X.Y.Z"
git tag vX.Y.Z
git push origin main --tags
```

3. Build and publish as above

## Automation with GitHub Actions

Consider setting up GitHub Actions for automated releases. Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.x'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    - name: Build package
      run: python -m build
      working-directory: sdks/python
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: python -m twine upload dist/*
      working-directory: sdks/python
```

## Troubleshooting

- **Name already taken**: The package name "aetherlab" must be unique on PyPI
- **Invalid token**: Ensure your API token starts with `pypi-`
- **Missing files**: Check MANIFEST.in includes all necessary files
- **Import errors**: Verify all dependencies are listed in setup.py 