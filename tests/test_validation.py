"""Tests for YAML frontmatter validation."""

import pytest
from pathlib import Path
from cadence_installer.validation import (
    validate_file,
    parse_frontmatter,
    ValidationStatus,
    ValidationResult,
)


class TestParseFrontmatter:
    """Test YAML frontmatter parsing."""

    def test_parse_valid_yaml_frontmatter(self):
        """Test parsing valid YAML frontmatter."""
        content = """---
name: test-agent
description: "A test agent"
---

# Agent Content
"""
        result = parse_frontmatter(content)
        assert result is not None
        assert result['name'] == 'test-agent'
        assert result['description'] == 'A test agent'

    def test_parse_no_frontmatter(self):
        """Test handling files with no frontmatter."""
        content = "# Just a markdown file\n\nNo frontmatter here."
        result = parse_frontmatter(content)
        assert result is None

    def test_parse_empty_file(self):
        """Test handling empty files."""
        content = ""
        result = parse_frontmatter(content)
        assert result is None

    def test_parse_malformed_yaml(self):
        """Test detecting malformed YAML."""
        content = """---
name: test-agent
description: "Unclosed quote
invalid: [unclosed list
---

# Content
"""
        with pytest.raises(ValueError) as excinfo:
            parse_frontmatter(content)
        assert "malformed yaml" in str(excinfo.value).lower()

    def test_parse_incomplete_frontmatter_delimiters(self):
        """Test handling incomplete frontmatter (only opening delimiter)."""
        content = """---
name: test-agent
description: "No closing delimiter"

# Content
"""
        result = parse_frontmatter(content)
        assert result is None

    def test_parse_frontmatter_not_at_start(self):
        """Test that frontmatter must be at the start of file."""
        content = """
Some content first

---
name: test-agent
---
"""
        result = parse_frontmatter(content)
        assert result is None


class TestValidateAgentFile:
    """Test validation for .agent.md files."""

    def test_validate_agent_valid(self):
        """Test validation of valid agent file."""
        content = """---
name: Builder
description: "TDD implementation specialist"
---

# Agent content
"""
        result = validate_file(content, '.agent.md')
        assert result.status == ValidationStatus.VALID
        assert result.errors == []

    def test_validate_agent_missing_name(self):
        """Test detecting missing name field in agent file."""
        content = """---
description: "TDD implementation specialist"
---

# Agent content
"""
        result = validate_file(content, '.agent.md')
        assert result.status == ValidationStatus.MISSING_FIELDS
        assert 'name' in str(result.errors).lower()

    def test_validate_agent_missing_description(self):
        """Test detecting missing description field in agent file."""
        content = """---
name: Builder
---

# Agent content
"""
        result = validate_file(content, '.agent.md')
        assert result.status == ValidationStatus.MISSING_FIELDS
        assert 'description' in str(result.errors).lower()

    def test_validate_agent_missing_both_fields(self):
        """Test detecting multiple missing fields."""
        content = """---
tools: ["read/readFile"]
---

# Agent content
"""
        result = validate_file(content, '.agent.md')
        assert result.status == ValidationStatus.MISSING_FIELDS
        assert 'name' in str(result.errors).lower()
        assert 'description' in str(result.errors).lower()


class TestValidateInstructionsFile:
    """Test validation for .instructions.md files."""

    def test_validate_instructions_valid(self):
        """Test validation of valid instructions file."""
        content = """---
applyTo: "**"
---

# Instructions content
"""
        result = validate_file(content, '.instructions.md')
        assert result.status == ValidationStatus.VALID
        assert result.errors == []

    def test_validate_instructions_missing_applyto(self):
        """Test detecting missing applyTo field in instructions file."""
        content = """---
name: some-instruction
---

# Instructions content
"""
        result = validate_file(content, '.instructions.md')
        assert result.status == ValidationStatus.MISSING_FIELDS
        assert 'applyto' in str(result.errors).lower()


class TestValidateSkillFile:
    """Test validation for SKILL.md files."""

    def test_validate_skill_valid(self):
        """Test validation of valid skill file."""
        content = """---
name: brainstorming
description: "Explores user intent"
---

# Skill content
"""
        result = validate_file(content, 'SKILL.md')
        assert result.status == ValidationStatus.VALID
        assert result.errors == []

    def test_validate_skill_missing_name(self):
        """Test that missing name in skill is flagged."""
        content = """---
description: "Explores user intent"
---

# Skill content
"""
        result = validate_file(content, 'SKILL.md')
        assert result.status == ValidationStatus.MISSING_FIELDS
        assert 'name' in str(result.errors).lower()

    def test_validate_skill_missing_description(self):
        """Test that missing description in skill is flagged."""
        content = """---
name: brainstorming
---

# Skill content
"""
        result = validate_file(content, 'SKILL.md')
        assert result.status == ValidationStatus.MISSING_FIELDS
        assert 'description' in str(result.errors).lower()


class TestValidateFileMalformedYAML:
    """Test validation with malformed YAML."""

    def test_validate_malformed_yaml(self):
        """Test that malformed YAML is detected."""
        content = """---
name: test
description: "Unclosed quote
---

# Content
"""
        result = validate_file(content, '.agent.md')
        assert result.status == ValidationStatus.MALFORMED
        assert len(result.errors) > 0
        assert 'yaml' in str(result.errors).lower()


class TestValidateFileNoFrontmatter:
    """Test validation with missing frontmatter."""

    def test_validate_no_frontmatter(self):
        """Test handling files without frontmatter."""
        content = "# Just markdown content"
        result = validate_file(content, '.agent.md')
        assert result.status == ValidationStatus.NO_FRONTMATTER
        assert len(result.errors) == 0

    def test_validate_empty_file(self):
        """Test handling empty files."""
        content = ""
        result = validate_file(content, '.agent.md')
        assert result.status == ValidationStatus.NO_FRONTMATTER
        assert len(result.errors) == 0


class TestValidateUnknownFileType:
    """Test validation with unknown file types."""

    def test_validate_unknown_file_type_raises_error(self):
        """Test that unknown file types raise ValueError."""
        content = """---
name: test
---

# Content
"""
        with pytest.raises(ValueError) as excinfo:
            validate_file(content, '.unknown.md')
        assert 'unknown file type' in str(excinfo.value).lower()
        assert '.unknown.md' in str(excinfo.value)

    def test_validate_unknown_file_type_shows_valid_types(self):
        """Test that error message lists valid file types."""
        content = "# Content"
        with pytest.raises(ValueError) as excinfo:
            validate_file(content, 'invalid')
        error_msg = str(excinfo.value).lower()
        assert '.agent.md' in error_msg
        assert '.instructions.md' in error_msg
        assert 'skill.md' in error_msg
