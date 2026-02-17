# Cadence

An automated installer for the Cadence multi-agent orchestration system. Deploy agents, skills, and instructions to VS Code Insiders with validation, backups, and sync tracking.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![CI Tests](https://github.com/DarkoKuzmanovic/Cadence/workflows/CI%20Tests/badge.svg)](https://github.com/DarkoKuzmanovic/Cadence/actions)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## What is Cadence?

Cadence is a minimal multi-agent orchestration system for VS Code Copilot (3+1 agents, 3 state files, zero bloat). This installer manages deployment of agent definitions, skills, and instruction files to your VS Code Insiders environment.

**Key insight:** Opus is the planner. Don't delegate planning to a lesser model — delegate _execution_.

## Features

- **🎨 Interactive TUI** — Browse files, preview diffs, and install with keyboard shortcuts
- **📊 Sync Status** — Track installed vs repository versions for all files
- **✅ Validation** — YAML frontmatter checking before installation
- **💾 Automatic Backups** — All overwrites backed up to `~/.agents/backups`
- **🔄 Restore Support** — Roll back to previous versions on demand
- **🗂️ Organized Installation** — Agents and instructions to User/prompts, skills to `~/.agents/skills`
- **⚡ CLI Commands** — Status reporting and uninstall via command-line
- **🎯 Cross-Platform** — Linux, macOS, and Windows support

## Quick Start

```bash
# Clone the repository
git clone https://github.com/DarkoKuzmanovic/Cadence.git
cd Cadence

# Install dependencies
pip install -r requirements.txt

# Launch interactive installer
python install.py

# Or check sync status
python install.py status

# View help
python install.py --help
```

The TUI will scan the repository for agent files in `agents/` (`.agent.md`), instruction files in `instructions/` (`.instructions.md`), and skill directories in `skills/` (`SKILL.md`). Select files with `space`, press `i` to install.

## Usage Examples

### Interactive TUI Mode

```bash
# Launch from the Cadence repository
cd /path/to/Cadence
python install.py
```

**Keyboard shortcuts:**

- `space` — Toggle file selection
- `enter` — Show diff for selected file
- `i` — Install selected files
- `a` / `d` — Select/deselect all
- `0-3` — Filter by type (all/agents/skills/instructions)
- `q` — Quit

### CLI Status Command

```bash
# Show sync status for current directory
python install.py status

# Check a specific workspace
python install.py status /path/to/workspace

# Example output:
# ┌──────────────────┬──────────────────┬────────────────┬──────────────────┐
# │ File             │ Status           │ Installed      │ Repository       │
# ├──────────────────┼──────────────────┼────────────────┼──────────────────┤
# │ Builder.agent.md │ ✓ Up-to-date     │ 2026-02-17 ... │ 2026-02-17 ...   │
# │ Scout.agent.md   │ ↓ Update avail.  │ 2026-02-16 ... │ 2026-02-17 ...   │
# └──────────────────┴──────────────────┴────────────────┴──────────────────┘
#
# Note: Agent files are stored in agents/ directory in the repository
```

### CLI Uninstall Command

```bash
# Uninstall specific files (with confirmation)
python install.py uninstall ~/.config/Code\ -\ Insiders/User/prompts/Builder.agent.md

# Skip confirmation
python install.py uninstall --yes Builder.agent.md

# Dry run to see what would happen
python install.py uninstall --dry-run Builder.agent.md

# Restore from backup
python install.py uninstall --restore Builder.agent.md
```

## Agent Architecture

Cadence uses specialized agents for different tasks. See [AGENTS.md](AGENTS.md) for detailed conventions.

**Core agents:**

- **Cadence** (Opus 4.6) — Plans, orchestrates, manages interaction
- **Scout** (Gemini Flash) — Parallel read-only codebase exploration
- **Builder** (Sonnet 4.5) — TDD-driven implementation
- **Critic** (Sonnet 4.5) — Code review and verification

**Utility agents:**

- **Forge** — Specialized implementation orchestration
- **Frontend-Engineer** — UI/UX and frontend work
- **Workhorse** — General-purpose autonomous coding

## Installation Details

For comprehensive installation instructions, platform-specific notes, troubleshooting, and developer setup, see [INSTALL.md](INSTALL.md).

**Installation targets:**

- **Linux:** `~/.config/Code - Insiders/User/prompts/`
- **macOS:** `~/Library/Application Support/Code - Insiders/User/prompts/`
- **Windows:** `%APPDATA%\Code - Insiders\User\prompts\`
- **Skills:** `~/.agents/skills/` (all platforms)

## Requirements

- Python 3.8+
- VS Code Insiders 1.110+
- Dependencies: `textual`, `rich`, `tomli`, `tomli_w`, `pyyaml`

## Configuration

Optional config file: `~/.cadence/config.toml`

```toml
[installation]
vscode_variant = "insiders"  # or "stable"
prompts_dir = "~/.config/Code - Insiders/User/prompts"
skills_dir = "~/.agents/skills"

[backup]
enabled = true
location = "~/.agents/backups"
```

## Author & License

**Darko Kuzmanovic**
Email: <darko.kuzmanovic@gmail.com>
Website: [https://quz.ma](https://quz.ma)
GitHub: [github.com/DarkoKuzmanovic](https://github.com/DarkoKuzmanovic)

Licensed under the MIT License. © 2026

**Credits:** Inspired by [copilot-orchestra](https://github.com/ShepAlderson/copilot-orchestra) and [Copilot Atlas](https://github.com/bigguy345/Github-Copilot-Atlas).
