---
name: coding-principles
description: Core coding principles for all agents. Use when writing, reviewing, or modifying code. Covers simplicity, surgical changes, goal-driven execution, and regenerability.
---

# Coding Principles

These principles apply to every code change, regardless of language or framework.

## Think Before Coding

- State assumptions explicitly. If uncertain, ask — don't pick an interpretation silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## Simplicity First

- No features beyond what was asked. No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- If you write 200 lines and it could be 50, rewrite it.
- Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## Surgical Changes

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken. Match existing style, even if you'd do it differently.
- If you notice unrelated issues, mention them — don't fix them silently.
- Remove imports/variables/functions that YOUR changes made unused. Don't remove pre-existing dead code unless asked.
- The test: every changed line should trace directly to the task's objective.

## Goal-Driven Execution

Transform tasks into verifiable goals:

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

## Regenerability

- Write code so any file or module can be rewritten from scratch without breaking the system.
- Minimize coupling at module boundaries. Prefer clear, declarative configuration.
- If regenerating a file requires understanding 10 other files, the coupling is too tight.
- Favor explicit dependencies over implicit ones — pass state, don't assume globals.
