"""Tests for file sync logic and version checking."""

import os
import shutil
import time
from datetime import datetime
from pathlib import Path

import pytest

from cadence_installer.sync import (
    compare_file_times,
    create_backup,
    restore_backup,
    validate_file_type,
    FileStatus,
)


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for testing."""
    return tmp_path


@pytest.fixture
def backup_dir(tmp_path):
    """Create a backup directory for testing."""
    backup_path = tmp_path / "backups"
    backup_path.mkdir(exist_ok=True)
    return backup_path


class TestFileComparison:
    """Tests for file comparison by modification time."""

    def test_source_newer_than_destination(self, temp_dir):
        """Test when source file is newer than destination."""
        source = temp_dir / "source.agent.md"
        dest = temp_dir / "dest.agent.md"

        # Create destination first
        dest.write_text("old content")
        time.sleep(0.01)  # Ensure time difference

        # Create source after
        source.write_text("new content")

        status = compare_file_times(source, dest)
        assert status == FileStatus.SOURCE_NEWER

    def test_source_older_than_destination(self, temp_dir):
        """Test when source file is older than destination."""
        source = temp_dir / "source.agent.md"
        dest = temp_dir / "dest.agent.md"

        # Create source first
        source.write_text("old content")
        time.sleep(0.01)  # Ensure time difference

        # Create destination after
        dest.write_text("new content")

        status = compare_file_times(source, dest)
        assert status == FileStatus.SOURCE_OLDER

    def test_files_identical_mtime(self, temp_dir):
        """Test when files have identical modification times."""
        source = temp_dir / "source.agent.md"
        dest = temp_dir / "dest.agent.md"

        source.write_text("content")
        shutil.copy2(source, dest)  # copy2 preserves metadata including mtime

        status = compare_file_times(source, dest)
        assert status == FileStatus.IDENTICAL

    def test_source_missing(self, temp_dir):
        """Test when source file doesn't exist."""
        source = temp_dir / "nonexistent.agent.md"
        dest = temp_dir / "dest.agent.md"
        dest.write_text("content")

        status = compare_file_times(source, dest)
        assert status == FileStatus.SOURCE_MISSING

    def test_destination_missing(self, temp_dir):
        """Test when destination file doesn't exist."""
        source = temp_dir / "source.agent.md"
        dest = temp_dir / "nonexistent.agent.md"
        source.write_text("content")

        status = compare_file_times(source, dest)
        assert status == FileStatus.DEST_MISSING

    def test_both_missing(self, temp_dir):
        """Test when both files don't exist."""
        source = temp_dir / "nonexistent1.agent.md"
        dest = temp_dir / "nonexistent2.agent.md"

        status = compare_file_times(source, dest)
        assert status == FileStatus.BOTH_MISSING


class TestBackupManagement:
    """Tests for backup creation and restoration."""

    def test_create_backup_with_timestamp(self, temp_dir, backup_dir):
        """Test backup creation with correct timestamp format."""
        dest_file = temp_dir / "file.agent.md"
        dest_file.write_text("original content")

        backup_path = create_backup(dest_file, backup_dir)

        # Verify backup exists
        assert backup_path.exists()
        assert backup_path.read_text() == "original content"

        # Verify timestamp format: YYYY-MM-DD_HHMMSS_microseconds
        name_parts = backup_path.name.split(".")
        assert name_parts[0] == "file"
        assert name_parts[1] == "agent"
        assert name_parts[2] == "md"
        # Timestamp format: YYYY-MM-DD_HHMMSS_microseconds
        timestamp = name_parts[3]
        assert len(timestamp) == 24  # YYYY-MM-DD_HHMMSS_MMMMMM = 24 chars
        assert timestamp[4] == "-"
        assert timestamp[7] == "-"
        assert timestamp[10] == "_"
        assert timestamp[17] == "_"

        # Verify it can be parsed as a valid datetime
        datetime.strptime(timestamp, "%Y-%m-%d_%H%M%S_%f")

    def test_create_backup_directory_if_missing(self, temp_dir):
        """Test that backup directory is created if it doesn't exist."""
        dest_file = temp_dir / "file.agent.md"
        dest_file.write_text("content")

        backup_dir = temp_dir / "backups"
        assert not backup_dir.exists()

        backup_path = create_backup(dest_file, backup_dir)

        assert backup_dir.exists()
        assert backup_path.exists()

    def test_backup_preserves_content(self, temp_dir, backup_dir):
        """Test that backup preserves exact file content."""
        dest_file = temp_dir / "file.instructions.md"
        original_content = "Important content\nWith multiple lines\n"
        dest_file.write_text(original_content)

        backup_path = create_backup(dest_file, backup_dir)

        assert backup_path.read_text() == original_content

    def test_restore_backup(self, temp_dir, backup_dir):
        """Test backup restoration."""
        dest_file = temp_dir / "file.agent.md"
        dest_file.write_text("original")

        backup_path = create_backup(dest_file, backup_dir)

        # Modify destination
        dest_file.write_text("modified")
        assert dest_file.read_text() == "modified"

        # Restore backup
        restore_backup(backup_path, dest_file)

        assert dest_file.read_text() == "original"

    def test_restore_backup_creates_parent_dir(self, temp_dir, backup_dir):
        """Test that restore creates parent directory if needed."""
        dest_file = temp_dir / "subdir" / "file.agent.md"

        # Create backup from a temporary file
        temp_file = temp_dir / "temp.agent.md"
        temp_file.write_text("content")
        backup_path = create_backup(temp_file, backup_dir)

        # Restore to location where parent doesn't exist
        assert not dest_file.parent.exists()
        restore_backup(backup_path, dest_file)

        assert dest_file.exists()
        assert dest_file.read_text() == "content"


class TestFileTypeValidation:
    """Tests for file type validation."""

    def test_valid_agent_md_file(self):
        """Test .agent.md files are valid."""
        assert validate_file_type(Path("Builder.agent.md")) is True

    def test_valid_instructions_md_file(self):
        """Test .instructions.md files are valid."""
        assert validate_file_type(Path("Initialize.instructions.md")) is True

    def test_valid_skill_md_file(self):
        """Test SKILL.md files are valid."""
        assert validate_file_type(Path("SKILL.md")) is True

    def test_valid_skill_md_with_path(self):
        """Test SKILL.md files with path are valid."""
        assert validate_file_type(Path("skills/tdd-workflow/SKILL.md")) is True

    def test_invalid_regular_md_file(self):
        """Test regular .md files are invalid."""
        assert validate_file_type(Path("README.md")) is False

    def test_invalid_txt_file(self):
        """Test .txt files are invalid."""
        assert validate_file_type(Path("file.txt")) is False

    def test_invalid_no_extension(self):
        """Test files without extension are invalid."""
        assert validate_file_type(Path("file")) is False

    def test_invalid_py_file(self):
        """Test .py files are invalid."""
        assert validate_file_type(Path("sync.py")) is False
