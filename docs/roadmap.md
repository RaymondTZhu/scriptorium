Goal:
Create a clean repository structure with Python packaging, isolated data folders, placeholder modules, and documentation.
Success criteria:
-  repository structure exists 
-  dependencies are declared 
-  editable install works 
-  generated and personal data are ignored by Git 
Goal:
Define project purpose, safety boundaries, architectural direction, and roadmap.
Success criteria:
-  README explains the project clearly 
-  ethics policy exists 
-  architecture document exists 
-  roadmap exists 
Goal:
Define the structured handwriting capture template.
Success criteria:
-  template JSON exists 
-  character set is defined 
-  variant count is defined 
-  template version is defined 
Goal:
Generate a blank handwriting template image from metadata.
Success criteria:
-  blank template image can be created 
-  template contains character labels 
-  template includes version/provenance text 
Goal:
Convert a completed handwriting template image into a clean processed image.
Success criteria:
-  input image can be loaded 
-  grayscale image can be produced 
-  binary thresholded image can be produced 
-  intermediate debug outputs can be saved 
Goal:
Extract handwritten glyphs from known template cells.
Success criteria:
-  each expected cell can be cropped 
-  empty or low-quality cells can be detected 
-  glyph images can be saved 
-  glyph manifest can be created 
Goal:
Make extracted glyphs inspectable and reusable.
Success criteria:
-  glyph library can be loaded 
-  glyph records are structured 
-  contact sheet can be generated 
-  extraction failures can be visually reviewed 
Goal:
Render typed text using extracted glyph images.
Success criteria:
-  user text can be converted to glyph sequence 
-  spaces and newlines are supported 
-  glyph variants can be sampled 
-  PNG output can be generated 
Goal:
Attach visible and metadata-based provenance to generated outputs.
Success criteria:
-  visible generated-output label is added 
-  JSON sidecar manifest is created 
-  renderer version is recorded 
-  template version is recorded 
Goal:
Create basic reports for extraction and rendering quality.
Success criteria:
-  contact sheet exists 
-  output preview exists 
-  visual report exists 
-  failure cases are easy to inspect 
Goal:
Expose the core workflow through a backend interface.
Success criteria:
-  FastAPI app runs 
-  health endpoint works 
-  future route structure is clear 
