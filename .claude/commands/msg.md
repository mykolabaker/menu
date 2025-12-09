# Git Commit Plan Generator

## Command

First, determine the subproject name by getting the basename of the current working directory. This will be used as a prefix for all commit messages.

Review git changes in the current project directory only using `git status --porcelain .` and `git diff --stat .` and `git diff .`. Ignore changes in other monorepo projects. **Exclude any files that are ignored by .gitignore** - only include files that git is actually tracking or will track. Group related changes into logical commits. For each commit, provide a lowercase commit message with the subproject prefix and list of affected files.

## Grouping Strategy

**Prefer fewer, larger commits** that group related changes by:
1. **Feature/functionality** - Changes that implement a single feature together
2. **Refactoring scope** - Related code improvements that serve one goal
3. **Subsystem** - Changes to a specific component or module
4. **Migration/infrastructure** - Moving or reorganizing code

**Avoid tiny commits** unless changes are truly unrelated.

## Output Format

For each suggested commit, output:
1. **Commit message**: "{subproject} - " prefix followed by lowercase, past tense, no period (5-10 words after prefix)
2. **Executable git commands**: Multiline commands with file list included

**Important**: Before generating commands, use `git status --porcelain` to identify tracked/untracked files, and exclude any files that are ignored by .gitignore. Only include files that git will actually add.

Use `\` for line continuation to keep commands readable. Use `git add -A` to handle modified and deleted files.

```bash
# Commit 1: {subproject} - <commit message>

git add -A \
  path/to/file1.ext \
  path/to/file2.ext \
  path/to/file3.ext
git commit -m "{subproject} - <commit message>"
```

## Commit Message Rules

1. **Subproject prefix**: Always start with "{subproject} - " where subproject is the basename of the current directory
2. **Lowercase only**
3. **Past tense** (e.g., "added" not "add")
4. **Concise and descriptive** (typically 5-10 words after the prefix)
5. **Include "why" when it adds clarity** (e.g., "migrated auth to shared library for reuse")
6. **Prefer specific verbs**: "implemented", "refactored", "fixed", "updated", "removed", "migrated", "integrated"
7. **No period at the end**
8. **No attribution footer**: Do NOT add Claude Code attribution or Co-Authored-By lines

**Format**: `{subproject} - {lowercase past tense description}`

**IMPORTANT**: The commit message should be clean and simple, with NO additional attribution, footers, or metadata. Just provide the commands as shown in the examples - the user will execute them directly.

## Examples

Assuming the subproject is named "myproject":

### Single cohesive change
```bash
# Commit 1: myproject - migrated webcache and s3 clients to crawler utils shared library

git add -A \
  libs/crawler_utils/__init__.py \
  libs/crawler_utils/pyproject.toml \
  libs/crawler_utils/webcache_client.py \
  libs/crawler_utils/s3_client.py \
  monitor/src/common/webcache_client.py \
  monitor/src/workers/recon.py
git commit -m "myproject - migrated webcache and s3 clients to crawler utils shared library"
```

### Multiple related commits
```bash
# Commit 1: myproject - added claude code commands for commit messages and code review

git add -A \
  .claude/commands/cr.md \
  .claude/commands/msg.md
git commit -m "myproject - added claude code commands for commit messages and code review"

# Commit 2: myproject - improved icypeas integration with scoring and exploration script

git add -A \
  moab/src/api/app.py \
  moab/src/utils/__init__.py \
  scripts/dev/explore_icypeas.py
git commit -m "myproject - improved icypeas integration with scoring and exploration script"
```

### Everything in one commit (when changes are tightly coupled)
```bash
# Commit 1: myproject - implemented user authentication with session management and tests

git add -A \
  src/auth/middleware.py \
  src/auth/session.py \
  src/models/user.py \
  src/api/routes.py \
  tests/test_auth.py \
  requirements.txt
git commit -m "myproject - implemented user authentication with session management and tests"
```

## Usage Notes

- **Bias toward fewer commits**: Combine changes that work together
- **Group by purpose, not file type**: Don't separate tests from implementation
- **Include context in message**: Help future developers understand the change
- **Use multiline format**: Break long file lists across multiple lines with `\` continuation

## All-in-One Alternative

After showing the individual commits, provide an alternative single commit that combines all changes:

```bash
Alternative: All in one commit

git add -A .
git commit -m "{subproject} - <comma-delimited list of changes without repeating subproject>"
```

**Format rules for the combined message**:
1. Start with "{subproject} - " prefix (only once)
2. List all changes separated by commas
3. Each change should be past tense, lowercase
4. NO subproject prefix on individual items (it's only at the start)
5. Keep it concise and readable

**Example**:
If individual commits are:
- Commit 1: myproject - added feature A
- Commit 2: myproject - fixed bug B
- Commit 3: myproject - updated config C

The combined message would be:
```bash
# Alternative: All in one commit

git add -A .
git commit -m "myproject - added feature A, fixed bug B, updated config C"
```
