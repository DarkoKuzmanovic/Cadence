---
name: reviewAndFix
description: Review code for issues, prioritize findings, and fix them iteratively
argument-hint: Scope of review (e.g., "staged files", "src/", or specific file)
---

# Review and Fix Workflow

Perform a code quality review, prioritize issues, and fix them iteratively.

## 1. Determine Scope

Review the specified files or, if not specified, all modified/staged files.

## 2. Code Quality Checks

Evaluate against these criteria:

### Cleanliness
- No debug statements (`console.log`, `print`, `debugger`)
- No commented-out code blocks
- No orphaned TODOs without linked issues

### Error Handling
- No empty try-catch blocks
- Errors handled appropriately (logged, propagated, or recovered)
- No silent failures

### Code Style
- Matches project conventions
- Consistent naming
- Reasonable function length

### Security
- No secrets or credentials in code
- User inputs sanitized

### Documentation
- Complex logic has comments
- Public APIs documented

## 3. Report Findings

Categorize issues by priority:

**Must fix:** Bugs, security issues, or code that will break
**Should fix:** Code quality issues, empty error handlers, missing validation
**Consider:** Suggestions for improvement

## 4. Fix Workflow

1. Present findings ranked high to low
2. On user approval, fix issues starting with highest priority
3. After fixes, re-review to verify no regressions
4. Continue until user is satisfied or all issues addressed

## 5. Output Format

```markdown
## Review: [scope]

### Issues Found

**Must fix:**
- [ ] [file:line] Issue description

**Should fix:**
- [ ] [file:line] Issue description

**Consider:**
- [ ] [file:line] Suggestion

### Passed Checks
- [list of clean areas]

### Summary
[Ready to commit / Needs fixes]
```
