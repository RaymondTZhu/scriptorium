Scriptorium V1 is planned as a modular pipeline:
```
blank handwriting template
→ completed consented sample
→ image preprocessing
→ template alignment
→ grid-based segmentation
→ glyph extraction
→ glyph library construction
→ procedural text rendering
→ watermark/provenance export
→ evaluation report
```
Shared project utilities.
Expected responsibilities:
-  project paths 
-  configuration objects 
-  shared data types 
-  reusable constants 
Computer vision pipeline.
Expected responsibilities:
-  image loading 
-  grayscale conversion 
-  thresholding 
-  template alignment 
-  grid-based segmentation 
-  glyph cleanup 
-  glyph quality checks 
Handwritten-style rendering pipeline.
Expected responsibilities:
-  glyph library loading 
-  text layout 
-  glyph variant sampling 
-  baseline variation 
-  spacing variation 
-  PNG rendering 
Provenance and watermarking.
Expected responsibilities:
-  visible generated-output labels 
-  sidecar metadata manifests 
-  future image metadata embedding 
-  future invisible watermark experiments 
Evaluation and visual reporting.
Expected responsibilities:
-  contact sheets 
-  extraction metrics 
-  rendering comparison reports 
-  provenance durability checks 
Future FastAPI backend.
Expected responsibilities:
-  health checks 
-  sample upload endpoints 
-  preprocessing endpoints 
-  generation endpoints 
-  manifest retrieval endpoints 
Future frontend application.
Expected responsibilities:
-  upload interface 
-  glyph approval interface 
-  text generation interface 
-  output preview 
-  manifest download 
The first version should use a structured handwriting template instead of arbitrary handwriting pages.
Reason:
Arbitrary handwriting segmentation is difficult. Cursive, touching letters, variable baselines, inconsistent spacing, shadows, skew, and page perspective can quickly turn the project into a segmentation research problem.
A structured template keeps V1 realistic while still requiring meaningful engineering:
-  image preprocessing 
-  grid geometry 
-  glyph extraction 
-  rendering 
-  provenance 
-  evaluation 
Using a template makes the system less flexible but more reliable.
That is a good V1 tradeoff because the goal is to build a full, understandable, end-to-end system before attempting harder open-world handwriting segmentation.
