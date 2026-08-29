Scriptorium is a research and learning prototype for consent-based handwriting style synthesis.
The project is designed for legitimate uses such as:
-  accessibility tools for people who may benefit from assisted writing workflows 
-  creative typography and font-like personal style exploration 
-  personalized journaling or letter-writing 
-  preserving the handwriting style of consenting users 
-  research into handwriting synthesis and style transfer 
-  research into watermarking, provenance, and generated-media traceability 
Scriptorium must not be used for:
-  academic dishonesty 
-  forgery 
-  impersonation 
-  fraud 
-  signature generation 
-  bypassing school, workplace, or institutional policies 
-  generating handwriting from a person who did not consent 
-  removing, hiding, or weakening provenance from generated outputs 
All handwriting samples used by the system must come from the user or from a person who has explicitly consented.
Future versions should store a consent record for each sample batch. A consent record should include:
-  sample batch ID 
-  timestamp 
-  declared sample owner 
-  consent confirmation 
-  policy version 
Generated outputs should include provenance by default.
Planned V1 provenance mechanisms include:
-  visible generated-output label 
-  JSON sidecar manifest 
-  image metadata where supported 
-  renderer version and template version references 
The project should avoid language such as:
-  perfect imitation 
-  forgery 
-  undetectable 
-  bypass 
-  cheat 
-  fake homework 
-  signature generation 
The project should prefer language such as:
-  consent-based 
-  handwriting-style rendering 
-  provenance-aware 
-  generated-media traceability 
-  personal style preservation 
-  research prototype 
Ethics should be part of the system architecture, not only a disclaimer in the README.
For this project, that means:
-  consent should be represented in data models 
-  provenance should be added during export 
-  generated outputs should be labeled by default 
-  non-consented use should be outside the supported workflow 
-  safety constraints should be discussed in technical documentation 
