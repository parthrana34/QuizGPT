# Contributing to QuizGPT

We love your input! We want to make contributing to QuizGPT as easy and transparent as possible. This document provides guidelines and instructions for contributing.

## Code of Conduct

### Our Pledge
We are committed to providing a welcoming and inspiring community for all. Please be respectful and constructive in all interactions.

### Our Standards
Examples of behavior that contributes to creating a positive environment include:
- Using welcoming and inclusive language
- Being respectful of differing opinions, viewpoints, and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

## How Can I Contribute?

### Reporting Bugs
Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, include as many details as possible:

- **Use a clear and descriptive title**
- **Provide a step-by-step explanation** of the problem in as much detail as possible
- **Provide specific examples** to demonstrate the steps
- **Describe the observed behavior** and what exactly is the problem
- **Explain which behavior you expected** to see instead and why
- **Include code samples** when relevant
- **Specify your Python version** and OS
- **Include any relevant error messages or logs**

### Suggesting Enhancements
Enhancement suggestions are tracked as GitHub Issues. When creating an enhancement suggestion, please include:

- **Use a clear and descriptive title**
- **Provide a step-by-step description** of the suggested enhancement in as much detail as possible
- **Provide specific examples** to demonstrate the steps or point out how the feature would be used
- **Explain why this enhancement would be useful** to most QuizGPT users
- **List some other tools or libraries** where this enhancement exists, if applicable

### Pull Requests

- Fill in the required template
- Follow the TypeScript styleguides
- Include appropriate test cases
- Update documentation as needed
- End all files with a newline

### Testing

Before submitting a pull request, ensure all tests pass:

```bash
python -m pytest tests/ -v
```

### Style Guide

#### Python Code Style
- Follow PEP 8
- Use meaningful variable names
- Add docstrings to all functions and classes
- Add type hints
- Maximum line length: 100 characters

#### Example:
```python
def find_answer_index(answer: str, options: List[str]) -> int:
    """
    Find the index of the correct answer in options list.
    
    Args:
        answer: The correct answer text
        options: List of available options
    
    Returns:
        Index of the best matching option (0-based)
    
    Raises:
        ValueError: If options list is empty
    """
    if not options:
        raise ValueError("Options list cannot be empty")
    
    # Implementation here
    return 0
```

#### Docstring Format
Use Google-style docstrings:
```python
def function(arg1: str, arg2: int) -> bool:
    """Brief one-line description.
    
    More detailed explanation of what the function does,
    including any important behavior or side effects.
    
    Args:
        arg1: Description of arg1
        arg2: Description of arg2
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When arg1 is invalid
        TypeError: When arg2 is not an integer
    """
    pass
```

## Development Workflow

### 1. Fork and Clone
```bash
git clone https://github.com/your-username/quizgpt.git
cd quizgpt
```

### 2. Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Development Dependencies
```bash
pip install -e ".[dev]"
pip install pytest pytest-cov black flake8 mypy
```

### 4. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 5. Make Your Changes
- Write clean, well-documented code
- Add tests for new functionality
- Update documentation as needed
- Run tests locally: `pytest tests/ -v`

### 6. Check Code Quality
```bash
# Format code
black src/quizgpt/ tests/

# Lint code
flake8 src/quizgpt/ tests/

# Type checking
mypy src/quizgpt/

# Test coverage
pytest tests/ --cov=quizgpt
```

### 7. Commit Your Changes
```bash
git commit -m "Add feature: clear description of what changed"
```

Follow the [Conventional Commits](https://www.conventionalcommits.org/) standard:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `test:` for test additions/changes
- `refactor:` for code refactoring
- `perf:` for performance improvements
- `chore:` for dependency updates, etc.

### 8. Push and Create Pull Request
```bash
git push origin feature/your-feature-name
```
Then create a Pull Request on GitHub with:
- Clear title and description
- Reference to any related issues
- Screenshots or examples if applicable

## Testing Requirements

### Test Coverage
- Minimum 70% code coverage required
- All new features must have tests
- All bug fixes must include regression tests

### Writing Tests
```python
import pytest
from quizgpt import QuizGPT

def test_quizgpt_initialization():
    """Test that QuizGPT initializes correctly."""
    generator = QuizGPT(api_key="test-key", n_questions=10)
    assert generator.n_questions == 10
    assert generator.api_key == "test-key"

def test_invalid_n_questions():
    """Test that invalid n_questions raises ValueError."""
    with pytest.raises(ValueError):
        QuizGPT(n_questions=15000)  # > 10,000
```

### Running Tests
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_generator.py -v

# Run specific test
pytest tests/test_generator.py::test_quizgpt_initialization -v

# With coverage
pytest tests/ --cov=quizgpt --cov-report=html
```

## Documentation

### Update README
If your changes affect user-facing functionality, update the README:
- Update the feature list if applicable
- Add usage examples
- Document new parameters
- Update API reference if needed

### Update CHANGELOG
Add an entry to CHANGELOG.md under the "[Unreleased]" section:
```markdown
## [Unreleased]
### Added
- New deduplication feature with FAISS support

### Changed
- Improved performance of dimension extraction

### Fixed
- Bug in answer index matching
```

## Release Process

Releases are handled by maintainers. When a release is ready:

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md with release notes
3. Create git tag: `git tag v3.4.0`
4. Run: `python -m build && python -m twine upload dist/*`

## Questions?

- Check [Discussions](https://github.com/your-org/quizgpt/discussions) for Q&A
- Read the [README](README.md) and [EXAMPLES](EXAMPLES.md)
- Review existing [Issues](https://github.com/your-org/quizgpt/issues)

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- GitHub contributors page

Thank you for contributing to QuizGPT! 🎉
