# Testing with pytest

This directory contains both unittest-style tests and pytest-style tests for the sum-tool package.

## Test Files

### Unittest Style (Original)
- `test_calculator.py` - Tests for the calculator module using unittest
- `test_verifier.py` - Tests for the verifier module using unittest

### Pytest Style (New)
- `test_calculator_pytest.py` - Pytest-style tests for the calculator module
- `test_verifier_pytest.py` - Pytest-style tests for the verifier module

## Running Tests

### Using pytest (Recommended)

```bash
# Activate virtual environment
source venv/bin/activate

# Install pytest if not already installed
pip install pytest

# Run all pytest-style tests
pytest tests/test_*_pytest.py

# Run all tests (both unittest and pytest styles)
pytest tests/

# Run with verbose output
pytest -v tests/

# Run specific test file
pytest tests/test_calculator_pytest.py

# Run specific test class
pytest tests/test_calculator_pytest.py::TestCalculateFileHash

# Run specific test function
pytest tests/test_calculator_pytest.py::TestCalculateFileHash::test_md5_hash

# Run with coverage report (requires pytest-cov)
pytest --cov=sumtool tests/

# Run only fast tests (exclude slow tests)
pytest -m "not slow" tests/

# Run integration tests only
pytest -m integration tests/
```

### Using unittest (Original)

```bash
# Activate virtual environment
source venv/bin/activate

# Run all unittest-style tests
python -m unittest discover tests/

# Run specific test module
python -m unittest tests.test_calculator

# Run with verbose output
python -m unittest discover tests/ -v
```

## Pytest Features Demonstrated

The pytest-style tests showcase modern pytest features:

### 1. Fixtures
```python
@pytest.fixture
def test_dir():
    """Create a temporary directory for testing."""
    test_dir = tempfile.mkdtemp()
    yield test_dir
    shutil.rmtree(test_dir)
```

### 2. Parameterized Tests
```python
@pytest.mark.parametrize("algorithm,expected_length", [
    ("md5", 32),
    ("sha1", 40),
    ("sha256", 64),
    ("sha512", 128),
])
def test_algorithm_parameters(self, test_file_with_content, algorithm, expected_length):
    """Test all supported algorithms with parameterized testing."""
```

### 3. Assertions
Simple assert statements instead of unittest's assert methods:
```python
assert result == "expected_value"
assert len(result) == 64
assert "test.tmp" not in rel_paths
```

### 4. Exception Testing
```python
with pytest.raises(ValueError, match="Unsupported algorithm"):
    calculate_file_hash(test_file_with_content, "invalid_algorithm")

with pytest.raises(FileNotFoundError):
    calculate_file_hash("/nonexistent/file.txt", "sha256")
```

### 5. Markers
```python
@pytest.mark.slow
@pytest.mark.integration
```

## Test Coverage

To generate a coverage report:

```bash
# Install coverage tools
pip install pytest-cov

# Run tests with coverage
pytest --cov=sumtool tests/ --cov-report=html

# View HTML report
open htmlcov/index.html  # On macOS
xdg-open htmlcov/index.html  # On Linux
```

## Test Organization

### Calculator Tests (`test_calculator_pytest.py`)
- **TestCalculateFileHash**: Tests for single file hash calculation
  - MD5, SHA1, SHA256, SHA512 algorithms
  - Error handling (unsupported algorithms, missing files)
  - Case insensitivity
  
- **TestCalculateChecksums**: Tests for directory checksum calculation
  - Single and multiple directories
  - Exclude patterns
  - Output file generation
  - Different algorithms

- **TestEdgeCases**: Edge cases and error handling
  - Empty directories
  - Nested directory structures
  - Large file handling
  - Parameterized algorithm tests

### Verifier Tests (`test_verifier_pytest.py`)
- **TestVerifySingleFile**: Single file verification
  - Success and failure cases
  - Missing files
  - Result attributes

- **TestDetectAlgorithm**: Algorithm detection from hash length
  - All supported algorithms
  - Default behavior
  - Parameterized tests

- **TestVerifyChecksums**: Directory verification
  - All files present
  - Modified files
  - Missing files
  - Auto-discovery of .sum files

- **TestVerificationResults**: VerificationResult dataclass tests
  - OK, FAILED, MISSING states

- **TestIntegration**: End-to-end workflow tests
  - Complete calc -> modify -> verify workflow
  - Cross-directory verification

## Best Practices

### Fixtures
- Use fixtures for common setup/teardown
- Named fixtures for clarity (`test_file_with_content`, `verification_test_setup`)
- Automatic cleanup with `yield`

### Assertions
- Use simple `assert` statements
- Clear error messages when needed
- One assertion per concept

### Test Structure
- Descriptive test names
- Group related tests in classes
- Separate concerns (unit vs integration)

### Parametrization
- Reduce code duplication
- Test multiple inputs easily
- Clear test case descriptions

## Migration from unittest to pytest

If migrating existing unittest tests to pytest:

1. Replace `unittest.TestCase` inheritance with regular classes
2. Replace `setUp()` with `@pytest.fixture`
3. Replace `tearDown()` with fixture cleanup (after `yield`)
4. Replace `self.assertEqual()` with `assert`
5. Replace `with self.assertRaises()` with `with pytest.raises()`
6. Use `@pytest.mark.parametrize` for data-driven tests

Example:

**unittest:**
```python
class TestHash(unittest.TestCase):
    def setUp(self):
        self.file = create_test_file()
    
    def test_md5(self):
        result = calculate_md5(self.file)
        self.assertEqual(len(result), 32)
```

**pytest:**
```python
@pytest.fixture
def test_file():
    return create_test_file()

def test_md5(test_file):
    result = calculate_md5(test_file)
    assert len(result) == 32
```

## Continuous Integration

Add to your CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.7", "3.8", "3.9", "3.10", "3.11"]
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install pytest pytest-cov
        pip install -e .
    
    - name: Run tests
      run: |
        pytest --cov=sumtool tests/
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## Troubleshooting

### Tests not discovered
- Check that test files start with `test_`
- Check that test classes start with `Test`
- Check that test functions start with `test_`

### Fixture errors
- Ensure fixtures are defined before use
- Check fixture scope if using caching
- Use `conftest.py` for shared fixtures

### Import errors
- Install package in development mode: `pip install -e .`
- Check PYTHONPATH includes project root

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [pytest parametrization](https://docs.pytest.org/en/stable/parametrize.html)
- [pytest best practices](https://docs.pytest.org/en/stable/explanation/best_practices.html)
