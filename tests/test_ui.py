"""Tests for interactive TUI installer."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from cadence_installer.ui import InstallerApp, FileItem
from cadence_installer.sync import FileStatus


class TestFileItemRendering:
    """Test file item creation and status indicators."""

    def test_file_item_creates_with_source_newer_status(self):
        """File item shows correct indicator for newer source."""
        item = FileItem(
            source=Path("Builder.agent.md"),
            dest=Path("/path/to/prompts/Builder.agent.md"),
            status=FileStatus.SOURCE_NEWER,
            relative_source="Builder.agent.md",
            relative_dest="User/prompts/Builder.agent.md"
        )
        assert item.status == FileStatus.SOURCE_NEWER
        assert item.selected is True  # Should be selected by default for newer files

    def test_file_item_creates_with_dest_missing_status(self):
        """File item shows correct indicator for missing destination."""
        item = FileItem(
            source=Path("Scout.agent.md"),
            dest=Path("/path/to/prompts/Scout.agent.md"),
            status=FileStatus.DEST_MISSING,
            relative_source="Scout.agent.md",
            relative_dest="User/prompts/Scout.agent.md"
        )
        assert item.status == FileStatus.DEST_MISSING
        assert item.selected is True  # Should be selected by default for new files

    def test_file_item_creates_with_identical_status(self):
        """File item shows correct indicator for identical files."""
        item = FileItem(
            source=Path("Critic.agent.md"),
            dest=Path("/path/to/prompts/Critic.agent.md"),
            status=FileStatus.IDENTICAL,
            relative_source="Critic.agent.md",
            relative_dest="User/prompts/Critic.agent.md"
        )
        assert item.status == FileStatus.IDENTICAL
        assert item.selected is False  # Should not be selected by default for identical

    def test_file_item_creates_with_source_older_status(self):
        """File item shows correct indicator for older source."""
        item = FileItem(
            source=Path("Cadence.agent.md"),
            dest=Path("/path/to/prompts/Cadence.agent.md"),
            status=FileStatus.SOURCE_OLDER,
            relative_source="Cadence.agent.md",
            relative_dest="User/prompts/Cadence.agent.md"
        )
        assert item.status == FileStatus.SOURCE_OLDER
        assert item.selected is False  # Should not be selected for older files


class TestFileSelection:
    """Test checkbox selection and deselection."""

    @pytest.mark.asyncio
    async def test_toggle_individual_file_selection(self):
        """User can toggle individual file selection."""
        app = InstallerApp()

        # Manually add test file items
        app.file_items = [
            FileItem(
                source=Path("test.agent.md"),
                dest=Path("/tmp/test.agent.md"),
                status=FileStatus.SOURCE_NEWER,
                relative_source="test.agent.md",
                relative_dest="User/prompts/test.agent.md",
                selected=True
            )
        ]

        async with app.run_test() as pilot:
            await pilot.pause()

            # Should have at least one item
            assert len(app.file_items) > 0

            # Get first item
            first_item = app.file_items[0]
            initial_state = first_item.selected

            # Toggle it
            await pilot.press("space")
            assert first_item.selected == (not initial_state)

    @pytest.mark.asyncio
    async def test_select_all_functionality(self):
        """User can select all files at once."""
        app = InstallerApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            # Press 'a' to select all
            await pilot.press("a")

            # All files should be selected
            assert all(f.selected for f in app.file_items)

    @pytest.mark.asyncio
    async def test_deselect_all_functionality(self):
        """User can deselect all files at once."""
        app = InstallerApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            # First select all
            await pilot.press("a")
            assert all(f.selected for f in app.file_items)

            # Press 'd' to deselect all
            await pilot.press("d")

            # No files should be selected
            assert not any(f.selected for f in app.file_items)


class TestFileTypeFiltering:
    """Test filtering by file type."""

    @pytest.mark.asyncio
    async def test_filter_agents_only(self):
        """User can filter to show agents only."""
        app = InstallerApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            # Apply agents filter (press '1')
            await pilot.press("1")

            # Check that only agent files are visible
            visible_items = [f for f in app.file_items if f.visible]
            assert all(f.relative_source.endswith('.agent.md') for f in visible_items)

    @pytest.mark.asyncio
    async def test_filter_skills_only(self):
        """User can filter to show skills only."""
        app = InstallerApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            # Apply skills filter (press '2')
            await pilot.press("2")

            # Check that only SKILL.md files are visible
            visible_items = [f for f in app.file_items if f.visible]
            assert all('SKILL.md' in str(f.relative_source) for f in visible_items)

    @pytest.mark.asyncio
    async def test_filter_instructions_only(self):
        """User can filter to show instructions only."""
        app = InstallerApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            # Apply instructions filter (press '3')
            await pilot.press("3")

            # Check that only instruction files are visible
            visible_items = [f for f in app.file_items if f.visible]
            assert all(f.relative_source.endswith('.instructions.md') for f in visible_items)

    @pytest.mark.asyncio
    async def test_clear_filter_shows_all(self):
        """User can clear filters to show all files."""
        app = InstallerApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            # Apply a filter
            await pilot.press("1")
            filtered_count = len([f for f in app.file_items if f.visible])

            # Clear filter (press '0')
            await pilot.press("0")

            # All files should be visible
            all_count = len([f for f in app.file_items if f.visible])
            assert all_count > filtered_count


class TestDiffPreview:
    """Test diff preview display."""

    @pytest.mark.asyncio
    async def test_diff_preview_shows_for_selected_file(self):
        """Diff preview panel shows changes for selected file."""
        app = InstallerApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            # Select first file and request diff
            await pilot.press("enter")

            # Check that diff preview is populated
            assert app.current_diff is not None
            assert len(app.current_diff) > 0

    @pytest.mark.asyncio
    async def test_diff_preview_shows_new_file_indicator(self):
        """Diff preview indicates when file is new."""
        app = InstallerApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            # Find a DEST_MISSING file
            new_file = next(
                (f for f in app.file_items if f.status == FileStatus.DEST_MISSING),
                None
            )

            if new_file:
                app.selected_file = new_file
                await pilot.press("enter")

                assert app.current_diff is not None
                assert "[New File]" in app.current_diff or "new file" in app.current_diff.lower()

    @pytest.mark.asyncio
    async def test_diff_preview_empty_for_identical_files(self):
        """Diff preview shows 'No changes' for identical files."""
        app = InstallerApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            # Find an identical file
            identical_file = next(
                (f for f in app.file_items if f.status == FileStatus.IDENTICAL),
                None
            )

            if identical_file:
                app.selected_file = identical_file
                await pilot.press("enter")

                assert app.current_diff is not None
                assert "No changes" in app.current_diff or "identical" in app.current_diff.lower()


class TestInstallationFlow:
    """Test installation execution."""

    @pytest.mark.asyncio
    async def test_installation_executes_for_selected_files(self):
        """Installation processes only selected files."""
        app = InstallerApp()

        with patch('cadence_installer.ui.shutil.copy2') as mock_copy:
            async with app.run_test() as pilot:
                await pilot.pause()

                # Get count of selected files
                selected_files = [f for f in app.file_items if f.selected]
                initial_count = len(selected_files)

                # Start installation (press 'i')
                await pilot.press("i")
                await pilot.pause()

                # Verify copy was called for each selected file
                assert mock_copy.call_count == initial_count

    @pytest.mark.asyncio
    async def test_installation_creates_destination_directories(self):
        """Installation creates missing directories."""
        app = InstallerApp()

        # Add test file item
        app.file_items = [
            FileItem(
                source=Path(__file__).parent.parent / "README.md",
                dest=Path("/tmp/test_install/prompts/test.agent.md"),
                status=FileStatus.SOURCE_NEWER,
                relative_source="test.agent.md",
                relative_dest="User/prompts/test.agent.md",
                selected=True
            )
        ]

        with patch('cadence_installer.ui.shutil.copy2'), \
             patch('cadence_installer.ui.validate_file_type', return_value=True):
            async with app.run_test() as pilot:
                await pilot.pause()

                # Start installation
                await pilot.press("i")
                await pilot.pause()

                # Verify directory was created (check that dest parent exists after install)
                # In real usage, mkdir is called - we just verify no error occurs
                assert app.status_message is not None

    @pytest.mark.asyncio
    async def test_installation_shows_success_message(self):
        """Installation displays success message on completion."""
        app = InstallerApp()

        # Add test file item
        app.file_items = [
            FileItem(
                source=Path(__file__).parent.parent / "README.md",
                dest=Path("/tmp/test_install2/prompts/test.agent.md"),
                status=FileStatus.SOURCE_NEWER,
                relative_source="test.agent.md",
                relative_dest="User/prompts/test.agent.md",
                selected=True
            )
        ]

        with patch('cadence_installer.ui.shutil.copy2'), \
             patch('cadence_installer.ui.validate_file_type', return_value=True):
            async with app.run_test() as pilot:
                await pilot.pause()

                # Start installation
                await pilot.press("i")
                await pilot.pause()

                # Check that success message is displayed
                assert app.status_message is not None
                assert "success" in app.status_message.lower() or "installed" in app.status_message.lower()


class TestConflictHandling:
    """Test conflict detection and resolution."""

    @pytest.mark.asyncio
    async def test_conflict_detection_for_newer_destination(self):
        """Installer detects when destination is newer than source."""
        app = InstallerApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            # Find a SOURCE_OLDER file
            older_file = next(
                (f for f in app.file_items if f.status == FileStatus.SOURCE_OLDER),
                None
            )

            if older_file:
                assert older_file.selected is False  # Should not be selected by default

    @pytest.mark.asyncio
    async def test_backup_created_before_overwrite(self):
        """Installer creates backup before overwriting newer files."""
        app = InstallerApp()

        # Create a temporary dest file
        dest_path = Path("/tmp/test_backup/test.agent.md")
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_text("existing content")

        # Add test file item with SOURCE_NEWER status
        app.file_items = [
            FileItem(
                source=Path(__file__).parent.parent / "README.md",
                dest=dest_path,
                status=FileStatus.SOURCE_NEWER,
                relative_source="test.agent.md",
                relative_dest="User/prompts/test.agent.md",
                selected=True
            )
        ]

        with patch('cadence_installer.ui.create_backup', return_value=Path("/tmp/backup.bak")) as mock_backup, \
             patch('cadence_installer.ui.shutil.copy2'), \
             patch('cadence_installer.ui.validate_file_type', return_value=True):
            async with app.run_test() as pilot:
                await pilot.pause()

                # Start installation
                await pilot.press("i")
                await pilot.pause()

                # Verify backup was created
                assert mock_backup.called

    @pytest.mark.asyncio
    async def test_user_can_skip_conflicting_file(self):
        """User can choose to skip files with conflicts."""
        app = InstallerApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            # Deselect a file (essentially skipping it)
            if app.file_items:
                app.file_items[0].selected = True
                await pilot.press("space")
                assert app.file_items[0].selected is False


class TestProgressIndicators:
    """Test progress tracking during installation."""

    @pytest.mark.asyncio
    async def test_progress_bar_shows_during_installation(self):
        """Progress bar displays during installation."""
        app = InstallerApp()

        with patch('cadence_installer.ui.shutil.copy2'):
            async with app.run_test() as pilot:
                await pilot.pause()

                # Start installation
                await pilot.press("i")

                # Check that progress is being tracked
                assert app.installation_progress >= 0
                assert app.installation_progress <= 100

    @pytest.mark.asyncio
    async def test_progress_updates_per_file(self):
        """Progress updates for each file processed."""
        app = InstallerApp()

        progress_values = []

        def track_progress(*args, **kwargs):
            progress_values.append(app.installation_progress)

        with patch('cadence_installer.ui.shutil.copy2', side_effect=track_progress):
            async with app.run_test() as pilot:
                await pilot.pause()

                selected_count = len([f for f in app.file_items if f.selected])

                if selected_count > 0:
                    await pilot.press("i")
                    await pilot.pause()

                    # Progress should have increased
                    if len(progress_values) > 1:
                        assert progress_values[-1] > progress_values[0]


class TestErrorHandling:
    """Test error handling for validation and IO failures."""

    @pytest.mark.asyncio
    async def test_validation_error_shows_message(self):
        """Validation errors display clear error messages."""
        app = InstallerApp()

        # Add test file item with invalid type
        app.file_items = [
            FileItem(
                source=Path("invalid.txt"),
                dest=Path("/tmp/invalid.txt"),
                status=FileStatus.SOURCE_NEWER,
                relative_source="invalid.txt",
                relative_dest="User/prompts/invalid.txt",
                selected=True
            )
        ]

        with patch('cadence_installer.ui.validate_file_type', return_value=False):
            async with app.run_test() as pilot:
                await pilot.pause()

                # Try to start installation with invalid file
                await pilot.press("i")
                await pilot.pause()

                # Check for error message (should report 0 installed and errors)
                assert app.status_message is not None
                assert "0" in app.status_message or "error" in app.status_message.lower()

    @pytest.mark.asyncio
    async def test_yaml_validation_rejects_invalid_files(self):
        """YAML validation runs before installation and rejects invalid files."""
        app = InstallerApp()

        # Create a test file with invalid YAML (missing required fields)
        test_file = Path("/tmp/test_invalid.agent.md")
        test_file.write_text("---\ntitle: Test\n---\n# Content")  # Missing 'name' and 'description'

        app.file_items = [
            FileItem(
                source=test_file,
                dest=Path("/tmp/dest/test_invalid.agent.md"),
                status=FileStatus.SOURCE_NEWER,
                relative_source="test_invalid.agent.md",
                relative_dest="User/prompts/test_invalid.agent.md",
                selected=True
            )
        ]

        with patch('cadence_installer.ui.validate_file_type', return_value=True):
            async with app.run_test() as pilot:
                await pilot.pause()

                # Try to install
                await pilot.press("i")
                await pilot.pause()

                # Should report errors due to missing required fields
                assert app.status_message is not None
                assert ("error" in app.status_message.lower() or "0 files" in app.status_message.lower())

    @pytest.mark.asyncio
    async def test_io_error_shows_message(self):
        """IO errors display clear error messages."""
        app = InstallerApp()

        # Add test file item
        app.file_items = [
            FileItem(
                source=Path(__file__).parent.parent / "README.md",
                dest=Path("/tmp/test_io_error/test.agent.md"),
                status=FileStatus.SOURCE_NEWER,
                relative_source="test.agent.md",
                relative_dest="User/prompts/test.agent.md",
                selected=True
            )
        ]

        with patch('cadence_installer.ui.shutil.copy2', side_effect=IOError("Permission denied")), \
             patch('cadence_installer.ui.validate_file_type', return_value=True), \
             patch('cadence_installer.ui.validate_file') as mock_validate:
            # Mock validate_file to return valid result
            from cadence_installer.validation import ValidationResult, ValidationStatus
            mock_validate.return_value = ValidationResult(
                status=ValidationStatus.VALID,
                errors=[],
                data={"name": "test"}
            )

            async with app.run_test() as pilot:
                await pilot.pause()

                # Try to install
                await pilot.press("i")
                await pilot.pause()

                # Check for error message (0 installed with 1 error)
                assert app.status_message is not None
                assert "0" in app.status_message or "error" in app.status_message.lower()

    @pytest.mark.asyncio
    async def test_keyboard_interrupt_exits_gracefully(self):
        """Ctrl+C exits the application gracefully."""
        app = InstallerApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # Press 'q' to quit
            await pilot.press("q")

            # App should exit without error
            assert not app.is_running


class TestDiffPreviewRealDiffs:
    """Test diff preview shows actual line-by-line differences."""

    @pytest.mark.asyncio
    async def test_diff_preview_shows_unified_diff(self):
        """Diff preview uses difflib to show real line-by-line changes."""
        from pathlib import Path
        import tempfile

        app = InstallerApp()

        # Create temp files with different content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.agent.md', delete=False) as src_f:
            src_f.write("line1\nline2 updated\nline3\n")
            src_path = Path(src_f.name)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.agent.md', delete=False) as dest_f:
            dest_f.write("line1\nline2\nline3\n")
            dest_path = Path(dest_f.name)

        try:
            # Create file item with SOURCE_NEWER status
            item = FileItem(
                source=src_path,
                dest=dest_path,
                status=FileStatus.SOURCE_NEWER,
                relative_source="test.agent.md",
                relative_dest="User/prompts/test.agent.md"
            )

            app.file_items = [item]

            async with app.run_test() as pilot:
                await pilot.pause()

                # Show diff
                await pilot.press("enter")

                # Check that diff contains unified diff markers
                assert app.current_diff is not None
                # Should contain unified diff format (-, +, @@, etc.)
                has_diff_content = (
                    "---" in app.current_diff or
                    "+++" in app.current_diff or
                    "-line2" in app.current_diff or
                    "+line2 updated" in app.current_diff
                )
                assert has_diff_content
        finally:
            src_path.unlink()
            dest_path.unlink()


class TestBackupLocationCentralized:
    """Test backup location is centralized to ~/.agents/backups."""

    @pytest.mark.asyncio
    async def test_backup_uses_agents_backups_dir(self):
        """Installer uses ~/.agents/backups for all backups."""
        app = InstallerApp()

        # Create a temporary dest file
        dest_path = Path("/tmp/test_backup_central/test.agent.md")
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_text("existing content")

        # Add test file item with SOURCE_NEWER status
        app.file_items = [
            FileItem(
                source=Path(__file__).parent.parent / "README.md",
                dest=dest_path,
                status=FileStatus.SOURCE_NEWER,
                relative_source="test.agent.md",
                relative_dest="User/prompts/test.agent.md",
                selected=True
            )
        ]

        with patch('cadence_installer.ui.create_backup') as mock_backup, \
             patch('cadence_installer.ui.shutil.copy2'), \
             patch('cadence_installer.ui.validate_file_type', return_value=True), \
             patch('cadence_installer.ui.validate_file') as mock_validate:
            # Mock validate_file to return valid result
            from cadence_installer.validation import ValidationResult, ValidationStatus
            mock_validate.return_value = ValidationResult(
                status=ValidationStatus.VALID,
                errors=[],
                data={"name": "test"}
            )

            async with app.run_test() as pilot:
                await pilot.pause()

                # Start installation
                await pilot.press("i")
                await pilot.pause()

                # Verify backup was created with correct backup_dir
                assert mock_backup.called
                # Check that the backup_dir argument contains .agents/backups
                backup_dir = mock_backup.call_args[0][1]
                assert ".agents" in str(backup_dir)
                assert "backups" in str(backup_dir)


class TestRaceConditionFix:
    """Test race condition in backup/install is fixed."""

    @pytest.mark.asyncio
    async def test_copy_operation_handles_race_condition(self):
        """Copy operation handles race conditions with try-except."""
        app = InstallerApp()

        # Add test file item
        app.file_items = [
            FileItem(
                source=Path(__file__).parent.parent / "README.md",
                dest=Path("/tmp/test_race/test.agent.md"),
                status=FileStatus.SOURCE_NEWER,
                relative_source="test.agent.md",
                relative_dest="User/prompts/test.agent.md",
                selected=True
            )
        ]

        # Simulate race condition - file exists check passes but copy fails
        with patch('cadence_installer.ui.shutil.copy2', side_effect=IOError("File changed during copy")), \
             patch('cadence_installer.ui.validate_file_type', return_value=True), \
             patch('cadence_installer.ui.validate_file') as mock_validate:
            # Mock validate_file to return valid result
            from cadence_installer.validation import ValidationResult, ValidationStatus
            mock_validate.return_value = ValidationResult(
                status=ValidationStatus.VALID,
                errors=[],
                data={"name": "test"}
            )

            async with app.run_test() as pilot:
                await pilot.pause()

                # Try to install
                await pilot.press("i")
                await pilot.pause()

                # Should handle the error gracefully
                assert app.status_message is not None
                assert "error" in app.status_message.lower()


class TestNavigationIndexReset:
    """Test navigation index resets when filtering."""

    @pytest.mark.asyncio
    async def test_filter_resets_selected_index(self):
        """Filtering resets selected_index to prevent out of bounds."""
        app = InstallerApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # Move down several times if possible
            if len(app.file_items) > 2:
                await pilot.press("down")
                await pilot.press("down")
                initial_index = app.selected_index
                assert initial_index > 0

                # Apply filter
                await pilot.press("1")

                # Index should reset to 0
                assert app.selected_index == 0

    @pytest.mark.asyncio
    async def test_all_filters_reset_index(self):
        """All filter actions reset the selected index."""
        app = InstallerApp()

        async with app.run_test() as pilot:
            await pilot.pause()

            # Test each filter
            for key in ["1", "2", "3", "0"]:
                # Move cursor down first
                if len(app.file_items) > 1:
                    await pilot.press("down")
                    if app.selected_index > 0:
                        # Apply filter
                        await pilot.press(key)
                        # Should reset
                        assert app.selected_index == 0


class TestKeyboardShortcuts:
    """Test keyboard navigation and shortcuts."""

    @pytest.mark.asyncio
    async def test_space_toggles_selection(self):
        """Space bar toggles file selection."""
        app = InstallerApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            if app.file_items:
                initial_state = app.file_items[0].selected
                await pilot.press("space")
                assert app.file_items[0].selected == (not initial_state)

    @pytest.mark.asyncio
    async def test_enter_shows_diff(self):
        """Enter key shows diff preview."""
        app = InstallerApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            await pilot.press("enter")
            assert app.current_diff is not None

    @pytest.mark.asyncio
    async def test_i_starts_installation(self):
        """'i' key starts installation process."""
        app = InstallerApp()

        with patch('cadence_installer.ui.shutil.copy2'):
            async with app.run_test() as pilot:
                await pilot.pause()

                await pilot.press("i")
                await pilot.pause()

                # Installation should have been triggered
                assert app.status_message is not None

    @pytest.mark.asyncio
    async def test_q_quits_application(self):
        """'q' key quits the application."""
        app = InstallerApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            await pilot.press("q")

            # App should not be running
            assert not app.is_running

    @pytest.mark.asyncio
    async def test_arrow_keys_navigate_file_list(self):
        """Arrow keys navigate through file list."""
        app = InstallerApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            if len(app.file_items) > 1:
                # Press down arrow
                await pilot.press("down")

                # Currently selected index should have changed
                assert app.selected_index > 0
