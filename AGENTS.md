# Cadence

A minimal multi-agent orchestration system for VS Code Copilot. 3+1 agents, 3 state files, zero bloat.

## Commands

Installation is manual. Copy `.agent.md` files to:

- **Linux:** `~/.config/Code - Insiders/User/prompts/`
- **macOS:** `~/Library/Application Support/Code - Insiders/User/prompts/`
- **Windows:** `%APPDATA%\Code - Insiders\User\prompts\`

## Architecture

Multi-agent system with specialized roles:

- **Cadence (Opus):** Planner and orchestrator.
- **Scout (Gemini):** Parallel read-only exploration.
- **Builder (Sonnet):** TDD implementation.
- **Critic (Sonnet):** Optional code review.

## Conventions

- **File Naming:** Agents use `.agent.md` suffix.
- **State Management:** Session state is stored in the `.agents/` directory (gitignored).
- **Core Files:**
  - `plan.md` - Persistent project plan.
  - `state.md` - Current phase status.
  - `decisions.md` - Design decisions and user answers.
- **Design:** Opus handles high-level reasoning; subagents handle parallel or specialized execution.

## Lessons Learned

### 2026-02-17: Initial Setup

**Problem:** Need structured project context for agents.
**Root cause:** Agents lack a unified source of truth for architectural conventions.
**Solution:** Created `AGENTS.md`.
**Prevention:** Always check for `AGENTS.md` at session start.
