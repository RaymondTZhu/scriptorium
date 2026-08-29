# Scriptorium

Consent-based handwriting style synthesis and provenance research prototype.

Scriptorium is an early-stage research and engineering project for exploring structured handwriting sample capture, glyph extraction, handwritten-style rendering, and provenance-aware generated media.

## Purpose

The goal of this project is to explore whether consented handwriting samples can be converted into a structured glyph library and used to render new handwritten-style text with transparent provenance.

This project is intended for legitimate uses such as:

- accessibility tools
- creative typography
- personalized journaling or letter-writing
- preserving the handwriting style of consenting users
- research into handwriting synthesis
- research into watermarking and generated-media provenance

## Non-goals

This project is not intended for:

- academic dishonesty
- forgery
- impersonation
- fraud
- signature generation
- bypassing school, workplace, or institutional policies
- generating handwriting from non-consenting people
- producing outputs that hide or remove generated-media provenance

## V1 direction

The first version is intentionally scoped around a structured handwriting template and a classical computer vision pipeline.

The planned V1 flow is:
```text
blank handwriting template
→ completed consented sample
→ image preprocessing
→ grid-based glyph extraction
→ glyph library
→ procedural handwritten-style rendering
→ visible and metadata-based provenance
→ evaluation reports
```
