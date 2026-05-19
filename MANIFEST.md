# Repository Manifest

Project name: Aurora Markets Research Terminal

This repository contains a desktop AI equity research terminal for new-energy stocks, with a FastAPI backend, Vue/Vite frontend, local demo fixtures, report export helpers, and CI checks.

## Included

- `app.py` desktop launcher
- `apps/api/` FastAPI backend, schemas, services, and tests
- `apps/web/` Vue 3 frontend source and package lockfile
- `scripts/create_submission_package.py` reproducible submission bundle script
- `README.md`, `SUBMISSION_GUIDE.md`, `AGENTS.md`, and sanitized user guide document
- `.github/workflows/ci.yml` backend and frontend validation workflow

## Excluded

The repository intentionally excludes local runtime and privacy-sensitive files:

- `.runtime/`
- `apps/runtime_assets/`
- `node_modules/`
- `dist/`
- `.venv/`
- `__pycache__/`
- `.pytest_cache/`
- `.env*`
- `reports/`
- `submission/`
- local logs, browser/WebEngine cache, smoke screenshots, and generated temporary images
