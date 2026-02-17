# Contributing to Cadence

Thank you for your interest in contributing to Cadence! This document provides guidelines for contributing to the project.

## Development Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/DarkoKuzmanovic/Cadence.git
   cd Cadence
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # or
   .venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -e .[dev]
   ```

4. **Run tests**
   ```bash
   pytest tests/ -v
   ```

## Making Changes

1. **Create a feature branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed

3. **Run tests**

   ```bash
   # Run all tests
   pytest tests/ -v

   # Run specific test file
   pytest tests/test_ui.py -v

   # Run with coverage
   pytest tests/ --cov=cadence_installer --cov-report=html
   ```

4. **Commit your changes**

   ```bash
   git add .
   git commit -m "feat: Add your feature description"
   ```

   Use conventional commit messages:
   - `feat:` - New features
   - `fix:` - Bug fixes
   - `docs:` - Documentation changes
   - `test:` - Test additions or changes
   - `refactor:` - Code refactoring
   - `chore:` - Maintenance tasks

5. **Push and create a pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for public functions and classes
- Keep functions focused and single-purpose
- Use pathlib.Path for file operations (cross-platform compatibility)

## Testing Guidelines

- Write tests for all new functionality
- Maintain or improve test coverage (currently 100%)
- Use pytest fixtures for test setup
- Test cross-platform behavior where applicable
- Include integration tests for user-facing features

## Documentation

- Update README.md for user-facing changes
- Update INSTALL.md for installation/setup changes
- Update CHANGELOG.md following [Keep a Changelog](https://keepachangelog.com/) format
- Add docstrings to new functions/classes

## Pull Request Process

1. Ensure all tests pass
2. Update documentation
3. Add entry to CHANGELOG.md under "Unreleased"
4. Request review from maintainers
5. Address review feedback
6. Squash commits if requested

## Reporting Issues

When reporting bugs, please include:

- Operating system and version
- Python version
- Steps to reproduce
- Expected vs actual behavior
- Error messages or logs
- VS Code/VS Code Insiders version (if relevant)

## Questions?

Feel free to open an issue for questions or discussions about proposed changes.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
