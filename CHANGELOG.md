# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-17

### Added

- Interactive TUI installer with Textual framework
- File selection with checkbox-style interface
- Real-time diff preview using difflib
- CLI status command showing sync state with Rich tables
- CLI uninstall command with backup restoration
- YAML frontmatter validation for agents, skills, and instructions
- Automatic timestamped backups (microsecond precision)
- Cross-platform VS Code path detection (Linux/macOS/Windows)
- mtime-based file version comparison
- Centralized skills installation to `~/.agents/skills`
- Unified backup directory at `~/.agents/backups`
- Keyboard navigation (space, enter, i, q, a, d, 0-3)
- File type filtering (agents/skills/instructions/all)
- Dry-run support for CLI commands
- Comprehensive test suite (132 tests, 100% passing)
- Complete documentation (README.md + INSTALL.md)
- MIT License

### Technical Details

- Python 3.8+ compatibility
- Dependencies: textual>=0.47.0, rich>=13.0.0, PyYAML>=6.0
- Test coverage: pytest with integration tests
- Exit codes: 0 (success), 1 (error), 2 (invalid args)

[1.0.0]: https://github.com/DarkoKuzmanovic/Cadence/releases/tag/v1.0.0
