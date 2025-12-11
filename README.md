# COVID-19 CT Longitudinal Lung Analysis

*Segment • Register • Quantify changes in lung infection over time from 3D chest CT.*

## Overview

We analyze serial CT scans from a (simulated) COVID-19 patient to see how infection spreads, regresses, or stabilizes. The pipeline:

- **Segmentation** to isolate lungs and infection.
- **Registration** to align scans from different time points.
- **Quantification** to turn masks + aligned scans into metrics you can track.

## Methods

### Segmentation

- **3D Region Growing** to get a coarse lung mask.
- **3D Level Set** to refine infection boundaries for smooth, accurate masks.

### Registration

- **Intensity-Based Rigid (Mutual Information)** for global alignment.
- **B-Spline Deformable** to correct local motion (breathing/anatomical differences).

### Quantification

- **Infection volume %** (infected voxels / lung voxels).
- **Dice coefficient** vs. expert masks (if available).
- **Longitudinal change** in infection size/intensity across scans.

### Team Roles

- **James Nguyen** — Managed the GitHub repository, integrated program modules, and developed the quantification pipeline.
- **Carter Yang** — Developed the front-end visualization interface for segmented and registered CT outputs, and assisted in the image registration workflow.
- **Sani Hasan** — Implemented the core codebase for segmentation and registration, and developed the 3D reconstruction pipeline.
- **Daniel Lee** — Performed data preprocessing and conducted thorough debugging to ensure system stability and accuracy. 
