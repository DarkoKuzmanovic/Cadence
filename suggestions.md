# Cadence Improvement Suggestions

Analysis of all 7 agents, instructions, skills, and prompts against VS Code Insiders 1.109/1.110 capabilities.

---

## 1. Features You're Not Using (High Impact)

### 1.1 Agent Hooks (1.109.3)

Hooks run shell commands at key lifecycle points — deterministic, not AI-guided. None of your agents reference hooks.

**What to add:**

- `PreToolUse` hook on `editFiles` — run linter/formatter automatically after every file edit (eliminates the "run lint" step Builder does manually)
- `PostToolUse` hook on `runInTerminal` — audit trail of all terminal commands agents run
- `SubagentStart` / `SubagentStop` hooks — log which subagents Cadence spawns and when they finish (useful for debugging orchestration)
- `SessionStart` hook — automatically check for `AGENTS.md` existence, read project context

**Setup:** Use `/hooks` slash command in chat, or create `.vscode/hooks.json`. Format is compatible with Claude Code and Copilot CLI.

### 1.2 Terminal Sandboxing (1.109)

Builder, Workhorse, and Frontend-Engineer all have terminal access but zero guardrails. Terminal sandboxing restricts file system access to the workspace folder and controls network access.

**What to add:**

- Enable `chat.tools.terminal.sandbox.enabled` for development
- Configure `chat.tools.terminal.sandbox.network` with trusted domains (npm registry, PyPI, GitHub)
- Document recommended sandbox settings in `INSTALL.md` or a new `.vscode/settings.json` template

**Why:** Prevents agents from accidentally touching files outside the workspace. Builder running `rm -rf` on wrong path is a real risk.

### 1.3 Handoff `model` Parameter (1.109)

Your handoffs don't specify which model to use. Since 1.109, handoffs support an optional `model` parameter.

**Current:**

```yaml
handoffs:
  - label: "✅ Approve Plan → Start Building"
    agent: Cadence
    prompt: "Plan approved. Begin Phase 1 implementation."
    send: false
```

**Suggested:**

```yaml
handoffs:
  - label: "✅ Approve Plan → Start Building"
    agent: Cadence
    prompt: "Plan approved. Begin Phase 1 implementation."
    model: "Claude Opus 4.6 (copilot)"
    send: false
```

This ensures the continuation happens on the right model instead of falling through to whatever is selected.

### 1.4 Mermaid Diagrams (1.109)

The `renderMermaidDiagram` tool is available since 1.109 but none of your agents include it in their tool list. Cadence's plan presentations and Scout's codebase summaries would benefit from visual diagrams.

**What to add:**

- Add `"renderMermaidDiagram"` to Cadence's `tools` list
- Use it in Phase 2 (Plan) to visualize architecture or data flow for complex tasks
- Use it in Scout results to show dependency graphs or call chains

### 1.5 Context Editing for Anthropic (1.109)

`github.copilot.chat.anthropic.contextEditing.enabled` clears tool results and thinking tokens from previous turns, extending effective context in long sessions. Your Cadence orchestrator (which does the longest sessions) would benefit most.

**What to add:**

- Recommend enabling in `INSTALL.md` or settings template
- Particularly important for multi-phase builds (5+ phases) where context exhaustion is real

### 1.6 `disable-model-invocation` on Subagents

Your subagents (Builder, Scout, Critic, Frontend-Engineer, Workhorse) use `user-invocable: false` — good. But they don't set `disable-model-invocation` To prevent the model from auto-invoking them as subagents when they shouldn't be.

**What to add:**

- Add `disable-model-invocation: true` to Critic (should only run during 3B, never auto-invoked)
- Consider it for Scout too (should be invoked deliberately by Cadence, not speculatively)
- Leave it off for Builder and Frontend-Engineer (Cadence needs to invoke these)

Wait — `disable-model-invocation` prevents the model from loading the agent automatically. Since your subagents have `user-invocable: false`, they're already hidden from the dropdown. But without `disable-model-invocation`, the _model itself_ could still decide to invoke them during any session. Adding it gives you explicit control.

### 1.7 Skills as Slash Commands (1.109.3)

Your skills exist but none use the new `user-invokable` or `disable-model-invocation` frontmatter properties to control invocation. Skills now appear in the `/` menu alongside prompts.

**What to add:**

- Add frontmatter to skills that should be user-invokable (e.g., `brainstorming`, `code-review`, `tdd-workflow`)
- Set `disable-model-invocation: true` on utility skills that should only trigger explicitly (e.g., `skill-creator`)

### 1.8 Integrated Browser (1.109)

`vscode/openSimpleBrowser` is in Cadence's tools, but the new Integrated Browser (`workbench.browser.openLocalhostLinks`) is far more capable — supports auth, DevTools, and "Add element to chat".

**What to add:**

- Add `vscode/openIntegratedBrowser` tool to Frontend-Engineer for visual verification
- Recommend `simpleBrowser.useIntegratedBrowser: true` in settings
- Frontend-Engineer could inspect rendered components directly and send elements to chat for analysis

---

## 2. Architecture Improvements

### 2.1 Consolidate Forge + Workhorse

**Problem:** Forge/Workhorse is a parallel orchestration pipeline alongside Cadence/Builder. This creates confusion about which pipeline to use.

- Forge is essentially a prompt-refinement layer → Workhorse (general-purpose coder)
- Cadence is a full lifecycle orchestrator → Builder (TDD specialist)

**Options:**

A. **Remove Forge + Workhorse entirely.** Cadence already does prompt refinement (Phase 0: Understand) better. Builder can handle general tasks. This aligns with "3+1 agents, zero bloat."

B. **Keep Forge as a user-facing lightweight entry point.** Rename its purpose: "For quick tasks that don't need the full Cadence workflow." But then it overlaps with Cadence's Fast-Path Mode.

C. **Merge Workhorse's strengths into Builder.** Builder currently enforces strict TDD. Workhorse is more flexible ("TDD when appropriate"). Make Builder's TDD enforcement configurable via the invocation prompt rather than baked-in.

**Recommendation:** Option A. Your README says "3+1 agents" but you ship 7. Forge and Workhorse add cognitive overhead. If you need a non-TDD builder, just invoke Builder with relaxed acceptance criteria.

### 2.2 Scout's Circular Tool Reference

Scout's tools include `search/searchSubagent`, but Scout IS the search subagent. Remove it:

```yaml
# Remove from Scout's tools:
"search/searchSubagent"
```

Scout should use direct search tools (`search/codebase`, `search/textSearch`, `search/fileSearch`) — not spawn a sub-subagent.

### 2.3 README vs Agent Model Mismatch

README says:

> - **Builder** (Sonnet 4.5) — TDD-driven implementation
> - **Critic** (Sonnet 4.5) — Code review and verification

But the agent files say:

> Builder: `["Claude Opus 4.6 (copilot)", "Claude Sonnet 4.6 (copilot)"]`
> Critic: `["Claude Opus 4.6 (copilot)", "Claude Sonnet 4.6 (copilot)"]`

And Cadence's body text says:

> Builder (Opus 4.6), Critic (Opus 4.6)

**Fix:** Update README to match actual agent file model lists. Also consider whether Builder really needs Opus — Sonnet is faster and cheaper for implementation work. Reserve Opus for planning (Cadence) and complex reviews (Critic).

### 2.4 Inconsistent context7/Upstash Access

| Agent             | Has context7? |
| :---------------- | :------------ |
| Builder           | ✅            |
| Scout             | ✅            |
| Frontend-Engineer | ✅            |
| Workhorse         | ❌            |
| Critic            | ❌            |
| Forge             | ❌            |
| Cadence           | ❌            |

**Fix:** Add `"upstash/context7/*"` to Workhorse (it references context7 in its instructions but doesn't have the tool). Remove from consideration for Forge (it doesn't code) and Cadence (delegates to subagents). Consider adding to Critic for verifying API usage correctness.

### 2.5 Cadence Model Choice

Currently: `["Claude Sonnet 4.6 (copilot)", "Claude Opus 4.6 (copilot)"]`

This means Sonnet is preferred (first in list), with Opus as fallback. For an orchestrator that needs strong reasoning for planning, Opus should be first:

```yaml
model: ["Claude Opus 4.6 (copilot)", "Claude Sonnet 4.6 (copilot)"]
```

Your README even says: "Opus is the planner. Don't delegate planning to a lesser model." Then make sure Cadence defaults to Opus.

---

## 3. New Agents to Consider

Based on your `ideas.md` and the current gaps:

### 3.1 Sentry (Security Reviewer) — Worth Adding

Your Critic agent checks for security issues, but a single bullet point ("No security issues") isn't enough for security-critical code. A dedicated security agent running in parallel with Critic during Phase 3B would add real value.

**Implementation:** Lightweight — mostly a Critic clone with a security-focused system prompt and `search/textSearch` for pattern scanning. Use Sonnet (fast, good at pattern matching).

### 3.2 Scribe (Documentation) — Skip

Your `Initialize.instructions.md` already handles AGENTS.md updates, and CHANGELOG/README updates are simple enough for Builder. A dedicated documentation agent adds overhead without proportional value.

### 3.3 Gardener (Repo Hygiene) — Skip for Now

Useful but rare. Better implemented as a skill (`/repo-hygiene`) that any agent can load on demand, rather than a full agent with its own context window.

### 3.4 Alchemist (Performance) — Skip

Too specialized. Performance work is infrequent and better handled by Builder with a performance-focused invocation prompt.

---

## 4. Settings/Config Recommendations

Recommended VS Code settings to ship alongside Cadence (in INSTALL.md or a `.vscode/settings.json` template):

```jsonc
{
  // Agent features
  "chat.customAgentInSubagent.enabled": true,
  "chat.requestQueuing.enabled": true,
  "chat.requestQueuing.defaultAction": "steer",
  "github.copilot.chat.copilotMemory.enabled": true,
  "chat.useAgentSkills": true,

  // Anthropic optimizations
  "github.copilot.chat.anthropic.contextEditing.enabled": true,
  "github.copilot.chat.anthropic.toolSearchTool.enabled": true,
  "github.copilot.chat.anthropic.thinking.budgetTokens": 10000,

  // Terminal safety
  "chat.tools.terminal.sandbox.enabled": true,

  // Search
  "github.copilot.chat.searchSubagent.enabled": true,

  // Browser
  "simpleBrowser.useIntegratedBrowser": true,

  // Skills locations (if not defaults)
  "chat.agentSkillsLocations": {
    "~/.agents/skills": true,
  },

  // Agent files locations
  "chat.agentFilesLocations": {
    "~/.config/Code - Insiders/User/prompts": true,
  },
}
```

---

## 5. Skill Gaps

### 5.1 Agent-Ops Skill (from ideas.md) — Add This

A skill teaching agents VS Code Agent Platform internals: parallelization rules, `askQuestions` patterns, Copilot Memory usage, context window management. Cadence would load this automatically.

### 5.2 Writing-Clearly Skill — You Have This but It's Not in the Repo

Your `~/.agents/skills/writing-clearly-and-concisely/` exists in your home directory but isn't distributed with Cadence. Consider including it if Cadence is meant to be shared.

### 5.3 Design-Engineer / Frontend-Design Skills — Same Issue

These exist in your home directory but not in the repo. Frontend-Engineer should auto-load these.

---

## 6. Quick Wins (Low Effort, Immediate Value)

| #   | Change                                         | File(s)                             | Effort |
| --- | ---------------------------------------------- | ----------------------------------- | ------ |
| 1   | Fix Cadence model order (Opus first)           | `Cadence.agent.md`                  | 1 min  |
| 2   | Remove `search/searchSubagent` from Scout      | `Scout.agent.md`                    | 1 min  |
| 3   | Add `renderMermaidDiagram` to Cadence tools    | `Cadence.agent.md`                  | 1 min  |
| 4   | Add `upstash/context7/*` to Workhorse          | `Workhorse.agent.md`                | 1 min  |
| 5   | Add `model` param to handoffs                  | `Cadence.agent.md`                  | 2 min  |
| 6   | Fix README model mismatch                      | `README.md`                         | 5 min  |
| 7   | Add recommended settings to INSTALL.md         | `INSTALL.md`                        | 10 min |
| 8   | Add `disable-model-invocation` to Critic/Scout | `Critic.agent.md`, `Scout.agent.md` | 2 min  |

---

## 7. Things That Are Working Well (Don't Touch)

- **File-conflict detection** before parallel execution — unique and valuable
- **Invocation templates** — structured, avoids context leaks between agents
- **Fast-Path Mode** — smart optimization for trivial tasks
- **Crash recovery** protocol with Copilot Memory + state files
- **Stopping rules** — mandatory pauses at the right moments
- **WHAT not HOW delegation** — prevents over-specification
- **Builder's TDD enforcement** — strict but effective
- **Critic's structured review format** — clear, actionable
- **Context conservation** strategies in Cadence
- **Model fallback lists** everywhere — handles model unavailability gracefully

---

## 8. Risks/Anti-patterns to Watch

1. **Context window bloat from state files.** `.agents/plan.md` grows with each phase. For 8-phase plans, the plan file alone could consume significant context. Consider keeping only the current + next phase in active context and summarizing completed phases.

2. **Over-orchestration.** Cadence's full workflow (understand → scout → plan → build → review → commit) adds 5 mandatory subagent invocations per phase. For a 5-phase project that's 25+ subagent calls. Consider making Phase 1 (Scout) and Phase 3B (Critic) optional for phases where the scope is well-understood.

3. **Memory-to-file duplication.** Cadence writes to both `.agents/state.md` AND Copilot Memory. If they diverge, the crash recovery protocol doesn't specify which takes precedence. Make the priority explicit: Copilot Memory > state files (memory survives workspace resets).

4. **Forge's `unipilot.nanogpt` model reference.** `"Gemini 3 Flash (Preview) (unipilot.nanogpt)"` — this appears to be a non-standard provider. If this is an internal/custom model provider, document it. If it's a typo or deprecated, remove it.

---

## GPT-5.2 Comments (2026-02-18)

Notes on the quality/accuracy of this doc and a few additions. I did not apply any of these changes to agent files.

- **Verified (repo reality):** Model mismatch callout is real: `README.md` says Builder/Critic are Sonnet 4.5, but `agents/Builder.agent.md` and `agents/Critic.agent.md` list Opus/Sonnet 4.6, and `agents/Cadence.agent.md` text labels Builder/Critic as Opus. Tighten this into a single source of truth (README vs agent frontmatter vs agent body text).
- **Verified:** Scout currently includes `search/searchSubagent` in `agents/Scout.agent.md`. Removing it is a clean simplification.
- **Verified:** Workhorse references Context7 in prose but lacks `upstash/context7/*` in `agents/Workhorse.agent.md`. Either add the tool or remove the instruction line to avoid “paper capabilities.”
- **File path clarity:** Quick Wins table references `Cadence.agent.md`, `Scout.agent.md`, etc. In the repo they live under `agents/`. If you meant “installed file name”, say so explicitly; otherwise use `agents/Cadence.agent.md` etc to reduce confusion.
- **Hooks section tweak:** If the goal is “auto-format after edits,” the hook wants to run _after_ `edit/editFiles` completes (not `PreToolUse`). Also align names with real tool IDs (`edit/editFiles`, `execute/runInTerminal`) so the doc is copy/pasteable.
- **Hooks safety:** Document guardrails: keep hook commands fast/idempotent, and prefer formatting only changed files (avoid “run full lint suite on every edit”).
- **Tool IDs need verification:** `renderMermaidDiagram` and `vscode/openIntegratedBrowser` might not be the exact tool names Copilot exposes. Recommend adding a short “confirm tool IDs” checklist (e.g., check the tool picker / agent template docs) so this doc stays correct across Insiders updates.
- **Handoff `model` parameter:** Worth trying, but call out brittleness: model display strings change. Prefer stable IDs if supported; if not, at least keep the string identical to the agent’s `model:` entries.
- **`disable-model-invocation` semantics:** Add a warning to verify that setting it does not prevent Cadence from invoking the agent via `agent` tool. (If it blocks _all_ invocation, it will break the workflow.)
- **Settings template realism:** VS Code settings often do not expand `~`. Consider `${env:HOME}` (and Windows/macOS equivalents) for `chat.agentSkillsLocations` / `chat.agentFilesLocations`, or document “paste absolute paths.” Also mark which keys are “must-have” vs “nice-to-have.”
- **“3+1 agents” alignment:** If you keep Forge/Workhorse/Frontend-Engineer, consider reframing the tagline as “3+1 core + optional extras,” or make the installer default to core-only and install extras via a flag. Otherwise the doc/README will keep drifting from the shipped surface area.
- **Security reviewer alternative:** Before adding a new Sentry agent, consider a small "Security pass" section in Critic's required output (1-2 bullets for secrets, injection, unsafe filesystem/commands) or a `/security-review` skill. It keeps agent count down while improving depth.

---

## Claude Opus 4.6 Comments (2026-02-18)

Review of the suggestions doc, GPT-5.2's notes, and the actual agent files. I applied the changes marked with [APPLIED] below.

### Agreements with the original analysis

- **[APPLIED] Cadence model order:** Confirmed. Sonnet was listed first but your README says "Opus is the planner." Swapped to Opus-first.
- **[APPLIED] Scout's circular tool:** Confirmed. `search/searchSubagent` in Scout is nonsensical — Scout IS the search subagent. Removed.
- **[APPLIED] Workhorse missing context7:** Confirmed. The prose says "use context7 MCP" but the tool isn't in the frontmatter. Added `upstash/context7/*`.
- **[APPLIED] README model mismatch:** Three sources of truth (README, agent frontmatter, Cadence body text) all disagreed. Unified: README now matches frontmatter. Builder lists Opus/Sonnet 4.6, Critic lists Opus/Sonnet 4.6, Cadence body text already said Opus 4.6.
- **[APPLIED] `disable-model-invocation` on Critic/Scout:** Added to both. These should only be invoked deliberately by Cadence, never auto-loaded by the model.
- **[APPLIED] Handoff `model` parameter:** Added to both Cadence handoffs, using the same string as Cadence's own `model:` list (Opus first) per GPT-5.2's brittleness warning.

### Agreements with GPT-5.2

- **Hooks naming:** GPT-5.2 is right that `PreToolUse` is wrong for auto-formatting — you want `PostToolUse` on `edit/editFiles`. The original doc's suggestion would fire the linter _before_ the edit completes, which is useless.
- **Tool ID verification:** `renderMermaidDiagram` and `vscode/openIntegratedBrowser` are not confirmed tool IDs. I did not add these to any agent files. Verify by checking the tool picker in VS Code Insiders before adding.
- **Security in Critic vs new agent:** Agree with GPT-5.2. I did NOT add a Sentry agent. Instead, Critic already checks for security — if you want more depth, expand Critic's security checklist or add a `/security-review` skill.
- **Settings `~` expansion:** GPT-5.2 is correct that VS Code doesn't expand `~` in settings. Use `${env:HOME}` or document absolute paths.

### Disagreements / additional observations

- **Forge/Workhorse removal (Section 2.1, Option A):** The original doc recommends removing Forge+Workhorse entirely. I left them untouched. They serve a different use case — Forge is a user-facing lightweight entry point for quick tasks that don't need the full Cadence ceremony. If you do want to consolidate, Option C (make Builder's TDD configurable) is the safer path. Removing agents is easy; the hard part is making sure Cadence's Fast-Path Mode truly covers all of Forge's use cases (it currently doesn't — Forge does prompt refinement, Cadence's fast-path skips it).
- **Forge's `unipilot.nanogpt` model:** The original doc flags this as potentially non-standard. It IS non-standard — this appears to be a custom model provider (NanoGPT/UniPilot). If this is intentional, document it in INSTALL.md. If it's leftover from experimentation, clean it up. I left it as-is since I can't verify your setup.
- **Builder on Opus vs Sonnet:** The original doc questions whether Builder needs Opus. Builder currently lists Opus first, Sonnet as fallback. For implementation work (not planning), Sonnet 4.6 is typically sufficient and faster. Consider swapping Builder to Sonnet-first: `["Claude Sonnet 4.6 (copilot)", "Claude Opus 4.6 (copilot)"]`. This would match the original design philosophy in your README. I did NOT make this change — it's a judgment call about cost/speed vs capability.
- **Frontend-Engineer model:** Currently `Gemini 3 Pro` first, Sonnet fallback. This is fine for UI work, but note that Gemini models may handle Copilot agent tool calls differently than Claude/Anthropic models. If you hit issues with Frontend-Engineer not using tools correctly, try swapping to Sonnet-first.
- **Context window bloat (Section 8.1):** The plan file growing unboundedly is a real risk. Consider adding a line to Cadence's Phase 3C (commit step) that says: "For plans with >5 phases, summarize completed phases to a single status line in `.agents/plan.md` to conserve context." I did NOT edit this into Cadence's instructions — it's a behavior change that needs your review.
- **Crash recovery priority:** The original doc (Section 8.3) notes that Copilot Memory and state files could diverge. Cadence's crash recovery section reads both but doesn't specify precedence. Add: "If Copilot Memory and `.agents/state.md` conflict, trust Copilot Memory (survives workspace resets)." I did NOT add this — it changes recovery behavior.
- **Missing `renderMermaidDiagram`:** I did NOT add this tool to Cadence despite the original recommendation. The tool ID needs verification first (per GPT-5.2). Once confirmed, it would be a good addition for plan visualization.
- **Scout model choice is smart:** Gemini 3 Flash for exploration with Haiku 4.5 fallback is a good cost optimization. Fast models for read-only search work is the right call.
