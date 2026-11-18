# Legacy scripts

One-off deployment, debugging and setup scripts from earlier development. They are **not maintained** and are kept for reference.

- Run them from the **repository root**, e.g. `bash scripts/legacy/railway-status.sh`. Internal paths were updated for this location.
- Several target the earlier single-service Railway setup; the current deployment process is in [docs/deployment.md](../../docs/deployment.md).
- Scripts that need secrets read them from environment variables and stop with a message if one is missing.
