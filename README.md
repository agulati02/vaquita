# Vaquita

> AI-powered release notes for repositories that ship faster than humans can document.

---

## The problem

As coding agents become primary contributors to codebases, commit and PR volume is decoupling from human review and documentation capacity by an order of magnitude. The result: maintainers defer release notes entirely, leaving intermediate releases effectively undocumented for the people who depend on them.

The challenge isn't volume alone — it's *signal extraction at volume*: distinguishing breaking changes from noise, grouping semantically related commits, and inferring user-visible impact from diffs written by agents for agents.

## What Vaquita does

Vaquita is a CI utility that reads your diffs, understands them, and generates structured release notes — grounded in actual commits and PRs, not hallucinated summaries.

It fits into your existing release workflow as a CI step. On a tag or release event, Vaquita runs, generates the notes, and hands them back to you for final review and publishing. Human judgment stays in the loop; the volume problem doesn't.

Specifically, it handles:

- **High-velocity repositories** where commit and PR volume has outpaced human documentation capacity
- **Agent-authored code** where commit messages and PR descriptions are terse, inconsistent, or written for tooling rather than humans
- **Multi-contributor projects** where no single person has the full context to write release notes from scratch
- **Accuracy and trust** — notes are grounded in the actual diff and linked to the commits and PRs that produced them, so reviewers can verify every claim before publishing

## Installation

```bash
pip install vaquita
```

Or with `uv`:

```bash
uv add vaquita
```

## Quick start

```bash
# Generate release notes between two refs
vaquita generate --from v1.0.0 --to v1.1.0
```

## CI integration

Vaquita is designed to run as a CI step. GitHub Actions is the primary integration target, but the core is not GitHub-specific — it runs anywhere you can run automation against a Git repository.

```yaml
# .github/workflows/release.yml
- name: Generate release notes
  run: vaquita generate --from ${{ github.event.release.target_commitish }} --to ${{ github.sha }}
```

> Full GitHub Actions integration guide coming soon.

## Requirements

- Python >= 3.13

## Status

Early development — `v0.1.0`. APIs and CLI flags are subject to change.

## License

See [LICENSE](LICENSE).
