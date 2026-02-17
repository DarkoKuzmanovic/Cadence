#!/usr/bin/env python3
"""Cadence installer - unified entry point for TUI and CLI commands.

Usage:
    install.py                    # Launch interactive TUI installer
    install.py status [workspace] # Show installation status
    install.py uninstall <files>  # Uninstall files
    install.py --help             # Show help
    install.py --version          # Show version
"""

import argparse
import sys
from pathlib import Path

# Version information
__version__ = "1.0.0"


def main():
    """Main entry point for the Cadence installer."""
    parser = argparse.ArgumentParser(
        description="Cadence installer - manage agent, skill, and instruction files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  install.py                           # Launch interactive TUI
  install.py status                    # Show sync status for current directory
  install.py status /path/to/workspace # Show sync status for specific workspace
  install.py uninstall file.md --yes   # Uninstall file without confirmation
        """,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"Cadence installer {__version__}",
    )

    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Status command
    status_parser = subparsers.add_parser(
        "status",
        help="Show installation status",
        description="Display sync status of agent, skill, and instruction files",
    )
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
        help="Show what would happen without executing",
    )

    # Uninstall command
    uninstall_parser = subparsers.add_parser(
        "uninstall",
        help="Uninstall files",
        description="Remove or restore installed files",
    )
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

    # Parse arguments
    args = parser.parse_args()

    # Route to appropriate handler
    try:
        if args.command == "status":
            status_handler(args)
        elif args.command == "uninstall":
            uninstall_handler(args)
        else:
            # No command specified - launch TUI
            tui_handler()

    except KeyboardInterrupt:
        print("\n\nAborted by user.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def tui_handler():
    """Launch the interactive TUI installer."""
    try:
        from cadence_installer.ui import run_installer

        run_installer()
    except ImportError as e:
        print(f"Error: Failed to load TUI module: {e}", file=sys.stderr)
        print("Make sure all dependencies are installed: pip install -r requirements.txt", file=sys.stderr)
        sys.exit(1)


def status_handler(args):
    """Handle status command."""
    try:
        from cadence_installer.cli import status_command, format_status_table
        from rich.console import Console

        console = Console()

        # Execute status command
        file_infos = status_command(args.workspace, dry_run=getattr(args, 'dry_run', False))

        # Format and display results
        output = format_status_table(file_infos)
        console.print(output)

    except ImportError as e:
        print(f"Error: Failed to load CLI module: {e}", file=sys.stderr)
        print("Make sure all dependencies are installed: pip install -r requirements.txt", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("VS Code Insiders installation not found. Make sure it's installed.", file=sys.stderr)
        sys.exit(1)


def uninstall_handler(args):
    """Handle uninstall command."""
    try:
        from cadence_installer.cli import uninstall_command
        from rich.console import Console

        console = Console()

        # Execute uninstall command
        result = uninstall_command(
            args.files,
            backup_dir=args.backup_dir,
            dry_run=getattr(args, 'dry_run', False),
            skip_confirm=args.yes,
            restore=args.restore,
        )

        # Display results
        dry_run = getattr(args, 'dry_run', False)
        if dry_run:
            console.print(f"\n[dim]Dry run: {result['would_remove']} file(s) would be affected[/dim]")
        else:
            if result["removed"] > 0:
                console.print(f"\n[green]Removed {result['removed']} file(s)[/green]")
            if result["restored"] > 0:
                console.print(f"\n[green]Restored {result['restored']} file(s)[/green]")
            if result["errors"] > 0:
                console.print(f"\n[red]{result['errors']} error(s) occurred[/red]")
                sys.exit(1)

    except ImportError as e:
        print(f"Error: Failed to load CLI module: {e}", file=sys.stderr)
        print("Make sure all dependencies are installed: pip install -r requirements.txt", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
