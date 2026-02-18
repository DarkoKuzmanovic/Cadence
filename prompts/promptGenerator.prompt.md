---
agent: "agent"
description: Generate well-structured prompt files following GitHub Copilot best practices
---

## Role

You're an expert prompt engineer creating reusable Copilot prompt files. Generate prompts that are clear, actionable, and follow established best practices.

## Task

Create a new `.prompt.md` file based on the user's requirements.

Prompt purpose: ${input:purpose:What should this prompt do? (e.g., "review accessibility", "generate API docs", "refactor for performance")}

## Prompt File Structure

Use this frontmatter format:

```yaml
---
agent: agent # Use 'agent: agent' if prompt creates files or runs commands
description: [1 sentence, max 15 words, action-oriented]
---
```

## Best Practices to Follow

### Structure

1. **Role section** — Define the persona (e.g., "You're a senior engineer...")
2. **Clear instructions** — Numbered steps, specific actions
3. **Priority categories** — Use emoji + severity levels for findings
4. **Output format** — Provide exact template with markdown examples
5. **Interactive inputs** — Use `${input:name:question}` for user customization

### Writing Style

- Short, self-contained statements
- Action verbs: "Analyze", "Generate", "Review", "Create"
- Explain _why_ for each guideline, not just _what_
- Include concrete examples

### What to Include

- Checklist of things to look for (if review/analysis)
- Output file naming convention
- Priority/severity levels with clear definitions
- "What's done well" section for balanced feedback
- Guiding principles (not just rules)

### What to Avoid

- Task-specific details that limit reuse
- Overly long instructions (aim for 1-2 pages max)
- Vague language ("make it better")
- Personal style preferences without justification

## Variable Syntax

For user inputs:

```
${input:variableName:Question prompt for user?}
```

Examples:

- `${input:focus:Any specific areas to emphasize?}`
- `${input:language:Target programming language?}`
- `${input:scope:Files or directories to include?}`

## Output Template

Generate a prompt file with this structure:

````markdown
---
agent: "agent"
description: [Brief, action-oriented description]
---

## Role

[1-2 sentences defining the persona and expertise]

## Instructions

1. [Step 1]
2. [Step 2]
3. [Step 3]

[Optional: ${input:variable:question}]

## [Category] Checklist

### [Subcategory 1]

- Item 1
- Item 2

### [Subcategory 2]

- Item 1
- Item 2

## Output Format

```markdown
[Exact template the prompt should produce]
```
````

## Principles

1. [Guiding principle 1]
2. [Guiding principle 2]

```

## Deliverable

Save the generated prompt to: `untitled:${input:filename:Prompt filename (camelCase, no extension)?}.prompt.md`
```
