# Archived workflows

GitHub Actions only runs files in `.github/workflows/`. These earlier pipelines are kept for reference and **do not run**.

They were replaced by [`../workflows/pipeline.yml`](../workflows/pipeline.yml) because they overlapped (several ran on every push), referenced services that were never set up (Replit, AWS, Snyk, SonarCloud), or reported success while failing (`|| echo`, `continue-on-error`).

Active workflows: `pipeline.yml` (CI/CD) and `codeql.yml` (static analysis). `dependency-review.yml` is archived because it needs the GitHub dependency graph, which is not enabled on this repository.
