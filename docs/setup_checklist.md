# Setup Checklist

## Local environment

- [ ] Git is installed
- [ ] Python 3.11 or newer is installed
- [ ] repository is cloned locally
- [ ] virtual environment is created
- [ ] virtual environment is activated
- [ ] dependencies are installed with `python -m pip install -e ".[dev]"`

## Project structure

- [ ] `packages/common` exists
- [ ] `packages/cv` exists
- [ ] `packages/renderer` exists
- [ ] `packages/watermark` exists
- [ ] `packages/eval` exists
- [ ] `services/api` exists
- [ ] `apps/web` exists
- [ ] `docs` exists
- [ ] `templates` exists
- [ ] `experiments` exists
- [ ] local data folders exist

## Core V1 commands

- [ ] blank template can be generated with `python experiments/scripts/create_template.py`
- [ ] image preprocessing can run with `python experiments/scripts/preprocess_image.py --input templates/template_v1.png`
- [ ] glyph extraction can run with `python experiments/scripts/extract_glyphs.py --input templates/template_v1.png --user-id user_001`
- [ ] contact sheet generation can run with `python experiments/scripts/create_contact_sheet.py --manifest data/glyphs/user_001/glyph_manifest.json`
- [ ] text rendering can run with `python experiments/scripts/render_text.py --manifest data/glyphs/user_001/glyph_manifest.json --text "hello world"`
- [ ] full V1 pipeline can run with `python experiments/scripts/run_pipeline.py --input templates/template_v1.png --text "hello world" --user-id user_001`

## API scaffold

- [ ] API can start with `uvicorn services.api.main:app --reload`
- [ ] root route works at `/`
- [ ] health route works at `/health`
- [ ] project route works at `/project`
- [ ] Swagger docs work at `/docs`

## Tests

- [ ] tests pass with `pytest -p no:cacheprovider`

## Git safety

- [ ] `.gitignore` ignores generated data
- [ ] `.gitignore` ignores local virtual environments
- [ ] `.gitignore` ignores environment files
- [ ] `.gitignore` ignores local test scratch space
- [ ] `.gitkeep` files preserve empty data folders
- [ ] no personal handwriting samples are committed
- [ ] no generated outputs are committed unless intentionally treated as static project assets

## Project safety

- [ ] README states legitimate project uses
- [ ] README states non-goals
- [ ] ethics policy exists
- [ ] generated outputs include visible labeling by default
- [ ] generation records are written by default
- [ ] non-consented handwriting use is outside the supported workflow
