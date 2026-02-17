"""Configuration and path detection for VS Code installations."""

import os
import platform
import sys
from pathlib import Path
from typing import Dict

# Handle TOML imports for different Python versions
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

try:
    import tomli_w
except ImportError:
    tomli_w = None


def get_user_home() -> Path:
    """Get the user's home directory.

    Returns:
        Path: User home directory path.
    """
    return Path.home()


def detect_vscode_paths() -> Dict[str, Path]:
    """Detect VS Code User/prompts and User/skills paths for the current platform.

    Returns:
        Dict[str, Path]: Dictionary with 'prompts' and 'skills' keys.

    Raises:
        OSError: If the platform is not supported.
    """
    system = platform.system()

    if system == "Linux":
        home = get_user_home()
        base = home / ".config" / "Code" / "User"
    elif system == "Darwin":  # macOS
        home = get_user_home()
        base = home / "Library" / "Application Support" / "Code" / "User"
    elif system == "Windows":
        appdata = os.environ.get("APPDATA")
        if not appdata:
            raise OSError("APPDATA environment variable not set on Windows")
        # Normalize path separators for cross-platform testing
        base = Path(appdata.replace("\\", "/")) / "Code" / "User"
    else:
        raise OSError(f"Unsupported platform: {system}")

    return {
        "prompts": base / "prompts",
        "skills": base / "skills",
    }


def detect_vscode_insiders_paths() -> Dict[str, Path]:
    """Detect VS Code Insiders User/prompts and User/skills paths for the current platform.

    Returns:
        Dict[str, Path]: Dictionary with 'prompts' and 'skills' keys.

    Raises:
        OSError: If the platform is not supported.
    """
    system = platform.system()

    if system == "Linux":
        home = get_user_home()
        base = home / ".config" / "Code - Insiders" / "User"
    elif system == "Darwin":  # macOS
        home = get_user_home()
        base = home / "Library" / "Application Support" / "Code - Insiders" / "User"
    elif system == "Windows":
        appdata = os.environ.get("APPDATA")
        if not appdata:
            raise OSError("APPDATA environment variable not set on Windows")
        # Normalize path separators for cross-platform testing
        base = Path(appdata.replace("\\", "/")) / "Code - Insiders" / "User"
    else:
        raise OSError(f"Unsupported platform: {system}")

    return {
        "prompts": base / "prompts",
        "skills": base / "skills",
    }


def detect_agents_skills_path() -> Path:
    """Detect the .agents/skills path in the user's home directory.

    Returns:
        Path: Path to ~/.agents/skills
    """
    return get_user_home() / ".agents" / "skills"


def read_config(config_path: Path) -> Dict:
    """Read a TOML configuration file.

    Args:
        config_path: Path to the TOML config file.

    Returns:
        Dict: Parsed configuration dictionary, or empty dict if file doesn't exist.

    Raises:
        ImportError: If tomli/tomllib is not available.
    """
    if not config_path.exists():
        return {}

    if tomllib is None:
        raise ImportError(
            "tomli is required for Python < 3.11. Install with: pip install tomli"
        )

    with open(config_path, "rb") as f:
        return tomllib.load(f)


def write_config(config_path: Path, config: Dict) -> None:
    """Write a TOML configuration file.

    Args:
        config_path: Path to write the TOML config file.
        config: Configuration dictionary to write.

    Raises:
        ImportError: If tomli_w is not available.
    """
    if tomli_w is None:
        raise ImportError(
            "tomli_w is required for writing TOML files. Install with: pip install tomli_w"
        )

    # Create parent directories if they don't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "wb") as f:
        tomli_w.dump(config, f)
