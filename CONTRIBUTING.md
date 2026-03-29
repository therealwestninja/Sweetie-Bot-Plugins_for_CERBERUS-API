# Contributing

## Philosophy
This repository starts as an architecture and planning scaffold.
Contributions should improve clarity, structure, contracts, or carefully isolated implementation stubs.

## Contribution priorities
1. documentation quality
2. interface contracts
3. placeholder code structure
4. tests for schemas and loaders
5. tooling that helps inventory or package assets

## Ground rules
- preserve mergeability
- avoid rewriting the runtime core in-place
- keep character content in assets when practical
- document assumptions
- prefer additive change over invasive refactors in this stage

## Commit style
Suggested prefixes:
- docs:
- feat:
- fix:
- chore:
- test:
- refactor:

## Pull request checklist
- [ ] documents updated
- [ ] contracts updated if interfaces changed
- [ ] tests added or updated where appropriate
- [ ] no hidden safety regressions introduced
