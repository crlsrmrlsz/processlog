# Contributing to Event Log Generator

Thank you for your interest in contributing to Event Log Generator! This project aims to support the process mining community by providing high-quality synthetic test data for developing and testing process mining software.

## Ways to Contribute

### 🐛 Report Bugs
- Use GitHub Issues to report bugs
- Include detailed reproduction steps
- Provide your environment details (OS, Python version)
- Attach relevant config files and error messages

### 📝 Improve Documentation
- Fix typos or clarify existing docs
- Add examples for common use cases
- Improve inline code comments
- Translate documentation

### ✨ Add Example Configurations
- Create new process configurations for different domains
- Share interesting process patterns (loops, parallel flows, etc.)
- Document real-world process adaptations

### 🧪 Expand Test Coverage
- Add tests for edge cases
- Improve integration tests with PM4Py
- Add performance benchmarks

### 🔧 Propose New Features
- Open an issue first to discuss the feature
- Explain the use case and benefits
- Consider backward compatibility

## Development Setup

### Prerequisites
- Python 3.10 or higher
- Git

### Setup Instructions

```bash
# Clone the repository
git clone https://github.com/crlsrmrlsz/event-log-gen.git
cd event-log-gen

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=event_log_gen --cov-report=html

# Run specific test file
pytest tests/test_core/test_generator.py -v

# Run PM4Py integration tests
pytest tests/test_pm4py_compatibility.py -v
```

### Code Quality

```bash
# Format code with black
black src/ tests/

# Sort imports
isort src/ tests/

# Type checking
mypy src/

# Linting
flake8 src/ tests/
```

## Contribution Workflow

### 1. Fork and Branch
```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/YOUR_USERNAME/event-log-gen.git
cd event-log-gen

# Create a feature branch
git checkout -b feature/your-feature-name
```

### 2. Make Changes
- Write code following the existing style
- Add tests for new functionality
- Update documentation as needed
- Keep commits focused and atomic

### 3. Test Your Changes
```bash
# Run tests
pytest tests/ -v

# Verify CLI still works
event-log-gen validate -c configs/process_config.yaml
event-log-gen generate -c configs/process_config.yaml -n 10 -f csv
```

### 4. Commit Guidelines
Follow conventional commit format:

```
type(scope): short description

Longer description if needed

Fixes #123
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions/changes
- `refactor`: Code refactoring
- `chore`: Build/tooling changes

**Examples:**
```
feat(exporter): add SQLite export format
fix(validator): handle empty activity lists
docs(readme): add PM4Py visualization example
test(generator): add calendar edge cases
```

### 5. Submit Pull Request
- Push to your fork
- Open PR against `main` branch
- Fill out the PR template
- Link related issues
- Wait for review

## Code Standards

### Python Style
- Follow PEP 8
- Use type hints
- Write docstrings for public APIs
- Maximum line length: 100 characters

### Code Principles
- **SOLID principles**: Single responsibility, Open/closed, Liskov substitution
- **DRY**: Don't repeat yourself
- **KISS**: Keep it simple and stupid
- **Clean Code**: Expressive names, small functions, clear intent

### Testing
- Write tests for new features
- Aim for >80% code coverage
- Test edge cases and error paths
- Use descriptive test names

## Documentation

### Docstring Format
```python
def function_name(param: type) -> return_type:
    """
    Short one-line description.

    Longer description if needed.

    Args:
        param: Description of parameter

    Returns:
        Description of return value

    Raises:
        ExceptionType: When this exception is raised

    Example:
        >>> function_name(value)
        expected_output
    """
```

### Configuration Examples
When adding example configurations:
- Include inline comments explaining parameters
- Show realistic values
- Document expected outputs
- Test with actual generation

## Project Structure

```
event-log-gen/
├── src/event_log_gen/       # Main package
│   ├── config/              # Configuration loading and validation
│   ├── core/                # Event generation engine
│   ├── exporters/           # Format exporters (CSV, Parquet, JSON, XES)
│   └── utils/               # Utilities (naming, metadata)
├── tests/                   # Test suite
├── configs/                 # Example configurations
├── docs/                    # Documentation
└── examples/                # Usage examples
```

## Release Process (Maintainers Only)

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create git tag: `git tag -a v1.x.x -m "Release v1.x.x"`
4. Push tag: `git push origin v1.x.x`
5. Create GitHub release from tag

## Getting Help

- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: General questions and ideas
- **Email**: crlsrmrlsz@gmail.com for private inquiries

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to Event Log Generator!** 🎉

Your efforts help the process mining community build better tools and advance the field of process analytics.
