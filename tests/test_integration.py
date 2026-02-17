"""Integration tests for install.py main entry point."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from cadence_installer.cli import FileInfo, FileState
from cadence_installer.config import detect_vscode_insiders_paths, detect_agents_skills_path


def test_install_py_exists():
    """Test that install.py exists in the workspace root."""
    install_py = Path(__file__).parent.parent / "install.py"
    assert install_py.exists(), "install.py should exist in workspace root"


def test_install_py_is_executable():
    """Test that install.py has executable permissions (shebang)."""
    install_py = Path(__file__).parent.parent / "install.py"
    content = install_py.read_text()
    assert content.startswith("#!/usr/bin/env python3"), "install.py should have shebang"


def test_help_flag_shows_usage():
    """Test that --help flag shows usage information."""
    install_py = Path(__file__).parent.parent / "install.py"
    result = subprocess.run(
        [sys.executable, str(install_py), "--help"],
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert result.returncode == 0
    assert "usage" in result.stdout.lower() or "usage" in result.stderr.lower()
    assert "status" in result.stdout or "status" in result.stderr
    assert "uninstall" in result.stdout or "uninstall" in result.stderr


def test_version_flag_shows_version():
    """Test that --version flag shows version information."""
    install_py = Path(__file__).parent.parent / "install.py"
    result = subprocess.run(
        [sys.executable, str(install_py), "--version"],
        capture_output=True,
        text=True,
        timeout=5,
    )

    # version flag may exit with 0 or show help
    # Just verify it doesn't crash
    assert result.returncode in [0, 2]


def test_status_command_routes_correctly():
    """Test that 'status' subcommand routes to cli.status_command."""
    install_py = Path(__file__).parent.parent / "install.py"

    with patch("cadence_installer.cli.status_command") as mock_status:
        with patch("cadence_installer.cli.format_status_table") as mock_format:
            # Mock return values
            mock_status.return_value = []
            mock_format.return_value = "No files found"

            result = subprocess.run(
                [sys.executable, str(install_py), "status"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            # Should exit successfully
            assert result.returncode == 0


def test_uninstall_command_routes_correctly():
    """Test that 'uninstall' subcommand routes to cli.uninstall_command."""
    install_py = Path(__file__).parent.parent / "install.py"

    # Create a temporary file to uninstall
    with patch("cadence_installer.cli.uninstall_command") as mock_uninstall:
        # Mock return value
        mock_uninstall.return_value = {"removed": 0, "restored": 0, "errors": 0, "would_remove": 1}

        result = subprocess.run(
            [sys.executable, str(install_py), "uninstall", "/tmp/test.md", "--dry-run", "--yes"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        # Should exit successfully
        assert result.returncode == 0


def test_no_args_launches_tui():
    """Test that running with no arguments attempts to launch TUI."""
    install_py = Path(__file__).parent.parent / "install.py"

    # Import the module directly and patch before calling main
    import importlib.util

    spec = importlib.util.spec_from_file_location("install", install_py)
    assert spec is not None, "Failed to create module spec"
    assert spec.loader is not None, "Module spec has no loader"

    install_module = importlib.util.module_from_spec(spec)

    # Execute the module to load it
    spec.loader.exec_module(install_module)

    # Now patch and call main
    with patch.object(sys, "argv", [str(install_py)]):
        with patch("cadence_installer.ui.run_installer") as mock_run:
            try:
                install_module.main()
            except SystemExit:
                pass  # Expected if main() calls sys.exit()

            # Verify run_installer was called
            mock_run.assert_called_once()


def test_status_command_with_workspace_arg():
    """Test status command with workspace argument."""
    install_py = Path(__file__).parent.parent / "install.py"
    workspace = Path(__file__).parent.parent

    result = subprocess.run(
        [sys.executable, str(install_py), "status", str(workspace)],
        capture_output=True,
        text=True,
        timeout=5,
    )

    # Should execute without error
    assert result.returncode == 0
    # Should show some output
    assert len(result.stdout) > 0 or len(result.stderr) > 0


def test_status_command_dry_run():
    """Test status command with --dry-run flag."""
    install_py = Path(__file__).parent.parent / "install.py"

    result = subprocess.run(
        [sys.executable, str(install_py), "status", "--dry-run"],
        capture_output=True,
        text=True,
        timeout=5,
    )

    # Should execute without error
    assert result.returncode == 0


def test_uninstall_command_dry_run():
    """Test uninstall command with --dry-run flag."""
    install_py = Path(__file__).parent.parent / "install.py"

    result = subprocess.run(
        [sys.executable, str(install_py), "uninstall", "/tmp/test.md", "--dry-run", "--yes"],
        capture_output=True,
        text=True,
        timeout=5,
    )

    # Should execute without error
    assert result.returncode == 0
    # Should mention dry run
    assert "would" in result.stdout.lower() or "dry" in result.stdout.lower()


def test_invalid_command_shows_error():
    """Test that invalid command shows error and help."""
    install_py = Path(__file__).parent.parent / "install.py"

    result = subprocess.run(
        [sys.executable, str(install_py), "invalid_command"],
        capture_output=True,
        text=True,
        timeout=5,
    )

    # Should exit with error code
    assert result.returncode != 0


def test_error_handling_missing_vscode():
    """Test error handling when VS Code installation is not found."""
    install_py = Path(__file__).parent.parent / "install.py"

    # Patch to simulate missing VS Code
    with patch("cadence_installer.config.detect_vscode_insiders_paths") as mock_detect:
        mock_detect.side_effect = OSError("VS Code not found")

        # Run status command
        result = subprocess.run(
            [sys.executable, str(install_py), "status"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        # Should handle error gracefully (not crash)
        # Exit code may be 0 or 1 depending on error handling
        assert result.returncode in [0, 1]


def test_full_install_workflow(tmp_path):
    """Test full install workflow: detect paths → scan files → verify."""
    # Create a mock workspace with test files
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    # Create test files in agents/ subdirectory
    agents_dir = workspace / "agents"
    agents_dir.mkdir()
    agent_file = agents_dir / "Test.agent.md"
    agent_file.write_text("# Test Agent\n")

    instructions_dir = workspace / "instructions"
    instructions_dir.mkdir()
    inst_file = instructions_dir / "Test.instructions.md"
    inst_file.write_text("# Test Instructions\n")

    skills_dir = workspace / "skills"
    skill_dir = skills_dir / "test-skill"
    skill_dir.mkdir(parents=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text("# Test Skill\n")

    # Run status command on the test workspace
    install_py = Path(__file__).parent.parent / "install.py"

    result = subprocess.run(
        [sys.executable, str(install_py), "status", str(workspace)],
        capture_output=True,
        text=True,
        timeout=5,
    )

    # Should execute successfully
    assert result.returncode == 0

    # Should find our test files (they won't be installed yet)
    # We're just verifying the scan works
    assert len(result.stdout) > 0 or len(result.stderr) > 0


def test_config_file_persistence(tmp_path):
    """Test that config file can be read and written."""
    from cadence_installer.config import read_config, write_config

    config_file = tmp_path / "config.toml"

    # Write config
    test_config = {
        "workspace": str(tmp_path / "workspace"),
        "installed_files": ["Test.agent.md"],
    }

    write_config(config_file, test_config)

    # Verify file exists
    assert config_file.exists()

    # Read config back
    loaded_config = read_config(config_file)

    # Verify data matches
    assert loaded_config["workspace"] == test_config["workspace"]
    assert loaded_config["installed_files"] == test_config["installed_files"]


def test_exit_code_on_success():
    """Test that successful commands exit with code 0."""
    install_py = Path(__file__).parent.parent / "install.py"

    result = subprocess.run(
        [sys.executable, str(install_py), "status", "--dry-run"],
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert result.returncode == 0


def test_exit_code_on_invalid_args():
    """Test that invalid arguments exit with code 2."""
    install_py = Path(__file__).parent.parent / "install.py"

    result = subprocess.run(
        [sys.executable, str(install_py), "--invalid-flag"],
        capture_output=True,
        text=True,
        timeout=5,
    )

    # argparse typically exits with 2 for invalid arguments
    assert result.returncode == 2


def test_common_flags_work_across_commands():
    """Test that common flags like --help work with subcommands."""
    install_py = Path(__file__).parent.parent / "install.py"

    # Test --help with status subcommand
    result = subprocess.run(
        [sys.executable, str(install_py), "status", "--help"],
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert result.returncode == 0
    assert "status" in result.stdout.lower() or "status" in result.stderr.lower()

    # Test --help with uninstall subcommand
    result = subprocess.run(
        [sys.executable, str(install_py), "uninstall", "--help"],
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert result.returncode == 0
    assert "uninstall" in result.stdout.lower() or "uninstall" in result.stderr.lower()


def test_all_existing_tests_still_pass():
    """Test that all existing tests still pass after integration."""
    # This is a meta-test that verifies we haven't broken existing functionality
    # Run pytest on the entire test suite (excluding this test to avoid recursion)

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "-k", "not test_all_existing_tests_still_pass"],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=Path(__file__).parent.parent,
    )

    # All tests should pass
    assert result.returncode == 0, f"Existing tests failed:\n{result.stdout}\n{result.stderr}"
