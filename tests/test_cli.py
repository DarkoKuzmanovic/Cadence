"""Tests for CLI commands (status, uninstall)."""

import shutil
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO

import pytest

from cadence_installer.cli import (
    status_command,
    uninstall_command,
    format_status_table,
    get_installed_files,
    get_repo_files,
    FileInfo,
    FileState,
)
from cadence_installer.config import detect_agents_skills_path


@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace with repo files."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    # Create repo agent files in agents/ subdirectory
    agents_dir = workspace / "agents"
    agents_dir.mkdir()
    (agents_dir / "Builder.agent.md").write_text("# Builder")
    (agents_dir / "Scout.agent.md").write_text("# Scout")

    # Create repo instruction files
    instructions_dir = workspace / "instructions"
    instructions_dir.mkdir()
    (instructions_dir / "Initialize.instructions.md").write_text("# Init")

    # Create repo skill files
    skills_dir = workspace / "skills"
    tdd_skill = skills_dir / "tdd-workflow"
    tdd_skill.mkdir(parents=True)
    (tdd_skill / "SKILL.md").write_text("# TDD")

    return workspace


@pytest.fixture
def temp_install_dir(tmp_path):
    """Create a temporary installation directory."""
    install_dir = tmp_path / "install"
    prompts_dir = install_dir / "prompts"
    skills_dir = install_dir / "skills"
    prompts_dir.mkdir(parents=True)
    skills_dir.mkdir(parents=True)

    return {
        "prompts": prompts_dir,
        "skills": skills_dir,
    }


@pytest.fixture
def temp_backup_dir(tmp_path):
    """Create a temporary backup directory."""
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    return backup_dir


class TestGetRepoFiles:
    """Tests for getting repository files."""

    def test_get_repo_files_finds_agents(self, temp_workspace):
        """Test finding .agent.md files in workspace."""
        files = get_repo_files(temp_workspace)

        agent_files = [f for f in files if f.name.endswith(".agent.md")]
        assert len(agent_files) == 2
        assert any(f.name == "Builder.agent.md" for f in agent_files)
        assert any(f.name == "Scout.agent.md" for f in agent_files)

    def test_get_repo_files_finds_instructions(self, temp_workspace):
        """Test finding .instructions.md files in workspace."""
        files = get_repo_files(temp_workspace)

        instruction_files = [f for f in files if f.name.endswith(".instructions.md")]
        assert len(instruction_files) == 1
        assert instruction_files[0].name == "Initialize.instructions.md"

    def test_get_repo_files_finds_skills(self, temp_workspace):
        """Test finding SKILL.md files in workspace."""
        files = get_repo_files(temp_workspace)

        skill_files = [f for f in files if f.name == "SKILL.md"]
        assert len(skill_files) == 1
        assert "tdd-workflow" in str(skill_files[0].path)

    def test_get_repo_files_empty_workspace(self, tmp_path):
        """Test empty workspace returns empty list."""
        empty_workspace = tmp_path / "empty"
        empty_workspace.mkdir()

        files = get_repo_files(empty_workspace)
        assert files == []


class TestGetInstalledFiles:
    """Tests for getting installed files."""

    def test_get_installed_files_in_prompts(self, temp_install_dir):
        """Test finding installed files in prompts directory."""
        prompts_dir = temp_install_dir["prompts"]
        skills_dir = temp_install_dir["skills"]

        (prompts_dir / "Builder.agent.md").write_text("# Builder")
        (prompts_dir / "Initialize.instructions.md").write_text("# Init")

        files = get_installed_files(prompts_dir, skills_dir)

        assert len(files) == 2
        assert any(f.name == "Builder.agent.md" for f in files)
        assert any(f.name == "Initialize.instructions.md" for f in files)

    def test_get_installed_files_in_skills(self, temp_install_dir):
        """Test finding installed files in skills directory."""
        prompts_dir = temp_install_dir["prompts"]
        skills_dir = temp_install_dir["skills"]

        tdd_skill = skills_dir / "tdd-workflow"
        tdd_skill.mkdir(parents=True)
        (tdd_skill / "SKILL.md").write_text("# TDD")

        files = get_installed_files(prompts_dir, skills_dir)

        skill_files = [f for f in files if f.name == "SKILL.md"]
        assert len(skill_files) == 1
        assert "tdd-workflow" in str(skill_files[0].path)

    def test_get_installed_files_empty_directories(self, temp_install_dir):
        """Test empty directories return empty list."""
        prompts_dir = temp_install_dir["prompts"]
        skills_dir = temp_install_dir["skills"]

        files = get_installed_files(prompts_dir, skills_dir)
        assert files == []


class TestStatusCommand:
    """Tests for status command."""

    def test_status_shows_up_to_date_files(self, temp_workspace, temp_install_dir):
        """Test status shows files that are up-to-date."""
        prompts_dir = temp_install_dir["prompts"]
        skills_dir = temp_install_dir["skills"]

        # Copy file from workspace/agents to install dir
        repo_file = temp_workspace / "agents" / "Builder.agent.md"
        installed_file = prompts_dir / "Builder.agent.md"
        shutil.copy2(repo_file, installed_file)

        with patch('cadence_installer.cli.detect_vscode_insiders_paths', return_value=temp_install_dir), \
             patch('cadence_installer.cli.detect_agents_skills_path', return_value=skills_dir):
            result = status_command(temp_workspace, dry_run=False)

        assert len(result) == 1
        assert result[0].name == "Builder.agent.md"
        assert result[0].state == FileState.UP_TO_DATE

    def test_status_shows_newer_available(self, temp_workspace, temp_install_dir):
        """Test status shows when newer version is available."""
        prompts_dir = temp_install_dir["prompts"]
        skills_dir = temp_install_dir["skills"]

        # Create installed file first (older)
        installed_file = prompts_dir / "Builder.agent.md"
        installed_file.write_text("# Old Builder")
        time.sleep(0.01)

        # Update repo file (newer)
        repo_file = temp_workspace / "agents" / "Builder.agent.md"
        repo_file.write_text("# New Builder")

        with patch('cadence_installer.cli.detect_vscode_insiders_paths', return_value=temp_install_dir), \
             patch('cadence_installer.cli.detect_agents_skills_path', return_value=skills_dir):
            result = status_command(temp_workspace, dry_run=False)

        assert len(result) == 1
        assert result[0].name == "Builder.agent.md"
        assert result[0].state == FileState.NEWER_AVAILABLE

    def test_status_shows_local_changes(self, temp_workspace, temp_install_dir):
        """Test status shows when local changes exist."""
        prompts_dir = temp_install_dir["prompts"]
        skills_dir = temp_install_dir["skills"]

        # Create repo file first
        repo_file = temp_workspace / "agents" / "Builder.agent.md"
        repo_file.write_text("# Original")
        time.sleep(0.01)

        # Create newer installed file (local changes)
        installed_file = prompts_dir / "Builder.agent.md"
        installed_file.write_text("# Modified locally")

        with patch('cadence_installer.cli.detect_vscode_insiders_paths', return_value=temp_install_dir), \
             patch('cadence_installer.cli.detect_agents_skills_path', return_value=skills_dir):
            result = status_command(temp_workspace, dry_run=False)

        assert len(result) == 1
        assert result[0].name == "Builder.agent.md"
        assert result[0].state == FileState.LOCAL_CHANGES

    def test_status_shows_not_installed(self, temp_workspace, temp_install_dir):
        """Test status shows files that are not installed."""
        skills_dir = temp_install_dir["skills"]

        with patch('cadence_installer.cli.detect_vscode_insiders_paths', return_value=temp_install_dir), \
             patch('cadence_installer.cli.detect_agents_skills_path', return_value=skills_dir):
            result = status_command(temp_workspace, dry_run=False)

        # No repo files should be shown since none are installed
        assert len(result) == 0

    def test_status_handles_missing_files(self, temp_workspace, temp_install_dir):
        """Test status handles missing files gracefully."""
        prompts_dir = temp_install_dir["prompts"]
        skills_dir = temp_install_dir["skills"]

        # Create installed file with no corresponding repo file
        (prompts_dir / "Orphan.agent.md").write_text("# Orphan")

        with patch('cadence_installer.cli.detect_vscode_insiders_paths', return_value=temp_install_dir), \
             patch('cadence_installer.cli.detect_agents_skills_path', return_value=skills_dir):
            result = status_command(temp_workspace, dry_run=False)

        # Should handle missing repo file gracefully
        orphan = [f for f in result if f.name == "Orphan.agent.md"]
        assert len(orphan) == 1
        assert orphan[0].state == FileState.ORPHANED


class TestFormatStatusTable:
    """Tests for status table formatting."""

    def test_format_status_table_basic(self):
        """Test basic table formatting."""
        file_infos = [
            FileInfo(
                name="Builder.agent.md",
                path=Path("/workspace/Builder.agent.md"),
                state=FileState.UP_TO_DATE,
                installed_version="2026-02-17 14:30",
                repo_version="2026-02-17 14:30",
            ),
        ]

        output = format_status_table(file_infos)

        assert "Builder.agent.md" in output
        assert "UP_TO_DATE" in output or "up-to-date" in output.lower()

    def test_format_status_table_multiple_states(self):
        """Test table with multiple file states."""
        file_infos = [
            FileInfo(
                name="Builder.agent.md",
                path=Path("/workspace/Builder.agent.md"),
                state=FileState.UP_TO_DATE,
                installed_version="2026-02-17 14:30",
                repo_version="2026-02-17 14:30",
            ),
            FileInfo(
                name="Scout.agent.md",
                path=Path("/workspace/Scout.agent.md"),
                state=FileState.NEWER_AVAILABLE,
                installed_version="2026-02-17 14:00",
                repo_version="2026-02-17 14:30",
            ),
            FileInfo(
                name="Critic.agent.md",
                path=Path("/workspace/Critic.agent.md"),
                state=FileState.NOT_INSTALLED,
                installed_version=None,
                repo_version="2026-02-17 14:30",
            ),
        ]

        output = format_status_table(file_infos)

        assert "Builder.agent.md" in output
        assert "Scout.agent.md" in output
        assert "Critic.agent.md" in output

    def test_format_status_table_empty_list(self):
        """Test formatting empty file list."""
        output = format_status_table([])

        assert "No files found" in output or len(output.strip()) == 0

    def test_format_status_table_includes_summary(self):
        """Test table includes summary line with counts."""
        file_infos = [
            FileInfo(
                name="Builder.agent.md",
                path=Path("/workspace/Builder.agent.md"),
                state=FileState.UP_TO_DATE,
                installed_version="2026-02-17 14:30",
                repo_version="2026-02-17 14:30",
            ),
            FileInfo(
                name="Scout.agent.md",
                path=Path("/workspace/Scout.agent.md"),
                state=FileState.NEWER_AVAILABLE,
                installed_version="2026-02-17 14:00",
                repo_version="2026-02-17 14:30",
            ),
            FileInfo(
                name="Orphan.agent.md",
                path=Path("/installed/Orphan.agent.md"),
                state=FileState.ORPHANED,
                installed_version="2026-02-17 14:30",
                repo_version=None,
            ),
        ]

        output = format_status_table(file_infos)

        # Should contain summary with total count
        assert "3 file" in output.lower() or "total" in output.lower()


class TestSkillsPathConsistency:
    """Tests for skills path consistency between CLI and TUI."""

    def test_status_uses_agents_skills_path(self, temp_workspace, temp_install_dir):
        """Test status command uses ~/.agents/skills for skills."""
        # Create skill in workspace
        skills_dir = temp_workspace / "skills"
        tdd_skill = skills_dir / "tdd-workflow"
        tdd_skill.mkdir(parents=True, exist_ok=True)
        (tdd_skill / "SKILL.md").write_text("# TDD")

        # Create .agents/skills directory
        agents_skills_dir = temp_install_dir["skills"]
        agents_skills_dir.mkdir(parents=True, exist_ok=True)

        # Copy skill to .agents/skills
        dest_skill = agents_skills_dir / "tdd-workflow"
        dest_skill.mkdir(parents=True, exist_ok=True)
        shutil.copy2(tdd_skill / "SKILL.md", dest_skill / "SKILL.md")

        # Mock both paths to use temp dirs
        with patch('cadence_installer.cli.detect_vscode_insiders_paths', return_value={"prompts": temp_install_dir["prompts"], "skills": temp_install_dir["skills"]}), \
             patch('cadence_installer.cli.detect_agents_skills_path', return_value=agents_skills_dir):
            result = status_command(temp_workspace, dry_run=False)

        # Should find the skill file
        skill_files = [f for f in result if f.name == "SKILL.md"]
        assert len(skill_files) == 1
        assert skill_files[0].state == FileState.UP_TO_DATE


class TestUninstallCommand:
    """Tests for uninstall command."""

    def test_uninstall_removes_files(self, temp_workspace, temp_install_dir, temp_backup_dir):
        """Test uninstall removes installed files."""
        prompts_dir = temp_install_dir["prompts"]

        # Create installed files
        (prompts_dir / "Builder.agent.md").write_text("# Builder")
        (prompts_dir / "Scout.agent.md").write_text("# Scout")

        files_to_remove = [
            prompts_dir / "Builder.agent.md",
            prompts_dir / "Scout.agent.md",
        ]

        # Mock user confirmation
        with patch('builtins.input', return_value='y'):
            result = uninstall_command(
                files_to_remove,
                backup_dir=temp_backup_dir,
                dry_run=False,
                skip_confirm=False,
                restore=False
            )

        assert result["removed"] == 2
        assert not (prompts_dir / "Builder.agent.md").exists()
        assert not (prompts_dir / "Scout.agent.md").exists()

    def test_uninstall_with_confirmation_yes(self, temp_workspace, temp_install_dir, temp_backup_dir):
        """Test uninstall proceeds when user confirms with 'y'."""
        prompts_dir = temp_install_dir["prompts"]
        (prompts_dir / "Builder.agent.md").write_text("# Builder")

        files_to_remove = [prompts_dir / "Builder.agent.md"]

        with patch('builtins.input', return_value='y'):
            result = uninstall_command(
                files_to_remove,
                backup_dir=temp_backup_dir,
                dry_run=False,
                skip_confirm=False,
                restore=False
            )

        assert result["removed"] == 1
        assert not (prompts_dir / "Builder.agent.md").exists()

    def test_uninstall_with_confirmation_no(self, temp_workspace, temp_install_dir, temp_backup_dir):
        """Test uninstall aborts when user declines with 'n'."""
        prompts_dir = temp_install_dir["prompts"]
        (prompts_dir / "Builder.agent.md").write_text("# Builder")

        files_to_remove = [prompts_dir / "Builder.agent.md"]

        with patch('builtins.input', return_value='n'):
            result = uninstall_command(
                files_to_remove,
                backup_dir=temp_backup_dir,
                dry_run=False,
                skip_confirm=False,
                restore=False
            )

        assert result["removed"] == 0
        assert (prompts_dir / "Builder.agent.md").exists()

    def test_uninstall_skip_confirmation(self, temp_workspace, temp_install_dir, temp_backup_dir):
        """Test uninstall with --yes flag skips confirmation."""
        prompts_dir = temp_install_dir["prompts"]
        (prompts_dir / "Builder.agent.md").write_text("# Builder")

        files_to_remove = [prompts_dir / "Builder.agent.md"]

        result = uninstall_command(
            files_to_remove,
            backup_dir=temp_backup_dir,
            dry_run=False,
            skip_confirm=True,
            restore=False
        )

        assert result["removed"] == 1
        assert not (prompts_dir / "Builder.agent.md").exists()

    def test_uninstall_creates_backup(self, temp_workspace, temp_install_dir, temp_backup_dir):
        """Test uninstall creates backup before removing."""
        prompts_dir = temp_install_dir["prompts"]
        (prompts_dir / "Builder.agent.md").write_text("# Builder Content")

        files_to_remove = [prompts_dir / "Builder.agent.md"]

        with patch('builtins.input', return_value='y'):
            result = uninstall_command(
                files_to_remove,
                backup_dir=temp_backup_dir,
                dry_run=False,
                skip_confirm=False,
                restore=False
            )

        # Check backup was created
        backups = list(temp_backup_dir.glob("Builder.agent.md.*"))
        assert len(backups) == 1
        assert backups[0].read_text() == "# Builder Content"

    def test_uninstall_restore_from_backup(self, temp_workspace, temp_install_dir, temp_backup_dir):
        """Test uninstall --restore restores files from backup."""
        prompts_dir = temp_install_dir["prompts"]

        # Create and backup a file
        original_file = prompts_dir / "Builder.agent.md"
        original_file.write_text("# Original Content")

        # Create backup manually
        from cadence_installer.sync import create_backup
        backup_path = create_backup(original_file, temp_backup_dir)

        # Remove the file
        original_file.unlink()
        assert not original_file.exists()

        # Restore
        result = uninstall_command(
            [original_file],
            backup_dir=temp_backup_dir,
            dry_run=False,
            skip_confirm=True,
            restore=True
        )

        assert result["restored"] == 1
        assert original_file.exists()
        assert original_file.read_text() == "# Original Content"

    def test_uninstall_restore_handles_missing_backup(self, temp_workspace, temp_install_dir, temp_backup_dir):
        """Test uninstall --restore handles missing backups gracefully."""
        prompts_dir = temp_install_dir["prompts"]
        file_path = prompts_dir / "NonExistent.agent.md"

        result = uninstall_command(
            [file_path],
            backup_dir=temp_backup_dir,
            dry_run=False,
            skip_confirm=True,
            restore=True
        )

        assert result["restored"] == 0
        assert result.get("errors", 0) >= 1

    def test_uninstall_dry_run_no_changes(self, temp_workspace, temp_install_dir, temp_backup_dir):
        """Test --dry-run doesn't modify files."""
        prompts_dir = temp_install_dir["prompts"]
        (prompts_dir / "Builder.agent.md").write_text("# Builder")
        (prompts_dir / "Scout.agent.md").write_text("# Scout")

        files_to_remove = [
            prompts_dir / "Builder.agent.md",
            prompts_dir / "Scout.agent.md",
        ]

        result = uninstall_command(
            files_to_remove,
            backup_dir=temp_backup_dir,
            dry_run=True,
            skip_confirm=True,
            restore=False
        )

        # Files should still exist
        assert (prompts_dir / "Builder.agent.md").exists()
        assert (prompts_dir / "Scout.agent.md").exists()

        # No backups should be created
        backups = list(temp_backup_dir.glob("*"))
        assert len(backups) == 0

    def test_uninstall_dry_run_shows_expected_changes(self, temp_workspace, temp_install_dir, temp_backup_dir):
        """Test --dry-run shows what would be removed."""
        prompts_dir = temp_install_dir["prompts"]
        (prompts_dir / "Builder.agent.md").write_text("# Builder")

        files_to_remove = [prompts_dir / "Builder.agent.md"]

        result = uninstall_command(
            files_to_remove,
            backup_dir=temp_backup_dir,
            dry_run=True,
            skip_confirm=True,
            restore=False
        )

        # Should report what would be removed without actually removing
        assert result["would_remove"] == 1
        assert result.get("removed", 0) == 0
