---
name: tdd-workflow
description: Test-Driven Development workflow for implementation agents. Use when writing new features, fixing bugs, or refactoring code. Covers red-green-refactor cycle, test patterns, and verification steps.
---

# TDD Workflow

Strict red-green-refactor cycle for all implementation work.

## The Cycle

1. **Red** — Write a failing test that describes the desired behavior. Run it. Confirm it fails for the right reason.
2. **Green** — Write the minimum code to make the test pass. Nothing more.
3. **Refactor** — Clean up without changing behavior. Tests must still pass.
4. **Repeat** — Next behavior, next test.

## Test Writing Principles

- Test behavior, not implementation details.
- One assertion per concept (not necessarily one per test, but each test should verify one logical thing).
- Tests should be readable as documentation — a new developer should understand what the code does by reading the tests.
- Name tests descriptively: `should_reject_empty_email`, `renders_error_state_when_api_fails`.

## Verification Steps

1. Run the individual test file first — faster feedback loop.
2. Run the full test suite — catch regressions.
3. Run linting/formatting — catch style issues.
4. `git diff` — review what you actually changed.

## When to Skip TDD

- Configuration-only changes (env vars, build config).
- Pure documentation.
- Trivial renaming with existing test coverage.

Even in these cases, run the existing test suite to confirm nothing broke.

## Frontend-Specific TDD

For UI components:

1. Write component/interaction tests first (render, user events, state changes).
2. Include accessibility assertions (role, aria-label, keyboard navigation).
3. Build the component to pass.
4. Visual verification is supplementary, not a replacement for tests.
