# Scriptorium

Scriptorium is a research prototype for consent-based handwriting style synthesis and
provenance. The repository is currently an initial scaffold: it defines the package
boundaries, API service layout, experiment workspace, and data lifecycle that future
implementation will build on.

## Repository layout

```text
apps/web/              Web client
data/                  Local inputs, derived artifacts, and manifests
docs/                  Project documentation
experiments/           Notebooks, scripts, and generated results
packages/common/       Shared types and utilities
packages/cv/           Computer-vision processing
packages/eval/         Evaluation tools
packages/renderer/     Handwriting renderer
packages/watermark/    Provenance and watermarking
services/api/          FastAPI service
templates/             Reusable project templates
tests/                 Automated tests
```

Generated data under `data/` and `experiments/results/` is intentionally ignored. Keep
source material out of Git unless it is explicitly safe and appropriate to publish.

## Development setup

Scriptorium requires Python 3.11 or newer.

```bash
python -m venv .venv
```

Activate the environment, then install the project and development tools:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Run the baseline checks with:

```bash
ruff check .
mypy packages services
pytest
```

The scaffold does not yet expose an application entry point; those commands validate the
package structure as implementation is added.

## Responsible use

Only use handwriting samples with the writer's informed consent. Preserve provenance,
avoid impersonation, and treat source samples and generated artifacts as sensitive data.
