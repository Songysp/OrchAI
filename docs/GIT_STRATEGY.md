# Git Strategy

## Default branch

- `main` is the only long-lived branch
- `main` should stay stable and merge-ready

## Working branches

Use short-lived branches by intent:

- `feat/...` for features
- `fix/...` for bug fixes
- `refactor/...` for structural improvements
- `docs/...` for documentation only
- `chore/...` for tooling, CI, and maintenance

Examples:

- `feat/slack-socket-mode`
- `feat/representative-workflow`
- `fix/task-status-transition`
- `refactor/storage-contracts`
- `docs/deployment-guide`
- `chore/github-actions`

## Pull request rules

- Branch from `main`
- Keep PRs small and single-purpose
- Require CI to pass before merge
- Prefer squash merge
- Avoid direct commits to `main`

## Release posture

At the current stage, do not introduce a permanent `develop` branch.

Use:

- feature branches for development,
- `main` for integration,
- tags or GitHub releases later for versioned production milestones.
