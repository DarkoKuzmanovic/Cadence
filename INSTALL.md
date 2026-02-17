# Cadence Installer — Installation Guide

Comprehensive installation, configuration, and usage instructions for the Cadence installer.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)
- [Developer Setup](#developer-setup)

---

## Prerequisites

### Required Software

1. **Python 3.8 or higher**

   ```bash
   # Check Python version
   python --version
   # or
   python3 --version
   ```

   If Python is not installed or version is below 3.8, install from [python.org](https://www.python.org/downloads/).

2. **VS Code Insiders 1.110+**

   Download from [code.visualstudio.com/insiders](https://code.visualstudio.com/insiders).

   **Note:** The installer supports both VS Code Stable and VS Code Insiders. Insiders is recommended for access to the latest Copilot features (parallel subagents, prompt queuing, etc.).

3. **GitHub Copilot**

   Install the Copilot extension in VS Code from the Extensions marketplace or visit [github.com/features/copilot](https://github.com/features/copilot).

### VS Code Settings (Required)

Add to your VS Code `settings.json`:

```json
{
  "chat.customAgentInSubagent.enabled": true,
  "terminal.integrated.chatSandbox.enabled": true
}
```

These settings enable custom agents to invoke subagents and allow terminal access during chat sessions.

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/DarkoKuzmanovic/Cadence.git
cd Cadence
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies installed:**

- `textual` — Terminal UI framework for the TUI installer
- `rich` — Beautiful terminal formatting
- `pyyaml` — YAML parsing for frontmatter validation
- `tomli` / `tomli_w` — TOML config file support (Python < 3.11 needs `tomli`)

### 3. Run the Installer

#### Interactive TUI Mode (Recommended)

```bash
python install.py
```

This launches the interactive terminal UI where you can:

- Browse agent, skill, and instruction files
- Preview diffs before installing
- Select multiple files with keyboard shortcuts
- Filter by file type (agents, skills, instructions)

#### CLI Mode

Check installation status:

```bash
python install.py status
```

Run in a different workspace:

```bash
python install.py status /path/to/workspace
```

---

## Installation Paths

The installer places files in platform-specific directories:

### Agent and Instruction Files

These are placed in the VS Code User prompts directory:

| Platform    | Path                                                          |
| ----------- | ------------------------------------------------------------- |
| **Linux**   | `~/.config/Code - Insiders/User/prompts/`                     |
| **macOS**   | `~/Library/Application Support/Code - Insiders/User/prompts/` |
| **Windows** | `%APPDATA%\Code - Insiders\User\prompts\`                     |

**File types:**

- `*.agent.md` — Agent definition files
- `*.instructions.md` — Global instruction files

### Skill Files

Skills are centralized in `~/.agents/skills/` for all platforms:

```
~/.agents/skills/
├── brainstorming/
│   └── SKILL.md
├── code-review/
│   ├── SKILL.md
│   └── references/
│       └── style-guide.md
└── tdd-workflow/
    └── SKILL.md
```

This allows skills to be shared across projects and VS Code instances.

---

## Configuration

### Config File Location

`~/.cadence/config.toml` (optional)

The installer works without a config file. Configuration is primarily for advanced use cases or testing.

### Config Format

```toml
[installation]
# VS Code variant: "insiders" or "stable"
vscode_variant = "insiders"

# Override default installation paths (optional)
prompts_dir = "~/.config/Code - Insiders/User/prompts"
skills_dir = "~/.agents/skills"

[backup]
# Enable/disable backups (default: true)
enabled = true

# Backup directory (default: ~/.agents/backups)
location = "~/.agents/backups"

[validation]
# Validate YAML frontmatter before install (default: true)
enabled = true
```

### Creating a Config File

```bash
mkdir -p ~/.cadence

cat > ~/.cadence/config.toml << 'EOF'
[installation]
vscode_variant = "insiders"

[backup]
enabled = true
location = "~/.agents/backups"
EOF
```

---

## Usage

### Interactive TUI Mode

Launch the TUI installer:

```bash
cd /path/to/Cadence
python install.py
```

#### Keyboard Shortcuts

| Key       | Action                         |
| --------- | ------------------------------ |
| `space`   | Toggle file selection          |
| `enter`   | Show diff for selected file    |
| `i`       | Install selected files         |
| `a`       | Select all files               |
| `d`       | Deselect all files             |
| `0`       | Filter: Show all files         |
| `1`       | Filter: Show agents only       |
| `2`       | Filter: Show skills only       |
| `3`       | Filter: Show instructions only |
| `↑` / `↓` | Navigate file list             |
| `q`       | Quit                           |

#### TUI Workflow

1. **Browse Files** — The TUI scans the current directory for `.agent.md`, `.instructions.md`, and `SKILL.md` files.
2. **Select Files** — Use `space` to toggle selection. Files are auto-selected if they are new or have updates.
3. **Preview Changes** — Press `enter` to see a diff of what will change.
4. **Install** — Press `i` to install all selected files. Backups are created automatically.

#### File Status Indicators

- **✓ Identical** — Installed version matches repository
- **🔼 Newer** — Repository has a newer version
- **🔽 Older** — Repository is older than installed (local changes?)
- **➕ New** — File not installed yet
- **❌ Missing** — File expected but not found

### CLI Mode

#### Status Command

Show sync status for all files in the current directory:

```bash
python install.py status
```

Check a specific workspace:

```bash
python install.py status /path/to/workspace
```

**Example output:**

```
┌──────────────────────────────┬──────────────────┬──────────────────┬──────────────────┐
│ File                         │ Status           │ Installed        │ Repository       │
├──────────────────────────────┼──────────────────┼──────────────────┼──────────────────┤
│ Builder.agent.md             │ ✓ Up-to-date     │ 2026-02-17 10:30 │ 2026-02-17 10:30 │
│ Scout.agent.md               │ ↓ Update avail.  │ 2026-02-16 14:20 │ 2026-02-17 09:15 │
│ Cadence.agent.md             │ ✓ Up-to-date     │ 2026-02-17 11:00 │ 2026-02-17 11:00 │
│ skills/tdd-workflow/SKILL.md │ ↑ Local changes  │ 2026-02-17 15:00 │ 2026-02-16 12:00 │
└──────────────────────────────┴──────────────────┴──────────────────┴──────────────────┘

4 files total: 2 up-to-date, 1 update available, 1 local changes
```

**Status meanings:**

- **✓ Up-to-date** — Versions match
- **↓ Update available** — Newer version in repository
- **↑ Local changes** — Installed version is newer than repository (you may have edited it)
- **✗ Not installed** — File exists in repo but not installed
- **? Orphaned** — File installed but not in repository

#### Uninstall Command

Remove a file (creates backup before removal):

```bash
python install.py uninstall <file-path>
```

**Examples:**

```bash
# Remove a specific file (interactive confirmation)
python install.py uninstall ~/.config/Code\ -\ Insiders/User/prompts/Builder.agent.md

# Skip confirmation
python install.py uninstall --yes Builder.agent.md

# Dry run (preview without executing)
python install.py uninstall --dry-run Builder.agent.md

# Restore from backup
python install.py uninstall --restore Builder.agent.md

# Custom backup directory
python install.py uninstall --backup-dir ~/custom-backups Builder.agent.md
```

**Flags:**

- `--restore` — Restore file from most recent backup instead of removing
- `--dry-run` — Show what would happen without executing
- `--yes` — Skip confirmation prompt
- `--backup-dir <path>` — Use custom backup directory (default: `~/.agents/backups`)

---

## Troubleshooting

### "VS Code not detected"

**Problem:** Installer cannot find VS Code Insiders installation.

**Possible causes:**

1. VS Code Insiders is not installed.
2. Non-standard installation path.

**Solutions:**

1. Verify VS Code Insiders is installed:

   ```bash
   # Linux
   ls ~/.config/Code\ -\ Insiders/

   # macOS
   ls ~/Library/Application\ Support/Code\ -\ Insiders/

   # Windows
   dir %APPDATA%\Code\ -\ Insiders
   ```

2. If using VS Code Stable instead, create a config file:

   ```toml
   # ~/.cadence/config.toml
   [installation]
   vscode_variant = "stable"
   prompts_dir = "~/.config/Code/User/prompts"  # Linux example
   ```

### "Permission denied"

**Problem:** Installer cannot write to installation directories.

**Possible causes:**

1. Insufficient file permissions.
2. Directory owned by another user.

**Solutions:**

1. Check directory permissions:

   ```bash
   ls -ld ~/.config/Code\ -\ Insiders/User/prompts/
   ```

2. Fix ownership (Linux/macOS):

   ```bash
   sudo chown -R $USER:$USER ~/.config/Code\ -\ Insiders/
   ```

3. Ensure the directory exists:

   ```bash
   mkdir -p ~/.config/Code\ -\ Insiders/User/prompts/
   ```

### "Invalid YAML frontmatter"

**Problem:** File validation fails during installation.

**Cause:** Agent or skill files require valid YAML frontmatter for proper recognition by VS Code.

**Format requirements:**

**Agent files (`.agent.md`):**

```markdown
---
name: agent-name
description: Brief description
model: claude-4-opus
---

# Agent content here
```

**Skill files (`SKILL.md`):**

```markdown
---
name: skill-name
description: What this skill does
---

# Skill content here
```

**Instruction files (`.instructions.md`):**

```markdown
---
applyTo: "**"
---

# Instructions here
```

**Solution:**

1. Check the error message for specific validation issues.
2. Manually validate YAML frontmatter:

   ```bash
   # Install yq for YAML validation
   pip install yq

   # Extract and validate frontmatter
   sed -n '/^---$/,/^---$/p' file.agent.md | yq .
   ```

3. Common errors:
   - Missing closing `---`
   - Unquoted strings with special characters
   - Inconsistent indentation
   - Missing required fields (`name`, `description`)

### "Backup restoration failed"

**Problem:** Cannot restore file from backup.

**Possible causes:**

1. Backup file doesn't exist.
2. Corrupted backup file.
3. Permission issues.

**Solutions:**

1. List available backups:

   ```bash
   ls -lh ~/.agents/backups/
   ```

   Backup files are named: `<filename>.<timestamp>`

2. Manually restore from backup:

   ```bash
   cp ~/.agents/backups/Builder.agent.md.20260217103045 \
      ~/.config/Code\ -\ Insiders/User/prompts/Builder.agent.md
   ```

3. Check backup directory permissions:

   ```bash
   ls -ld ~/.agents/backups/
   ```

### "No files found"

**Problem:** TUI or status command shows no files.

**Cause:** Installer scans the current working directory. If run from the wrong location, it won't find any files.

**Solution:**

Run the installer from the Cadence repository root:

```bash
cd /path/to/Cadence
python install.py
```

Or specify the workspace explicitly:

```bash
python install.py status /path/to/Cadence
```

### "Import error: No module named 'textual'"

**Problem:** Missing dependencies.

**Solution:**

Install required packages:

```bash
pip install -r requirements.txt
```

For Python < 3.11, ensure `tomli` is installed:

```bash
pip install tomli
```

---

## Developer Setup

### Running Tests

The project uses pytest for testing.

**Run all tests:**

```bash
pytest
```

**Run with coverage:**

```bash
pytest --cov=cadence_installer --cov-report=html
```

**Run specific test file:**

```bash
pytest tests/test_sync.py
```

**Run specific test:**

```bash
pytest tests/test_sync.py::test_compare_file_times
```

### Code Structure

```
Cadence/
├── install.py                  # Main entry point (TUI + CLI router)
├── cadence_installer/          # Core installer package
│   ├── cli.py                  # CLI commands (status, uninstall)
│   ├── config.py               # Config file handling and path detection
│   ├── sync.py                 # File syncing and comparison logic
│   ├── ui.py                   # Interactive TUI using textual
│   └── validation.py           # YAML frontmatter validation
├── tests/                      # Test suite
│   ├── test_cli.py             # CLI command tests
│   ├── test_config.py          # Config and path detection tests
│   ├── test_sync.py            # Sync logic tests
│   ├── test_ui.py              # TUI tests (mocked)
│   ├── test_validation.py      # Validation tests
│   └── test_integration.py     # End-to-end integration tests
├── pytest.ini                  # Pytest configuration
├── requirements.txt            # Python dependencies
└── README.md                   # Project overview
```

### Key Modules

**`sync.py`**

- File comparison logic (modification times, content hashing)
- Backup creation and restoration
- File validation (extensions, naming)

**`validation.py`**

- YAML frontmatter parsing and validation
- Required field checking for agents, skills, instructions

**`cli.py`**

- Status command implementation
- Uninstall command with restore support
- Rich terminal formatting

**`ui.py`**

- Textual-based TUI application
- File selection and preview
- Diff generation

**`config.py`**

- Platform detection (Linux, macOS, Windows)
- VS Code path resolution
- TOML config file reading/writing

### Development Workflow

1. **Make changes** to the codebase
2. **Run tests** to ensure nothing breaks:

   ```bash
   pytest
   ```

3. **Manual testing** with the TUI:

   ```bash
   python install.py
   ```

4. **Check code style** (optional, if using linters):

   ```bash
   # Install development tools
   pip install black flake8 mypy

   # Format code
   black cadence_installer/ tests/

   # Check style
   flake8 cadence_installer/ tests/

   # Type check
   mypy cadence_installer/
   ```

### Adding New Features

**Example: Adding a new CLI command**

1. Add command handler in `cli.py`:

   ```python
   def my_command(args):
       """Handle my_command."""
       # Implementation here
   ```

2. Register command in `install.py`:

   ```python
   my_parser = subparsers.add_parser("mycommand", help="My new command")
   my_parser.add_argument("--option", help="Command option")
   ```

3. Route command in `install.py` main:

   ```python
   if args.command == "mycommand":
       my_command_handler(args)
   ```

4. Write tests in `tests/test_cli.py`:

   ```python
   def test_my_command():
       # Test implementation
       pass
   ```

5. Run tests:

   ```bash
   pytest tests/test_cli.py::test_my_command
   ```

### Dependencies

**Runtime:**

- `textual>=0.47.0` — TUI framework
- `rich>=13.7.0` — Terminal formatting
- `pyyaml>=6.0` — YAML parsing
- `tomli>=2.0.0` — TOML parsing (Python < 3.11)
- `tomli_w>=1.0.0` — TOML writing

**Development:**

- `pytest>=7.4.0` — Testing framework
- `pytest-cov>=4.1.0` — Coverage reporting
- `black>=23.12.0` — Code formatting (optional)
- `flake8>=6.1.0` — Linting (optional)
- `mypy>=1.7.0` — Type checking (optional)

### Contributing Guidelines

1. **Fork the repository** on GitHub
2. **Create a feature branch:** `git checkout -b feature/my-feature`
3. **Make changes** and add tests
4. **Run the test suite:** `pytest`
5. **Commit with conventional commits:** `feat: add new command`
6. **Push to your fork:** `git push origin feature/my-feature`
7. **Open a pull request** on GitHub

---

## Additional Resources

- **Main README:** [README.md](README.md) — Project overview and quick start
- **Agent Conventions:** [AGENTS.md](AGENTS.md) — Cadence agent architecture and workflow
- **GitHub Repository:** [github.com/DarkoKuzmanovic/Cadence](https://github.com/DarkoKuzmanovic/Cadence)
- **VS Code Copilot Docs:** [code.visualstudio.com/docs/copilot](https://code.visualstudio.com/docs/copilot)

---

**Questions or Issues?**

Open an issue on GitHub or reach out:

- Email: <darko.kuzmanovic@gmail.com>
- Website: [https://quz.ma](https://quz.ma)
