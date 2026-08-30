# Scriptorium

Consent-based handwriting style synthesis and generated-output traceability research prototype.

Scriptorium explores a structured V1 workflow for turning consented handwriting samples into a reusable glyph library and rendering new handwritten-style text with visible labeling and JSON generation records.

## Purpose

The goal of this project is to learn and demonstrate practical engineering across:

- computer vision
- image preprocessing
- structured data extraction
- glyph-based rendering
- generated-output traceability
- backend API scaffolding
- testing and project organization

The project is intentionally scoped as a research and learning prototype, not a production handwriting synthesis product.

## Ethical framing

Scriptorium is designed around consented handwriting samples and traceable generated outputs.

Legitimate use cases include:

- accessibility-oriented writing tools
- creative typography
- personal journaling
- preserving the handwriting style of consenting users
- research into handwriting synthesis
- research into generated-media traceability

This project is not intended for:

- academic dishonesty
- forgery
- impersonation
- fraud
- signature generation
- bypassing school, workplace, or institutional policies
- generating handwriting from non-consenting people
- removing generated-output labels or traceability records

## Current V1 workflow

The current V1 uses a structured lowercase-only handwriting template.

The local pipeline is:

    template image
    -> preprocessing
    -> grid-based glyph extraction
    -> glyph manifest
    -> contact sheet
    -> glyph-based text rendering
    -> visible generated-output footer
    -> JSON generation record

## What V1 currently supports

- generating a blank handwriting capture template
- preprocessing template images into binary images
- extracting glyph crops from known grid cells
- saving glyph manifests
- creating glyph contact sheets for visual inspection
- rendering lowercase text from extracted glyph variants
- adding a visible generated-output footer
- writing JSON generation records
- running a local V1 pipeline
- running a minimal FastAPI service scaffold
- running smoke tests

## What V1 does not support yet

- robust phone-photo perspective correction
- arbitrary handwriting page segmentation
- cursive or connected-word segmentation
- uppercase letters, digits, or punctuation in the active V1 template
- high-quality style modeling
- ML-based generation
- browser-based sample approval
- production authentication or storage
- real privacy/security guarantees
- removing generated-output traceability

## Local setup

Create and activate a virtual environment.

On Git Bash:

    python -m venv .venv
    source .venv/Scripts/activate

On PowerShell:

    python -m venv .venv
    .venv\Scripts\Activate.ps1

Install the project in editable mode with development dependencies:

    python -m pip install -e ".[dev]"

## Generate the blank template

    python experiments/scripts/create_template.py

This creates:

    templates/template_v1.png

## Preprocess an image

    python experiments/scripts/preprocess_image.py --input templates/template_v1.png --output data/processed/template_v1_binary.png

This creates a binary preprocessed image under:

    data/processed/

## Extract glyphs

    python experiments/scripts/extract_glyphs.py --input templates/template_v1.png --user-id user_001

This creates glyph crops and a manifest under:

    data/glyphs/user_001/

## Create a glyph contact sheet

    python experiments/scripts/create_contact_sheet.py --manifest data/glyphs/user_001/glyph_manifest.json

This creates:

    data/glyphs/user_001/glyph_contact_sheet.png

## Render text

    python experiments/scripts/render_text.py --manifest data/glyphs/user_001/glyph_manifest.json --text "hello world"

This creates:

    data/outputs/rendered_text.png

and a JSON generation record under:

    data/manifests/

## Run the full V1 pipeline

    python experiments/scripts/run_pipeline.py --input templates/template_v1.png --text "hello world" --user-id user_001

This runs:

- preprocessing
- glyph extraction
- contact sheet generation
- text rendering
- visible generated-output labeling
- JSON generation record creation

Expected outputs are saved under:

    data/processed/
    data/glyphs/
    data/outputs/
    data/manifests/

## Run the FastAPI service scaffold

    uvicorn services.api.main:app --reload

Then open:

    http://127.0.0.1:8000/
    http://127.0.0.1:8000/health
    http://127.0.0.1:8000/project
    http://127.0.0.1:8000/docs

The API currently exposes only basic scaffold routes. It does not yet expose upload or generation endpoints.

## Run tests

    pytest -p no:cacheprovider

The `-p no:cacheprovider` flag avoids local pytest cache issues on some Windows/OneDrive setups.

## Data and generated files

Local generated files are intentionally ignored by Git.

Ignored folders include:

    data/raw/
    data/processed/
    data/glyphs/
    data/outputs/
    data/manifests/
    experiments/results/
    .tmp_tests/

Do not commit personal handwriting samples or generated outputs unless they are deliberately sanitized demo assets.

## Current limitations

The current V1 assumes the input image matches the generated template layout closely.

It does not yet perform robust page detection, perspective correction, or phone-photo alignment. For best results, use the generated template image directly or a clean scan that preserves the same layout.

The current active template is lowercase-only so the V1 fits on one page and remains easy to debug.

The renderer is glyph-based and procedural. It does not yet learn a deep style representation or generate new strokes with a neural model.

## Next planned improvements

Planned next steps include:

- adding fiducial markers for template alignment
- improving glyph cleanup
- adding renderer variation controls
- adding a visual evaluation report command
- adding API endpoints for upload and generation
- adding a frontend for sample upload and output preview
- expanding the template to uppercase letters, digits, and punctuation
- exploring lightweight ML-based style evaluation
