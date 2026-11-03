# Dockerized application starter

A small HTTP service with `/health` demonstrates non-root container execution and the reusable Docker CI workflow. Replace `your-org` in `.github/workflows/ci.yml` with the toolkit repository owner and select a published release tag. The workflow checks the Dockerfile, builds it, and fails on unfixed HIGH or CRITICAL image vulnerabilities.

The example uses an explicit Python base-image tag. For production images, prefer a reviewed base image pinned by digest and update it through a scheduled review process. Docker CI requires a Linux runner with Docker available.
