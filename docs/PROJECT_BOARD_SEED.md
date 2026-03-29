# Project Board Seed

This file describes the initial labels, milestones, and starter issues for a fresh GitHub Project.

## Milestones
- M0 Fork Baseline
- M1 Character Shell
- M2 Talking Sweetie-Bot
- M3 Social Sweetie-Bot
- M4 Convention Demo
- M5 Companion Beta
- M6 Public-Safe Release Candidate

## Recommended starter issues

### M0 Fork Baseline
1. Initialize GitHub hygiene and automation
2. Add `/character` read-only endpoint scaffold
3. Add Character tab shell in the web placeholder
4. Inventory upstream extension points and patch seams

### M1 Character Shell
5. Implement persona state-machine wiring
6. Add emote mapper registry
7. Author first three motion-linked emotes
8. Add routine registry loader

### M2 Talking Sweetie-Bot
9. Add dialogue manager plumbing
10. Add Dialogue tab shell
11. Add phrase-to-emote pairing schema

### M4 Convention Demo
12. Build show-mode operator panel
13. Add session recorder scaffold
14. Author greeting, intro, and bow-exit demo routines

## Suggested status workflow
Backlog → Ready → In Progress → In Review → Done

## Suggested tracks
Runtime, Web, Assets, Ops, Docs

## Seed strategy
Use `scripts/github_seed.py --dry-run` to inspect the proposed labels, milestones, and issues. When ready, run the same script with a GitHub repository argument and an authenticated `gh` CLI session.
