# Security Policy

## Scope
This repository is an early-stage character-robot scaffold. Security matters in three layers:
- source control and supply chain
- web and API surfaces
- robot and accessory safety controls

## Reporting a vulnerability
Please do not post sensitive exploit details in a public issue.
Instead, open a private security advisory on GitHub or contact the maintainers through the most private channel available.

## What counts as security-sensitive here
- authentication or authorization bypass
- unsafe plugin loading or trust-boundary failures
- remote control paths that bypass safety checks
- package supply-chain or secret-leak risks
- workflows that could expose tokens or deployment credentials

## Response goals
- acknowledge the report
- assess scope and reproducibility
- contain high-risk paths first
- patch, document, and add regression coverage where practical
