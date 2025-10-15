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

- **Jamie** — GitHub management and connecting different program components.
- **Carter Yang** — Front-end visualization (showing segmented and registered results).
- **Sani Hasan** — Base programming for segmentation/registration.
- **Daniel Lee** — Base programming for segmentation/registration and testing.
