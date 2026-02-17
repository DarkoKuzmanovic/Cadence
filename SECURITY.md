# Security Policy

## Supported Versions

Currently supported versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in Cadence, please report it by emailing **darko.kuzmanovic@gmail.com**.

**Please do not** report security vulnerabilities through public GitHub issues.

### What to include in your report:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if you have one)

### What to expect:

- You will receive a response within 48 hours acknowledging receipt of your report
- We will investigate and provide an estimated timeline for a fix
- We will notify you when the vulnerability is fixed
- We will credit you in the release notes (unless you prefer to remain anonymous)

## Security Considerations

When using Cadence:

- **File Permissions**: The installer modifies files in your VS Code user directory. Ensure you trust the source repository.
- **YAML Parsing**: We use `yaml.safe_load()` to prevent code injection through YAML files.
- **Path Traversal**: User-supplied paths are resolved using `pathlib.Path` but should still be from trusted sources.
- **Backups**: All overwrites create automatic backups in `~/.agents/backups/` for recovery.

## Best Practices

1. Always review agent files before installation
2. Run the installer from a trusted repository copy
3. Use `--dry-run` flag to preview changes before applying
4. Regularly back up your VS Code configuration
5. Keep the installer updated to the latest version
