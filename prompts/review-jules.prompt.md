# Task: Review & Merge Google Jules PRs

You are reviewing pull requests and branches created by **Google Jules** (`google-labs-jules[bot]`), an AI coding agent that proposes security fixes, performance improvements, test additions, and code quality changes.

Branches follow the naming pattern `origin/[category]-[description]-[id]`.

## Skill Dependency

Read and follow the `gh-cli` skill (`gh-cli/SKILL.md`) for all GitHub CLI operations. Use `gh` commands directly — do not walk the user through manual git steps unless `gh` is unavailable.

## Repository Context

Before reviewing, familiarize yourself with the current repository:

```bash
# Verify gh is authenticated
gh auth status

# Identify default branch and repo info
gh repo view --json defaultBranchRef,name,owner --jq '{repo: "\(.owner.login)/\(.name)", default_branch: .defaultBranchRef.name}'
```

- Read any `AGENTS.md`, `CONTRIBUTING.md`, `ARCHITECTURE.md`, or equivalent docs at the repo root for conventions and architecture
- Check what CI/CD runs on PRs (GitHub Actions, etc.) and what checks must pass
- Note the project's test runner, test file conventions, and coverage expectations

## Workflow

### 0. Discover — List all pending Jules PRs

```bash
# Summary table: number, title, branch, CI status
gh pr list --author "google-labs-jules[bot]" --state open \
  --json number,title,headRefName,labels,statusCheckRollup \
  --jq '.[] | [.number, .title, .headRefName, ([.labels[].name] | join(",")), (if (.statusCheckRollup | length) == 0 then "no checks" elif (.statusCheckRollup | all(.conclusion == "SUCCESS")) then "✅ passing" else "❌ failing" end)] | @tsv' \
  | column -t -s $'\t'
```

Present a summary table to the user before diving into individual reviews. Prioritize: security fixes > bug fixes > test additions > performance > style/chore.

### 1. Assess — Is this PR worth reviewing?

```bash
# Read PR description and metadata
gh pr view <number> --json title,body,labels,files,statusCheckRollup

# Quick file list to gauge scope
gh pr view <number> --json files --jq '.files[].path'
```

- Skip PRs that are clearly noise (e.g., trivial comment rewording, unnecessary abstractions)
- If CI is failing, note it but still review the code — the fix may be valid even if tests need updating

### 2. Review — Apply these criteria

```bash
# Read the full diff
gh pr diff <number>

# Check CI status
gh pr checks <number>
```

**Correctness:**

- Does the change actually fix what it claims to fix?
- Does it introduce new bugs, regressions, or break existing behavior?
- Are edge cases handled? Does it match the existing code patterns?

**Scope:**

- Is the change minimal and surgical? Jules sometimes over-scopes changes.
- Reject or request changes if it refactors unrelated code, adds unnecessary abstractions, or changes public API surface without justification.

**Security (for security-tagged PRs):**

- Does it address a real vulnerability, or is it security theater?
- Is the fix correct and complete, not just a band-aid?
- Does it follow OWASP best practices?

**Performance (for performance-tagged PRs):**

- Is the optimization meaningful or micro-optimization with negligible impact?
- Does it trade readability for marginal gains?
- Are there benchmarks or evidence supporting the improvement?

**Compatibility:**

- Does it maintain compatibility with the project's stated minimum runtime/platform versions?
- Does it avoid using unstable, deprecated, or experimental APIs?

**Style & Conventions:**

- Matches existing code style (no gratuitous reformatting)
- Follows project conventions documented in repo guides
- No unnecessary dependencies added

**Tests (if included):**

- Do tests cover the actual fix/change, not just happy paths?
- Test file location and naming follows the project's existing pattern
- Optionally checkout and run tests locally:

```bash
gh pr checkout <number>
# Run project test command, e.g.: npm test, pytest, etc.
git checkout main
```

### 3. Decide — Execute verdict for each PR

For each PR, execute ONE of:

**✅ MERGE** — Passes all criteria, CI is green, no conflicts:

```bash
gh pr merge <number> --squash --delete-branch \
  --subject "fix: short description" \
  --body "- What was fixed\n- How"
```

Ensure the squash commit message follows the project's commit convention (e.g., conventional commits: `fix:`, `feat:`, `test:`, `perf:`, `chore:`).

**⚠️ REQUEST CHANGES** — Generally good but has specific fixable issues:

```bash
gh pr review <number> --request-changes --body "## Changes Requested

- [ ] Issue 1: description and suggested fix
- [ ] Issue 2: description and suggested fix"
```

**❌ CLOSE/REJECT** — Change is unnecessary, incorrect, or introduces risk:

```bash
gh pr close <number> --delete-branch --comment "Closing: reason for rejection."
```

### 4. Post-merge

- Check if the change warrants updating any project documentation (architecture docs, lessons learned, changelog)
- If the PR fixes a real security issue, note the pattern for future prevention

## Red Flags (auto-reject)

- Adds new dependencies without clear justification
- Changes package manager config (version, scripts, engine requirements) without reason
- Modifies CI/CD workflows
- Removes or weakens existing error handling without explanation
- Suppresses or bypasses type errors, linter rules, or compiler warnings
- Changes that are cosmetic-only with no functional benefit

## Important Notes

- Jules PRs often have long numeric suffixes in branch names — this is normal
- Always verify CI status before merging
- Be skeptical — AI-generated fixes can be superficial or introduce subtle issues. Don't rubber-stamp anything.
- When in doubt, err on the side of rejecting
- If a Jules PR partially overlaps with another Jules PR, review them together for conflicts
- If multiple branches are pending review, present the summary table first with branch name, category, and your verdict before diving into details
