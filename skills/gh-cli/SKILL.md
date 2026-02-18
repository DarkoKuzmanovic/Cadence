---
name: gh-cli
description: GitHub CLI (gh) wrapper for PR review workflows. Use when reviewing, merging, or managing pull requests and branches via the command line. Covers listing PRs, viewing diffs, checking CI status, leaving reviews, and merging.
user-invocable: true
---

# GitHub CLI Skill

Reusable `gh` CLI patterns for pull request review, triage, and merge workflows.

## Prerequisites

- `gh` CLI installed and authenticated (`gh auth status` to verify)
- Current directory is inside the target git repository

## Quick Reference

### List & Filter PRs

```bash
# All open PRs
gh pr list --state open

# PRs by a specific author (e.g., Jules bot)
gh pr list --author "google-labs-jules[bot]" --state open

# PRs with specific label
gh pr list --label "security" --state open

# JSON output for scripting (customize fields as needed)
gh pr list --author "google-labs-jules[bot]" --json number,title,headRefName,labels,createdAt,statusCheckRollup
```

### View PR Details

```bash
# Summary view
gh pr view <number>

# Full diff
gh pr diff <number>

# PR body/description only
gh pr view <number> --json body --jq '.body'

# Files changed
gh pr view <number> --json files --jq '.files[].path'

# Check CI status
gh pr checks <number>

# View specific fields as JSON
gh pr view <number> --json title,body,labels,reviews,statusCheckRollup,mergeable,headRefName
```

### Review a PR

```bash
# Approve
gh pr review <number> --approve --body "LGTM — reviewed criteria X, Y, Z."

# Request changes
gh pr review <number> --request-changes --body "Specific feedback here."

# Comment only (no verdict)
gh pr review <number> --comment --body "Question about the approach..."
```

### Merge a PR

```bash
# Squash merge (preferred for clean history)
gh pr merge <number> --squash --subject "fix: description" --body "- Detail 1\n- Detail 2"

# Squash merge and delete the remote branch
gh pr merge <number> --squash --delete-branch --subject "fix: description"

# Merge commit (preserves individual commits)
gh pr merge <number> --merge

# Rebase merge
gh pr merge <number> --rebase
```

### Close / Reject a PR

```bash
# Close with comment
gh pr close <number> --comment "Closing because: reason."

# Close and delete the branch
gh pr close <number> --delete-branch --comment "Reason for rejection."
```

### Branch Operations

```bash
# Checkout a PR branch locally (for deeper inspection)
gh pr checkout <number>

# Return to default branch
git checkout main  # or master, develop, etc.

# List remote branches matching a pattern (e.g., Jules branches)
git branch -r | grep -E "(security|performance|test|fix|chore)-.*-[0-9]+"
```

### Batch Operations

```bash
# Get all Jules PR numbers
gh pr list --author "google-labs-jules[bot]" --json number --jq '.[].number'

# Check CI status for all Jules PRs
for pr in $(gh pr list --author "google-labs-jules[bot]" --json number --jq '.[].number'); do
  echo "PR #$pr:"
  gh pr checks "$pr" 2>/dev/null || echo "  No checks"
  echo ""
done

# Summary table of all Jules PRs (number, title, branch, CI status)
gh pr list --author "google-labs-jules[bot]" \
  --json number,title,headRefName,statusCheckRollup \
  --jq '.[] | [.number, .title, .headRefName, (if (.statusCheckRollup | length) == 0 then "no checks" elif (.statusCheckRollup | all(.conclusion == "SUCCESS")) then "✅ passing" else "❌ failing" end)] | @tsv' \
  | column -t -s $'\t'
```

### Useful Aliases

```bash
# Add to ~/.config/gh/config.yml or run:
gh alias set jules-prs 'pr list --author "google-labs-jules[bot]" --state open'
gh alias set pr-summary 'pr view $1 --json title,body,labels,files,statusCheckRollup'
```

## Workflow Pattern: Review a Jules PR

Typical sequence for reviewing a single PR end-to-end:

```bash
# 1. See what's pending
gh pr list --author "google-labs-jules[bot]" --state open

# 2. Pick a PR and view it
gh pr view <number>

# 3. Check CI
gh pr checks <number>

# 4. Read the diff
gh pr diff <number>

# 5. (Optional) Checkout locally to run tests
gh pr checkout <number>
npm test  # or project-specific command
git checkout main

# 6. Decide: approve + merge, request changes, or close
gh pr merge <number> --squash --delete-branch --subject "fix: description"
# OR
gh pr review <number> --request-changes --body "Feedback."
# OR
gh pr close <number> --delete-branch --comment "Reason."
```

## Error Handling

- **"no checks reported"** — The repo may not have CI configured, or checks haven't started yet. Wait or verify manually.
- **"not mergeable"** — Conflicts exist. Checkout the branch and resolve, or close the PR.
- **Auth issues** — Run `gh auth status` and `gh auth login` if needed.
- **Rate limits** — Use `--json` output and minimize API calls in loops. Add `sleep 1` between batch calls if hitting limits.
