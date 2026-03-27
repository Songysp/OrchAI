# Deployment Strategy

## Recommended flow

This repository uses GitHub Actions for CI first, then layered CD.

- Feature branches run CI only
- `main` runs CI and publishes a Docker image to GHCR
- `staging` is the first automated deployment target
- `production` should remain approval-gated through GitHub Environments

## Workflows

### `ci.yml`

Runs on pull requests and pushes to `main`.

- installs Python dependencies,
- runs `ruff`,
- compiles Python sources,
- runs `pytest`,
- validates the Docker build.

### `docker.yml`

Runs on pushes to `main` and on manual dispatch.

- builds the Docker image from `infra/Dockerfile`,
- pushes the image to `ghcr.io/<owner>/<repo>`,
- tags the image with `latest` and the commit SHA.

### `deploy-staging.yml`

Prepared as the first deployment automation entry point.

Recommended next step:

- connect staging infrastructure,
- pull the latest GHCR image,
- deploy the service,
- verify `GET /health`.

### `deploy-production.yml`

Prepared as a manual, approval-gated production deployment entry point.

Recommended next step:

- protect the `production` environment with reviewers,
- deploy a tested image,
- verify health checks after deployment.

## GitHub Environments

Create these environments in GitHub:

- `staging`
- `production`

Recommended secret split:

### Shared build/runtime secrets

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GEMINI_API_KEY`
- `SLACK_BOT_TOKEN`
- `SLACK_APP_TOKEN`
- `DISCORD_BOT_TOKEN`

### Deployment secrets

- `DEPLOY_HOST`
- `DEPLOY_TOKEN`
- `DEPLOY_USER`
- `STAGING_URL`
- `PRODUCTION_URL`

## Initial CD rollout

The safest MVP rollout is:

1. Merge to `main`
2. CI passes
3. Docker image is pushed to GHCR
4. Staging deploy runs
5. Production deploy stays manual

That gives you automation without forcing a brittle production pipeline too early.
