---
name: regression-and-changelog-discipline
description: Use when modifying existing codebases or fixing bugs.
---
<body>
1. Never modify files in `tests/` unless explicitly creating new test files.
2. For every bug fixed, create a dedicated test function in a new test file that reproduces the issue.
3. Ensure all new tests pass before finalizing the task.
4. Update `CHANGELOG.md` immediately after a fix, using the exact format requested (e.g., `## Unreleased` heading and `- fix(<function>): <description>` bullets).
5. Verify that all public functions have type annotations as required by the project rules.

Self-check:
- [ ] Did I add a regression test for every fix?
- [ ] Is `CHANGELOG.md` updated with the correct format?
- [ ] Are all public functions type-annotated?
- [ ] Did I leave the original test files untouched?
</body>
