"""Interactive TUI installer for Cadence agents and skills."""

import difflib
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Header, Footer, Static, DataTable, Label, ProgressBar
from textual.binding import Binding
from textual import events

from cadence_installer.config import (
    detect_vscode_insiders_paths,
    detect_agents_skills_path,
    get_user_home,
)
from cadence_installer.sync import (
    compare_file_times,
    create_backup,
    validate_file_type,
    FileStatus
)
from cadence_installer.validation import validate_file, ValidationStatus


@dataclass
class FileItem:
    """Represents a file to be installed."""
    source: Path
    dest: Path
    status: FileStatus
    relative_source: str
    relative_dest: str
    selected: bool = field(default=False)
    visible: bool = field(default=True)

    def __post_init__(self):
        """Set default selection based on status."""
        if self.selected is False:  # Only auto-set if not explicitly set
            # Auto-select new files and newer files
            if self.status in (FileStatus.SOURCE_NEWER, FileStatus.DEST_MISSING):
                self.selected = True
            else:
                self.selected = False


class InstallerApp(App):
    """Interactive TUI installer application."""

    CSS = """
    Screen {
        background: $background;
    }

    #main-container {
        height: 100%;
    }

    #file-list-container {
        width: 3fr;
        border: solid $primary;
        height: 100%;
    }

    #diff-container {
        width: 2fr;
        border: solid $accent;
        height: 100%;
        padding: 1;
    }

    #status-bar {
        dock: bottom;
        height: 3;
        background: $panel;
        border-top: solid $primary;
    }

    DataTable {
        height: 1fr;
    }

    .status-message {
        color: $success;
    }

    .error-message {
        color: $error;
    }

    ProgressBar {
        margin: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("space", "toggle_selection", "Toggle"),
        Binding("enter", "show_diff", "Diff"),
        Binding("i", "install", "Install"),
        Binding("a", "select_all", "Select All"),
        Binding("d", "deselect_all", "Deselect All"),
        Binding("0", "filter_all", "All"),
        Binding("1", "filter_agents", "Agents"),
        Binding("2", "filter_skills", "Skills"),
        Binding("3", "filter_instructions", "Instructions"),
        Binding("up", "cursor_up", "Up", show=False),
        Binding("down", "cursor_down", "Down", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.file_items: List[FileItem] = []
        self.selected_index: int = 0
        self.selected_file: Optional[FileItem] = None
        self.current_diff: Optional[str] = None
        self.status_message: Optional[str] = None
        self.installation_progress: int = 0
        self.current_filter: Optional[str] = None
        self.workspace_root = Path.cwd()

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()

        with Container(id="main-container"):
            with Horizontal():
                with VerticalScroll(id="file-list-container"):
                    yield DataTable(id="file-table")

                with VerticalScroll(id="diff-container"):
                    yield Static("", id="diff-display")

        with Container(id="status-bar"):
            yield Label("", id="status-label")
            yield ProgressBar(id="progress-bar", total=100, show_eta=False)

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the application."""
        # Scan workspace for files
        self._scan_workspace()

        # Setup file table
        table = self.query_one("#file-table", DataTable)
        table.add_columns("", "File", "Status", "Destination")
        table.cursor_type = "row"

        # Populate table
        self._refresh_table()

        # Update status
        self._update_status(f"Found {len(self.file_items)} files")

    def _scan_workspace(self) -> None:
        """Scan workspace for agent/skill/instruction files."""
        # Get destination paths
        vscode_paths = detect_vscode_insiders_paths()
        agents_skills_path = detect_agents_skills_path()

        # Scan for agent files in agents/
        agents_dir = self.workspace_root / "agents"
        if agents_dir.exists():
            for agent_file in agents_dir.glob("*.agent.md"):
                dest = vscode_paths["prompts"] / agent_file.name
                status = compare_file_times(agent_file, dest)

                self.file_items.append(FileItem(
                    source=agent_file,
                    dest=dest,
                    status=status,
                    relative_source=f"agents/{agent_file.name}",
                    relative_dest=f"User/prompts/{agent_file.name}"
                ))

        # Scan for instruction files
        instructions_dir = self.workspace_root / "instructions"
        if instructions_dir.exists():
            for inst_file in instructions_dir.glob("*.instructions.md"):
                dest = vscode_paths["prompts"] / inst_file.name
                status = compare_file_times(inst_file, dest)

                self.file_items.append(FileItem(
                    source=inst_file,
                    dest=dest,
                    status=status,
                    relative_source=f"instructions/{inst_file.name}",
                    relative_dest=f"User/prompts/{inst_file.name}"
                ))

        # Scan for skill files
        skills_dir = self.workspace_root / "skills"
        if skills_dir.exists():
            for skill_file in skills_dir.rglob("SKILL.md"):
                # Calculate relative path for skill
                rel_path = skill_file.relative_to(skills_dir)
                dest = agents_skills_path / rel_path
                status = compare_file_times(skill_file, dest)

                self.file_items.append(FileItem(
                    source=skill_file,
                    dest=dest,
                    status=status,
                    relative_source=f"skills/{rel_path}",
                    relative_dest=f"~/.agents/skills/{rel_path}"
                ))

    def _refresh_table(self) -> None:
        """Refresh the file table display."""
        table = self.query_one("#file-table", DataTable)
        table.clear()

        for idx, item in enumerate(self.file_items):
            if not item.visible:
                continue

            # Selection indicator
            checkbox = "[X]" if item.selected else "[ ]"

            # Status indicator
            status_display = self._get_status_display(item.status)

            # Add row
            table.add_row(
                checkbox,
                item.relative_source,
                status_display,
                item.relative_dest,
                key=str(idx)
            )

    def _get_status_display(self, status: FileStatus) -> str:
        """Get display string for file status."""
        status_map = {
            FileStatus.SOURCE_NEWER: "🔼 Newer",
            FileStatus.SOURCE_OLDER: "🔽 Older",
            FileStatus.IDENTICAL: "✓ Identical",
            FileStatus.DEST_MISSING: "➕ New",
            FileStatus.SOURCE_MISSING: "❌ Missing",
            FileStatus.BOTH_MISSING: "❌ Both Missing",
        }
        return status_map.get(status, str(status))

    def _update_status(self, message: str, is_error: bool = False) -> None:
        """Update status bar message."""
        self.status_message = message
        label = self.query_one("#status-label", Label)
        label.update(message)

        if is_error:
            label.add_class("error-message")
            label.remove_class("status-message")
        else:
            label.add_class("status-message")
            label.remove_class("error-message")

    def _update_progress(self, current: int, total: int) -> None:
        """Update progress bar."""
        progress_bar = self.query_one("#progress-bar", ProgressBar)

        if total > 0:
            self.installation_progress = int((current / total) * 100)
            progress_bar.update(progress=current, total=total)
        else:
            self.installation_progress = 0
            progress_bar.update(progress=0, total=100)

    def _get_visible_items(self) -> List[FileItem]:
        """Get list of visible items."""
        return [item for item in self.file_items if item.visible]

    def _get_current_item(self) -> Optional[FileItem]:
        """Get currently selected item in the table."""
        visible_items = self._get_visible_items()
        if 0 <= self.selected_index < len(visible_items):
            return visible_items[self.selected_index]
        return None

    def action_toggle_selection(self) -> None:
        """Toggle selection of current file."""
        item = self._get_current_item()
        if item:
            item.selected = not item.selected
            self._refresh_table()

            selected_count = len([f for f in self.file_items if f.selected])
            self._update_status(f"{selected_count} files selected")

    def action_select_all(self) -> None:
        """Select all visible files."""
        visible_items = self._get_visible_items()
        for item in visible_items:
            item.selected = True

        self._refresh_table()
        self._update_status(f"All {len(visible_items)} files selected")

    def action_deselect_all(self) -> None:
        """Deselect all files."""
        for item in self.file_items:
            item.selected = False

        self._refresh_table()
        self._update_status("All files deselected")

    def action_filter_all(self) -> None:
        """Show all files."""
        self.current_filter = None
        for item in self.file_items:
            item.visible = True

        self.selected_index = 0
        self._refresh_table()
        self._update_status(f"Showing all {len(self.file_items)} files")

    def action_filter_agents(self) -> None:
        """Show only agent files."""
        self.current_filter = "agents"
        for item in self.file_items:
            item.visible = item.relative_source.endswith('.agent.md')

        self.selected_index = 0
        visible_count = len(self._get_visible_items())
        self._refresh_table()
        self._update_status(f"Showing {visible_count} agent files")

    def action_filter_skills(self) -> None:
        """Show only skill files."""
        self.current_filter = "skills"
        for item in self.file_items:
            item.visible = 'SKILL.md' in str(item.relative_source)

        self.selected_index = 0
        visible_count = len(self._get_visible_items())
        self._refresh_table()
        self._update_status(f"Showing {visible_count} skill files")

    def action_filter_instructions(self) -> None:
        """Show only instruction files."""
        self.current_filter = "instructions"
        for item in self.file_items:
            item.visible = item.relative_source.endswith('.instructions.md')

        self.selected_index = 0
        visible_count = len(self._get_visible_items())
        self._refresh_table()
        self._update_status(f"Showing {visible_count} instruction files")

    def action_show_diff(self) -> None:
        """Show diff for currently selected file."""
        item = self._get_current_item()
        if not item:
            self._update_status("No file selected", is_error=True)
            return

        self.selected_file = item
        diff_text = self._generate_diff(item)
        self.current_diff = diff_text

        diff_display = self.query_one("#diff-display", Static)
        diff_display.update(diff_text)

    def _generate_diff(self, item: FileItem) -> str:
        """Generate diff text for a file."""
        if item.status == FileStatus.DEST_MISSING:
            return f"[New File]\n\n{item.relative_source} → {item.relative_dest}\n\nThis file will be created."

        if item.status == FileStatus.IDENTICAL:
            return f"[No changes]\n\n{item.relative_source}\n\nFiles are identical."

        if item.status == FileStatus.SOURCE_OLDER:
            return f"[Older Source]\n\n{item.relative_source}\n\nSource is older than destination.\nRecommend skipping."

        if item.status == FileStatus.SOURCE_NEWER:
            # Use difflib to show real line-by-line differences
            try:
                if not item.dest.exists():
                    return f"[New File]\n\n{item.relative_source} → {item.relative_dest}\n\nDestination does not exist yet."

                # Read both files
                source_lines = item.source.read_text().splitlines(keepends=True)
                dest_lines = item.dest.read_text().splitlines(keepends=True)

                # Generate unified diff
                diff_lines = difflib.unified_diff(
                    dest_lines,
                    source_lines,
                    fromfile=f"installed/{item.dest.name}",
                    tofile=f"repository/{item.source.name}",
                    lineterm=''
                )

                diff_text = ''.join(diff_lines)

                if not diff_text:
                    return f"[No content changes]\n\n{item.relative_source}\n\nFiles differ only in metadata."

                return diff_text
            except Exception as e:
                return f"[Error generating diff]\n\n{item.relative_source}\n\nError: {str(e)}"

        return f"Status: {item.status}\n\n{item.relative_source} → {item.relative_dest}"

    def action_install(self) -> None:
        """Execute installation for selected files."""
        selected_files = [f for f in self.file_items if f.selected]

        if not selected_files:
            self._update_status("No files selected for installation", is_error=True)
            return

        self._update_status(f"Installing {len(selected_files)} files...")
        self._update_progress(0, len(selected_files))

        installed_count = 0
        errors = []

        # Centralized backup location: ~/.agents/backups
        backup_dir = get_user_home() / ".agents" / "backups"

        for idx, item in enumerate(selected_files):
            try:
                # Validate file type
                if not validate_file_type(item.source):
                    errors.append(f"Invalid file type: {item.relative_source}")
                    continue

                # YAML validation - read file and validate
                try:
                    content = item.source.read_text()
                    # Determine file type from extension
                    if item.source.name.endswith('.agent.md'):
                        file_type = '.agent.md'
                    elif item.source.name.endswith('.instructions.md'):
                        file_type = '.instructions.md'
                    elif item.source.name == 'SKILL.md':
                        file_type = 'SKILL.md'
                    else:
                        file_type = None

                    # Validate YAML frontmatter if file type is known
                    if file_type:
                        result = validate_file(content, file_type)
                        if result.status not in (ValidationStatus.VALID, ValidationStatus.NO_FRONTMATTER):
                            error_msg = f"YAML validation failed for {item.relative_source}: {', '.join(result.errors)}"
                            errors.append(error_msg)
                            continue
                except Exception as e:
                    errors.append(f"Failed to validate {item.relative_source}: {str(e)}")
                    continue

                # Create backup if destination exists and is being overwritten
                # Use try-except to handle race conditions
                try:
                    if item.dest.exists() and item.status == FileStatus.SOURCE_NEWER:
                        create_backup(item.dest, backup_dir)
                except Exception as e:
                    errors.append(f"Backup failed for {item.relative_source}: {str(e)}")
                    continue

                # Create destination directory
                item.dest.parent.mkdir(parents=True, exist_ok=True)

                # Copy file - wrapped in try-except to handle race conditions
                try:
                    shutil.copy2(item.source, item.dest)
                    installed_count += 1
                except IOError as e:
                    errors.append(f"Error installing {item.relative_source}: {str(e)}")
                    continue

                # Update progress
                self._update_progress(idx + 1, len(selected_files))

            except Exception as e:
                errors.append(f"Unexpected error with {item.relative_source}: {str(e)}")

        # Show final status
        if errors:
            error_msg = f"Installed {installed_count} files with {len(errors)} errors"
            self._update_status(error_msg, is_error=True)
        else:
            self._update_status(f"Successfully installed {installed_count} files!")

        # Reset progress
        self._update_progress(0, 100)

    def action_cursor_up(self) -> None:
        """Move cursor up in file list."""
        if self.selected_index > 0:
            self.selected_index -= 1
            table = self.query_one("#file-table", DataTable)
            table.move_cursor(row=self.selected_index)

    def action_cursor_down(self) -> None:
        """Move cursor down in file list."""
        visible_count = len(self._get_visible_items())
        if self.selected_index < visible_count - 1:
            self.selected_index += 1
            table = self.query_one("#file-table", DataTable)
            table.move_cursor(row=self.selected_index)

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()


def run_installer() -> None:
    """Run the interactive installer."""
    app = InstallerApp()
    app.run()


if __name__ == "__main__":
    run_installer()
