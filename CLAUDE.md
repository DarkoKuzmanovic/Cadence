# Cadence — Agent Installer for VS Code

Automated installer for a multi-agent orchestration system. Deploys agents, skills, and instruction files to VS Code Insiders with validation, backups, and sync tracking.

## Quick Reference

| What | Command |
|------|---------|
| Run TUI | `python install.py` |
| Show status | `python install.py status` |
| Run tests | `pytest tests/ -v` |
| Tests + coverage | `pytest tests/ --cov=cadence_installer --cov-report=html` |
| Dev setup | `python -m venv .venv && source .venv/bin/activate && pip install -e .[dev]` |

## Architecture

```
cadence_installer/     Main package (~1,500 LOC)
  ├── cli.py           CLI status/uninstall commands
  ├── config.py        Path detection & platform config
  ├── sync.py          File sync logic
  ├── ui.py            Textual TUI installer
  └── validation.py    YAML frontmatter validation
agents/                Agent definitions (.agent.md)
skills/                Skill modules (brainstorming, code-review, etc.)
instructions/          Instruction files
prompts/               Prompt templates
tests/                 Pytest suite (~2,400 LOC)
```

- **Python 3.8+**, setuptools, Textual TUI, Rich output, PyYAML
- **CI**: GitHub Actions matrix (Ubuntu/macOS/Windows x Python 3.8-3.12)
- **Target**: 100% test coverage

## Conventions

- Cross-platform paths via `pathlib.Path` (never string concatenation)
- Dataclasses for data structures, Enums for status types
- PEP 8 + Black formatting, type hints throughout
- Conventional Commits (`feat:`, `fix:`, `test:`, etc.)
- YAML frontmatter (`---\nname: ...\n---`) for agent/skill metadata
