"""YAML frontmatter validation for agent and skill files."""

import re
import yaml
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any, List


class ValidationStatus(Enum):
    """Validation status for frontmatter."""
    VALID = "valid"
    INVALID = "invalid"
    MISSING_FIELDS = "missing_fields"
    MALFORMED = "malformed"
    NO_FRONTMATTER = "no_frontmatter"


@dataclass
class ValidationResult:
    """Result of frontmatter validation."""
    status: ValidationStatus
    errors: List[str]
    data: Optional[Dict[str, Any]] = None


def parse_frontmatter(content: str) -> Optional[Dict[str, Any]]:
    """
    Parse YAML frontmatter from file content.

    Args:
        content: File content as string

    Returns:
        Dictionary of parsed YAML data, or None if no frontmatter found

    Raises:
        ValueError: If YAML is malformed
    """
    if not content or not content.strip():
        return None

    # Check if content starts with frontmatter delimiter
    if not content.startswith('---'):
        return None

    # Find the closing delimiter
    # Match from start of string, first --- line, then content, then closing ---
    pattern = r'^---\s*\n(.*?\n)---\s*\n'
    match = re.match(pattern, content, re.DOTALL)

    if not match:
        return None

    yaml_content = match.group(1)

    try:
        data = yaml.safe_load(yaml_content)
        return data if isinstance(data, dict) else None
    except yaml.YAMLError as e:
        raise ValueError(f"Malformed YAML frontmatter: {str(e)}")


def validate_file(content: str, file_type: str) -> ValidationResult:
    """
    Validate YAML frontmatter in agent/instruction/skill files.

    Args:
        content: File content as string
        file_type: File extension/type (.agent.md, .instructions.md, SKILL.md)

    Returns:
        ValidationResult with status and any errors

    Raises:
        ValueError: If file_type is not recognized
    """
    # Validate file_type parameter
    valid_types = ['.agent.md', '.instructions.md', 'SKILL.md']
    if file_type not in valid_types:
        raise ValueError(
            f"Unknown file type: {file_type}. "
            f"Valid types are: {', '.join(valid_types)}"
        )
    # Parse frontmatter
    try:
        data = parse_frontmatter(content)
    except ValueError as e:
        return ValidationResult(
            status=ValidationStatus.MALFORMED,
            errors=[str(e)],
            data=None
        )

    # Handle missing frontmatter
    if data is None:
        return ValidationResult(
            status=ValidationStatus.NO_FRONTMATTER,
            errors=[],
            data=None
        )

    # Determine required fields based on file type
    required_fields = []
    if file_type == '.agent.md':
        required_fields = ['name', 'description']
    elif file_type == '.instructions.md':
        required_fields = ['applyTo']
    elif file_type == 'SKILL.md':
        required_fields = ['name', 'description']

    # Check for missing required fields
    missing_fields = []
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)

    if missing_fields:
        return ValidationResult(
            status=ValidationStatus.MISSING_FIELDS,
            errors=[f"Missing required field(s): {', '.join(missing_fields)}"],
            data=data
        )

    # All validations passed
    return ValidationResult(
        status=ValidationStatus.VALID,
        errors=[],
        data=data
    )
