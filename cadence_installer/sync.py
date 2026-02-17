"""File sync logic and version checking."""

import shutil
from datetime import datetime
from enum import Enum
from pathlib import Path


class FileStatus(Enum):
    """File comparison status."""
    SOURCE_NEWER = "source_newer"
    SOURCE_OLDER = "source_older"
    IDENTICAL = "identical"
    SOURCE_MISSING = "source_missing"
    DEST_MISSING = "dest_missing"
    BOTH_MISSING = "both_missing"


def compare_file_times(source: Path, dest: Path) -> FileStatus:
    """Compare modification times of source and destination files.

    Args:
        source: Source file path
        dest: Destination file path

    Returns:
        FileStatus indicating the relationship between files
    """
    source_exists = source.exists()
    dest_exists = dest.exists()

    if not source_exists and not dest_exists:
        return FileStatus.BOTH_MISSING
    if not source_exists:
        return FileStatus.SOURCE_MISSING
    if not dest_exists:
        return FileStatus.DEST_MISSING

    # Handle race condition: file could be deleted between exists() and stat()
    try:
        source_mtime = source.stat().st_mtime
        dest_mtime = dest.stat().st_mtime
    except FileNotFoundError:
        # File was deleted after exists() check - re-evaluate
        source_exists = source.exists()
        dest_exists = dest.exists()
        if not source_exists and not dest_exists:
            return FileStatus.BOTH_MISSING
        if not source_exists:
            return FileStatus.SOURCE_MISSING
        if not dest_exists:
            return FileStatus.DEST_MISSING
        # If we still can't stat, raise the error
        raise

    if source_mtime > dest_mtime:
        return FileStatus.SOURCE_NEWER
    elif source_mtime < dest_mtime:
        return FileStatus.SOURCE_OLDER
    else:
        return FileStatus.IDENTICAL


def create_backup(dest_file: Path, backup_dir: Path) -> Path:
    """Create a timestamped backup of the destination file.

    Args:
        dest_file: File to backup
        backup_dir: Directory to store backups

    Returns:
        Path to the created backup file
    """
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Include microseconds to avoid collisions
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S_%f")

    # Build backup filename: original_name.timestamp.bak
    # e.g., file.agent.md -> file.agent.md.2026-02-17_143020.bak
    backup_name = f"{dest_file.name}.{timestamp}.bak"
    backup_path = backup_dir / backup_name

    shutil.copy2(dest_file, backup_path)

    return backup_path


def restore_backup(backup_path: Path, dest_file: Path) -> None:
    """Restore a backup file to its original location.

    Args:
        backup_path: Path to the backup file
        dest_file: Destination path to restore to
    """
    dest_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(backup_path, dest_file)


def validate_file_type(file_path: Path) -> bool:
    """Validate that file has an accepted extension.

    Accepted extensions:
    - .agent.md
    - .instructions.md
    - SKILL.md (filename)

    Args:
        file_path: File path to validate

    Returns:
        True if file type is valid, False otherwise
    """
    name = file_path.name

    # Check for SKILL.md
    if name == "SKILL.md":
        return True

    # Check for .agent.md
    if name.endswith(".agent.md"):
        return True

    # Check for .instructions.md
    if name.endswith(".instructions.md"):
        return True

    return False
