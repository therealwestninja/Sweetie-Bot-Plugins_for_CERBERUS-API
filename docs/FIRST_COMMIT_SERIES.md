# First Commit Series

This repo is still a scaffold, so the fastest path to a clean public history is a deliberate first commit series rather than one giant dump.

## Suggested commit sequence

1. **chore: initialize github hygiene**
   - add `.editorconfig`
   - add `.gitignore` touchups if needed
   - add `CODEOWNERS`, `SECURITY`, `SUPPORT`, and PR template

2. **ci: add baseline workflows**
   - add Python CI
   - add docs hygiene workflow
   - add release-draft workflow
   - add Dependabot

3. **docs: tighten readme and contribution flow**
   - update `README.md`
   - update `CONTRIBUTING.md`
   - add `docs/FIRST_COMMIT_SERIES.md`
   - add `docs/PROJECT_BOARD_SEED.md`

4. **feat: add issue forms and labels**
   - add issue forms for bugs, features, slices, and convention-demo tasks
   - add `.github/labels.yml`

5. **feat: add project board seed and gh helper script**
   - add `.github/project-board-seed.yml`
   - add `scripts/github_seed.py`

6. **refactor: bump scaffold version to 0.0.2**
   - update version strings
   - update changelog

7. **test: tighten local developer loop**
   - add `Makefile`
   - add pre-commit config
   - verify tests and lint

8. **docs: publish initial milestones and seeded issues**
   - create milestones on GitHub
   - open the first set of tracking issues from `docs/PROJECT_BOARD_SEED.md`

## Why this order works
The early commits make the repo easier to review and safer to collaborate in before any deeper implementation work starts.
