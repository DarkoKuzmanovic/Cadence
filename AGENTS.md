# Cadence

A minimal multi-agent orchestration system for VS Code Copilot. 3+1 agents, 3 state files, zero bloat.

## Commands

Use the installer (`python install.py`) or copy files manually:

- **Agents/Instructions:** `~/.config/Code - Insiders/User/prompts/` (Linux)
- **Skills:** `~/.agents/skills/`

See [INSTALL.md](INSTALL.md) for all platforms and recommended VS Code settings.

## Architecture

Multi-agent system with specialized roles:

- **Cadence (Opus 4.6 / Sonnet 4.6):** Planner and orchestrator.
- **Scout (Gemini 3 Flash / Haiku 4.5):** Parallel read-only exploration.
- **Builder (Opus 4.6 / Sonnet 4.6):** TDD implementation.
- **Critic (Opus 4.6 / Sonnet 4.6):** Code review and verification.

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
