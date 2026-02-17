"""Tests for configuration and path detection module."""

import os
import platform
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from cadence_installer.config import (
    detect_vscode_paths,
    detect_vscode_insiders_paths,
    detect_agents_skills_path,
    read_config,
    write_config,
    get_user_home,
)


class TestPathDetection:
    """Test cross-platform path detection."""

    @patch("platform.system")
    @patch("pathlib.Path.home")
    def test_vscode_path_linux(self, mock_home, mock_system):
        """Test VS Code path detection on Linux."""
        mock_system.return_value = "Linux"
        mock_home.return_value = Path("/home/testuser")

        paths = detect_vscode_paths()

        assert "prompts" in paths
        assert "skills" in paths
        assert paths["prompts"] == Path("/home/testuser/.config/Code/User/prompts")
        assert paths["skills"] == Path("/home/testuser/.config/Code/User/skills")

    @patch("platform.system")
    @patch("pathlib.Path.home")
    def test_vscode_insiders_path_linux(self, mock_home, mock_system):
        """Test VS Code Insiders path detection on Linux."""
        mock_system.return_value = "Linux"
        mock_home.return_value = Path("/home/testuser")

        paths = detect_vscode_insiders_paths()

        assert "prompts" in paths
        assert "skills" in paths
        assert paths["prompts"] == Path("/home/testuser/.config/Code - Insiders/User/prompts")
        assert paths["skills"] == Path("/home/testuser/.config/Code - Insiders/User/skills")

    @patch("platform.system")
    @patch("pathlib.Path.home")
    def test_vscode_path_macos(self, mock_home, mock_system):
        """Test VS Code path detection on macOS."""
        mock_system.return_value = "Darwin"
        mock_home.return_value = Path("/Users/testuser")

        paths = detect_vscode_paths()

        assert paths["prompts"] == Path("/Users/testuser/Library/Application Support/Code/User/prompts")
        assert paths["skills"] == Path("/Users/testuser/Library/Application Support/Code/User/skills")

    @patch("platform.system")
    @patch("pathlib.Path.home")
    def test_vscode_insiders_path_macos(self, mock_home, mock_system):
        """Test VS Code Insiders path detection on macOS."""
        mock_system.return_value = "Darwin"
        mock_home.return_value = Path("/Users/testuser")

        paths = detect_vscode_insiders_paths()

        assert paths["prompts"] == Path("/Users/testuser/Library/Application Support/Code - Insiders/User/prompts")
        assert paths["skills"] == Path("/Users/testuser/Library/Application Support/Code - Insiders/User/skills")

    @patch("platform.system")
    @patch.dict(os.environ, {"APPDATA": "C:\\Users\\testuser\\AppData\\Roaming"})
    def test_vscode_path_windows(self, mock_system):
        """Test VS Code path detection on Windows."""
        mock_system.return_value = "Windows"

        paths = detect_vscode_paths()

        assert paths["prompts"] == Path("C:/Users/testuser/AppData/Roaming/Code/User/prompts")
        assert paths["skills"] == Path("C:/Users/testuser/AppData/Roaming/Code/User/skills")

    @patch("platform.system")
    @patch.dict(os.environ, {"APPDATA": "C:\\Users\\testuser\\AppData\\Roaming"})
    def test_vscode_insiders_path_windows(self, mock_system):
        """Test VS Code Insiders path detection on Windows."""
        mock_system.return_value = "Windows"

        paths = detect_vscode_insiders_paths()

        assert paths["prompts"] == Path("C:/Users/testuser/AppData/Roaming/Code - Insiders/User/prompts")
        assert paths["skills"] == Path("C:/Users/testuser/AppData/Roaming/Code - Insiders/User/skills")

    @patch("pathlib.Path.home")
    def test_agents_skills_path(self, mock_home):
        """Test .agents/skills path resolution."""
        mock_home.return_value = Path("/home/testuser")

        path = detect_agents_skills_path()

        assert path == Path("/home/testuser/.agents/skills")

    @patch("platform.system")
    def test_unsupported_platform(self, mock_system):
        """Test that unsupported platforms raise an error."""
        mock_system.return_value = "FreeBSD"

        with pytest.raises(OSError) as exc_info:
            detect_vscode_paths()

        assert "Unsupported platform" in str(exc_info.value)


class TestConfigReadWrite:
    """Test TOML configuration file handling."""

    def test_write_and_read_config(self):
        """Test writing and reading TOML config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"

            test_config = {
                "installer": {
                    "target": "vscode-insiders",
                    "platform": "linux"
                },
                "paths": {
                    "prompts": "/home/user/.config/Code/User/prompts",
                    "skills": "/home/user/.agents/skills"
                }
            }

            write_config(config_path, test_config)
            assert config_path.exists()

            loaded_config = read_config(config_path)
            assert loaded_config == test_config

    def test_read_missing_config(self):
        """Test reading a non-existent config file returns empty dict."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "nonexistent.toml"

            config = read_config(config_path)
            assert config == {}

    def test_write_config_creates_parent_dirs(self):
        """Test that write_config creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "subdir" / "nested" / "config.toml"

            test_config = {"key": "value"}
            write_config(config_path, test_config)

            assert config_path.exists()
            assert config_path.parent.exists()

    def test_write_config_overwrites_existing(self):
        """Test that write_config overwrites existing files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"

            # Write first config
            write_config(config_path, {"old": "data"})

            # Overwrite with new config
            new_config = {"new": "data"}
            write_config(config_path, new_config)

            loaded = read_config(config_path)
            assert loaded == new_config
            assert "old" not in loaded


class TestUserHome:
    """Test user home directory detection."""

    @patch("pathlib.Path.home")
    def test_get_user_home(self, mock_home):
        """Test that get_user_home returns Path.home()."""
        mock_home.return_value = Path("/home/testuser")

        home = get_user_home()

        assert home == Path("/home/testuser")
        assert isinstance(home, Path)
