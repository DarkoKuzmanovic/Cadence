"""CLI commands for status reporting and uninstall functionality."""

import argparse
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional

from rich.console import Console
from rich.table import Table
from rich import box

from cadence_installer.config import detect_vscode_insiders_paths, detect_agents_skills_path
from cadence_installer.sync import (
    compare_file_times,
    create_backup,
    restore_backup,
    validate_file_type,
    FileStatus,
)


console = Console()


class FileState(Enum):
    """File installation state."""
    UP_TO_DATE = "up-to-date"
    NEWER_AVAILABLE = "newer_available"
    LOCAL_CHANGES = "local_changes"
    NOT_INSTALLED = "not_installed"
    ORPHANED = "orphaned"


@dataclass
class FileInfo:
    """Information about a file's installation status."""
    name: str
    path: Path
    state: FileState
    installed_version: Optional[str] = None
    repo_version: Optional[str] = None


def get_repo_files(workspace: Path) -> List[FileInfo]:
    """Get all valid repository files (agents, instructions, skills).

    Args:
        workspace: Path to the workspace directory

    Returns:
        List of FileInfo objects for repo files
    """
    repo_files = []

    if not workspace.exists():
        return repo_files

    # Find .agent.md files
    for agent_file in workspace.glob("*.agent.md"):
        if validate_file_type(agent_file):
            version = _format_mtime(agent_file)
            repo_files.append(
                FileInfo(
                    name=agent_file.name,
                    path=agent_file,
                    state=FileState.NOT_INSTALLED,
                    installed_version=None,
                    repo_version=version,
                )
            )

    # Find .instructions.md files in instructions/
    instructions_dir = workspace / "instructions"
    if instructions_dir.exists():
        for inst_file in instructions_dir.glob("*.instructions.md"):
            if validate_file_type(inst_file):
                version = _format_mtime(inst_file)
                repo_files.append(
                    FileInfo(
                        name=inst_file.name,
                        path=inst_file,
                        state=FileState.NOT_INSTALLED,
                        installed_version=None,
                        repo_version=version,
                    )
                )

    # Find SKILL.md files in skills/
    skills_dir = workspace / "skills"
    if skills_dir.exists():
        for skill_file in skills_dir.rglob("SKILL.md"):
            if validate_file_type(skill_file):
                version = _format_mtime(skill_file)
                repo_files.append(
                    FileInfo(
                        name=skill_file.name,
                        path=skill_file,
                        state=FileState.NOT_INSTALLED,
                        installed_version=None,
                        repo_version=version,
                    )
                )

    return repo_files


def get_installed_files(prompts_dir: Path, skills_dir: Path) -> List[FileInfo]:
    """Get all installed files from VS Code directories.

    Args:
        prompts_dir: Path to User/prompts directory
        skills_dir: Path to User/skills or .agents/skills directory

    Returns:
        List of FileInfo objects for installed files
    """
    installed_files = []

    # Get files from prompts directory
    if prompts_dir.exists():
        for file_path in prompts_dir.iterdir():
            if file_path.is_file() and validate_file_type(file_path):
                version = _format_mtime(file_path)
                installed_files.append(
                    FileInfo(
                        name=file_path.name,
                        path=file_path,
                        state=FileState.ORPHANED,
                        installed_version=version,
                        repo_version=None,
                    )
                )

    # Get SKILL.md files from skills directory
    if skills_dir.exists():
        for skill_file in skills_dir.rglob("SKILL.md"):
            if validate_file_type(skill_file):
                version = _format_mtime(skill_file)
                installed_files.append(
                    FileInfo(
                        name=skill_file.name,
                        path=skill_file,
                        state=FileState.ORPHANED,
                        installed_version=version,
                        repo_version=None,
                    )
                )

    return installed_files


def status_command(workspace: Path, dry_run: bool = False) -> List[FileInfo]:
    """Execute status command to show file sync status.

    Args:
        workspace: Path to workspace directory
        dry_run: If True, don't actually check files (for testing)

    Returns:
        List of FileInfo objects with sync status (only installed files)
    """
    # Get installation paths
    vscode_paths = detect_vscode_insiders_paths()
    prompts_dir = vscode_paths["prompts"]
    # Use centralized skills path instead of User/skills
    skills_dir = detect_agents_skills_path()

    # Get repo files
    repo_files = get_repo_files(workspace)

    # Get installed files
    installed_files = get_installed_files(prompts_dir, skills_dir)

    # Build a map of installed files
    # For skills, use path comparison since names are all "SKILL.md"
    # For other files, use name comparison
    installed_map = {}
    installed_skills_map = {}

    for f in installed_files:
        if f.name == "SKILL.md":
            # Map by skill name (parent directory)
            skill_name = f.path.parent.name
            installed_skills_map[skill_name] = f
        else:
            installed_map[f.name] = f

    # Compare and determine status
    result = []

    for repo_file in repo_files:
        if repo_file.name == "SKILL.md":
            # Handle skill files specially
            skill_name = repo_file.path.parent.name

            if skill_name in installed_skills_map:
                installed = installed_skills_map[skill_name]
                installed_path = installed.path

                # Compare files
                status = compare_file_times(repo_file.path, installed_path)

                if status == FileStatus.IDENTICAL:
                    state = FileState.UP_TO_DATE
                elif status == FileStatus.SOURCE_NEWER:
                    state = FileState.NEWER_AVAILABLE
                elif status == FileStatus.SOURCE_OLDER:
                    state = FileState.LOCAL_CHANGES
                else:
                    state = FileState.NOT_INSTALLED

                result.append(
                    FileInfo(
                        name=repo_file.name,
                        path=repo_file.path,
                        state=state,
                        installed_version=installed.installed_version,
                        repo_version=repo_file.repo_version,
                    )
                )

                # Remove from map since we matched it
                del installed_skills_map[skill_name]
            # Skip NOT_INSTALLED files

        elif repo_file.name in installed_map:
            installed = installed_map[repo_file.name]

            # Determine installed path based on file type
            if repo_file.name.endswith(".agent.md") or repo_file.name.endswith(".instructions.md"):
                installed_path = prompts_dir / repo_file.name
            else:
                continue

            # Compare files
            status = compare_file_times(repo_file.path, installed_path)

            if status == FileStatus.IDENTICAL:
                state = FileState.UP_TO_DATE
            elif status == FileStatus.SOURCE_NEWER:
                state = FileState.NEWER_AVAILABLE
            elif status == FileStatus.SOURCE_OLDER:
                state = FileState.LOCAL_CHANGES
            elif status == FileStatus.DEST_MISSING:
                state = FileState.NOT_INSTALLED
            else:
                state = FileState.NOT_INSTALLED

            result.append(
                FileInfo(
                    name=repo_file.name,
                    path=repo_file.path,
                    state=state,
                    installed_version=installed.installed_version,
                    repo_version=repo_file.repo_version,
                )
            )

            # Remove from installed_map since we matched it
            del installed_map[repo_file.name]
        # Skip NOT_INSTALLED files

    # Add any orphaned installed files (no matching repo file)
    for orphaned in installed_map.values():
        result.append(orphaned)

    for orphaned in installed_skills_map.values():
        result.append(orphaned)

    return result


def format_status_table(file_infos: List[FileInfo]) -> str:
    """Format file status information as a table.

    Args:
        file_infos: List of FileInfo objects

    Returns:
        Formatted table as string
    """
    if not file_infos:
        return "No files found"

    table = Table(box=box.SIMPLE)
    table.add_column("File", style="cyan", no_wrap=False)
    table.add_column("Status", style="magenta")
    table.add_column("Installed", style="yellow")
    table.add_column("Repository", style="green")

    # Count states for summary
    state_counts = {
        FileState.UP_TO_DATE: 0,
        FileState.NEWER_AVAILABLE: 0,
        FileState.LOCAL_CHANGES: 0,
        FileState.NOT_INSTALLED: 0,
        FileState.ORPHANED: 0,
    }

    for file_info in file_infos:
        state_counts[file_info.state] += 1

        # Color code status
        if file_info.state == FileState.UP_TO_DATE:
            status_str = "[green]✓ Up-to-date[/green]"
        elif file_info.state == FileState.NEWER_AVAILABLE:
            status_str = "[yellow]↓ Update available[/yellow]"
        elif file_info.state == FileState.LOCAL_CHANGES:
            status_str = "[blue]↑ Local changes[/blue]"
        elif file_info.state == FileState.NOT_INSTALLED:
            status_str = "[red]✗ Not installed[/red]"
        elif file_info.state == FileState.ORPHANED:
            status_str = "[dim]? Orphaned[/dim]"
        else:
            status_str = str(file_info.state.value)

        installed_ver = file_info.installed_version or "-"
        repo_ver = file_info.repo_version or "-"

        table.add_row(
            file_info.name,
            status_str,
            installed_ver,
            repo_ver,
        )

    # Render table to string
    from io import StringIO
    string_io = StringIO()
    temp_console = Console(file=string_io, force_terminal=True)
    temp_console.print(table)

    # Add summary line
    summary_parts = []
    if state_counts[FileState.UP_TO_DATE] > 0:
        summary_parts.append(f"{state_counts[FileState.UP_TO_DATE]} up-to-date")
    if state_counts[FileState.NEWER_AVAILABLE] > 0:
        summary_parts.append(f"{state_counts[FileState.NEWER_AVAILABLE]} updates available")
    if state_counts[FileState.LOCAL_CHANGES] > 0:
        summary_parts.append(f"{state_counts[FileState.LOCAL_CHANGES]} local changes")
    if state_counts[FileState.ORPHANED] > 0:
        summary_parts.append(f"{state_counts[FileState.ORPHANED]} orphaned")

    summary = f"\n{len(file_infos)} files total"
    if summary_parts:
        summary += f": {', '.join(summary_parts)}"
    temp_console.print(summary)

    return string_io.getvalue()


def uninstall_command(
    files: List[Path],
    backup_dir: Path,
    dry_run: bool = False,
    skip_confirm: bool = False,
    restore: bool = False,
) -> Dict[str, int]:
    """Execute uninstall command to remove or restore files.

    Args:
        files: List of file paths to uninstall or restore
        backup_dir: Directory for backups
        dry_run: If True, show what would happen without executing
        skip_confirm: If True, skip confirmation prompt
        restore: If True, restore from backup instead of removing

    Returns:
        Dictionary with counts of operations performed
    """
    result = {
        "removed": 0,
        "restored": 0,
        "errors": 0,
        "would_remove": 0,
    }

    if restore:
        # Restore mode: restore files from backups
        for file_path in files:
            # Find most recent backup for this file
            backup_files = list(backup_dir.glob(f"{file_path.name}.*"))

            if not backup_files:
                console.print(f"[red]No backup found for {file_path.name}[/red]")
                result["errors"] += 1
                continue

            # Sort by modification time (most recent first)
            backup_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            most_recent_backup = backup_files[0]

            if dry_run:
                console.print(f"[dim]Would restore {file_path.name} from {most_recent_backup.name}[/dim]")
                result["would_remove"] += 1
            else:
                try:
                    restore_backup(most_recent_backup, file_path)
                    console.print(f"[green]✓ Restored {file_path.name}[/green]")
                    result["restored"] += 1
                except Exception as e:
                    console.print(f"[red]Error restoring {file_path.name}: {e}[/red]")
                    result["errors"] += 1

        return result

    # Remove mode: remove files with backup
    if not skip_confirm and not dry_run:
        console.print(f"\n[yellow]About to remove {len(files)} file(s):[/yellow]")
        for file_path in files:
            console.print(f"  - {file_path.name}")

        response = input("\nProceed? (y/n): ").strip().lower()
        if response != "y":
            console.print("[dim]Aborted.[/dim]")
            return result

    for file_path in files:
        if not file_path.exists():
            continue

        if dry_run:
            console.print(f"[dim]Would remove {file_path.name}[/dim]")
            result["would_remove"] += 1
        else:
            try:
                # Create backup before removing
                create_backup(file_path, backup_dir)

                # Remove the file
                file_path.unlink()

                console.print(f"[green]✓ Removed {file_path.name}[/green]")
                result["removed"] += 1
            except Exception as e:
                console.print(f"[red]Error removing {file_path.name}: {e}[/red]")
                result["errors"] += 1

    return result


def _format_mtime(file_path: Path) -> str:
    """Format file modification time as readable string.

    Args:
        file_path: Path to file

    Returns:
        Formatted timestamp string
    """
    if not file_path.exists():
        return ""

    mtime = file_path.stat().st_mtime
    dt = datetime.fromtimestamp(mtime)
    return dt.strftime("%Y-%m-%d %H:%M")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Cadence installer CLI - manage agent and skill files"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show installation status")
    status_parser.add_argument(
        "workspace",
        type=Path,
        nargs="?",
        default=Path.cwd(),
        help="Workspace directory (default: current directory)",
    )
    status_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be checked without actually checking",
    )

    # Uninstall command
    uninstall_parser = subparsers.add_parser("uninstall", help="Uninstall files")
    uninstall_parser.add_argument(
        "files",
        type=Path,
        nargs="+",
        help="Files to uninstall",
    )
    uninstall_parser.add_argument(
        "--restore",
        action="store_true",
        help="Restore files from backup instead of removing",
    )
    uninstall_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without executing",
    )
    uninstall_parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompt",
    )
    uninstall_parser.add_argument(
        "--backup-dir",
        type=Path,
        default=Path.home() / ".agents" / "backups",
        help="Backup directory (default: ~/.agents/backups)",
    )

    args = parser.parse_args()

    if args.command == "status":
        file_infos = status_command(args.workspace, dry_run=args.dry_run)
        output = format_status_table(file_infos)
        console.print(output)

    elif args.command == "uninstall":
        result = uninstall_command(
            args.files,
            backup_dir=args.backup_dir,
            dry_run=args.dry_run,
            skip_confirm=args.yes,
            restore=args.restore,
        )

        if args.dry_run:
            console.print(f"\n[dim]Dry run: {result['would_remove']} file(s) would be affected[/dim]")
        else:
            if result["removed"] > 0:
                console.print(f"\n[green]Removed {result['removed']} file(s)[/green]")
            if result["restored"] > 0:
                console.print(f"\n[green]Restored {result['restored']} file(s)[/green]")
            if result["errors"] > 0:
                console.print(f"\n[red]{result['errors']} error(s) occurred[/red]")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
