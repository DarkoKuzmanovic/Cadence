---
description: End session cleanly — summarize progress, update AGENTS.md, create handoff for next session
---

# Session Handoff

Prepare a clean handoff for the next session by documenting what was accomplished and updating project context.

## Steps

1. **Summarize this session:**
   - What was the main goal?
   - What was accomplished?
   - What's left to do?
   - Any blockers or decisions pending?

2. **Update AGENTS.md** with any of the following (if applicable):
   - New conventions discovered
   - Debugging wins (use Lessons Learned format)
   - Architecture decisions made
   - Commands or workflows learned

3. **Create continuation point:**
   - Provide a one-liner to start the next session
   - Format: "Read AGENTS.md and continue with [specific next step]"

## Output Format

```markdown
## Session Summary

**Goal:** [What we set out to do]
**Accomplished:** [What got done]
**Remaining:** [What's left, if anything]

## AGENTS.md Updates

[List what was added/changed, or "No updates needed"]

## Next Session

Start with:

> Read AGENTS.md and [specific continuation instruction]
```

## When to Use

- Context window filling up during long task
- Natural stopping point reached
- Switching to different work
- End of coding session
