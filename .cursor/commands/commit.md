# Create Git Commit

Create a git commit that captures staged & unstaged changes with a clear, descriptive commit message.

## Pre-flight Checks

1. **Verify staged changes exist:**
   - If no staged changes are detected, inform the user and do NOT proceed

2. **Check repository state:**
   - Ensure no merge conflicts exist before proceeding

## Creating the Commit Message

1. **Analyze staged changes:**
   - Review what was modified to understand the scope and type of changes
   - Categorize changes (feature, bugfix, refactor, docs, test, etc.)

2. **Follow conventional commit format:**
   - Format: `<type>(<scope>): <subject>`
   - Common types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
   - Subject: imperative mood, lowercase, under 50 characters, no period
   - Add body if more explanation is needed

3. **Write clear, specific messages:**
   - Focus on what changed
   - Avoid generic messages like "fix bug"
   - Use present tense ("add feature" not "added feature")

## Examples

- `feat(api): add user registration endpoint`
- `fix(ui): correct button alignment in mobile view`
- `docs(readme): update installation instructions`
- `refactor(auth): simplify token validation logic`
