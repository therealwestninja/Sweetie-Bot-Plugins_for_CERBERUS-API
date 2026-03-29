from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass, field


@dataclass
class Label:
    name: str
    color: str
    description: str


@dataclass
class IssueSeed:
    title: str
    body: str
    labels: list[str] = field(default_factory=list)
    milestone: str | None = None


LABELS = [
    Label("triage", "D4C5F9", "Needs review and routing."),
    Label("type: bug", "d73a4a", "Something is broken."),
    Label("type: feature", "0e8a16", "New capability or enhancement."),
    Label("type: task", "1d76db", "Focused implementation or maintenance work."),
    Label("type: docs", "0075ca", "Documentation-only work."),
    Label("area: api", "5319e7", "Backend, runtime, or plugin work."),
    Label("area: web", "5319e7", "Operator UI or authoring surface."),
    Label("area: assets", "c5def5", "Persona, dialogue, or routine content."),
    Label("area: convention-demo", "f9d0c4", "Demo-floor and show-mode work."),
    Label("safety", "000000", "Motion or public-demo safety concern."),
]

MILESTONES = [
    "M0 Fork Baseline",
    "M1 Character Shell",
    "M2 Talking Sweetie-Bot",
    "M3 Social Sweetie-Bot",
    "M4 Convention Demo",
    "M5 Companion Beta",
    "M6 Public-Safe Release Candidate",
]

ISSUES = [
    IssueSeed(
        title="Initialize GitHub hygiene and automation",
        body=(
            "Add repo hygiene defaults, workflows, templates, and local "
            "developer commands."
        ),
        labels=["type: task", "type: docs", "triage"],
        milestone="M0 Fork Baseline",
    ),
    IssueSeed(
        title="Add /character read-only endpoint scaffold",
        body=(
            "Expose persona, mood, active routine, and attention summary "
            "through a thin read-only API surface."
        ),
        labels=["type: task", "area: api", "triage"],
        milestone="M0 Fork Baseline",
    ),
    IssueSeed(
        title="Add Character tab shell in the web placeholder",
        body=(
            "Create a basic operator-facing Character tab wired to the new "
            "read-only endpoint and websocket placeholders."
        ),
        labels=["type: task", "area: web", "triage"],
        milestone="M0 Fork Baseline",
    ),
    IssueSeed(
        title="Author the first convention-demo routines",
        body=(
            "Create greeting, intro, and bow-exit demo routines with asset "
            "metadata and operator notes."
        ),
        labels=["type: task", "area: assets", "area: convention-demo", "triage"],
        milestone="M4 Convention Demo",
    ),
]


def run(cmd: list[str], dry_run: bool) -> None:
    rendered = " ".join(cmd)
    print(f"$ {rendered}")
    if not dry_run:
        subprocess.run(cmd, check=True)


def seed(repo: str, dry_run: bool) -> None:
    for label in LABELS:
        run(
            [
                "gh",
                "label",
                "create",
                label.name,
                "--repo",
                repo,
                "--color",
                label.color,
                "--description",
                label.description,
                "--force",
            ],
            dry_run,
        )

    for milestone in MILESTONES:
        run(
            [
                "gh",
                "api",
                f"repos/{repo}/milestones",
                "--method",
                "POST",
                "-f",
                f"title={milestone}",
            ],
            dry_run,
        )

    for issue in ISSUES:
        cmd = [
            "gh",
            "issue",
            "create",
            "--repo",
            repo,
            "--title",
            issue.title,
            "--body",
            issue.body,
        ]
        for label in issue.labels:
            cmd.extend(["--label", label])
        if issue.milestone:
            cmd.extend(["--milestone", issue.milestone])
        run(cmd, dry_run)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed labels, milestones, and starter issues on GitHub."
    )
    parser.add_argument("--repo", help="owner/name of the GitHub repository")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without executing them",
    )
    args = parser.parse_args()

    if not args.repo and not args.dry_run:
        parser.error("--repo is required unless --dry-run is used")

    repo = args.repo or "owner/repo"
    seed(repo, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
