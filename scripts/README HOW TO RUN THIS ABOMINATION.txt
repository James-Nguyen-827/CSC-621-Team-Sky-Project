COVID-CT Toolkit — Script Guide

Each Python file runs on its own and opens folder pickers (no command-line use needed).

────────────────────────────────────────────
SEGMENTATION
────────────────────────────────────────────
• File: scripts\seg_only.py
• Purpose: Segments a single CT study — lungs and infection.
• Inputs: DICOM folder (selected via picker).
• Outputs:

image_resampled.nii.gz

mask_lung.nii.gz

mask_infection.nii.gz

qc_overlay.png

────────────────────────────────────────────
REGISTRATION
────────────────────────────────────────────
• File: scripts\register_pair.py
• Purpose: Registers a moving CT scan to a fixed one using rigid mutual-information and optional B-spline.
• Inputs: Two DICOM folders (fixed + moving).
• Outputs:

moving_rigid.nii.gz

optional moving_bspline.nii.gz

rigid.tfm / bspline.tfm transform files

────────────────────────────────────────────
QUANTIFICATION
────────────────────────────────────────────
• File: scripts\quant_only.py
• Purpose: Calculates infection metrics from existing segmentation masks.
• Inputs: Processed case folder containing image_resampled.nii.gz and mask files.
• Outputs: report.json
(includes percent_infected, lesion_count, total_volume_ml)

────────────────────────────────────────────
BATCH PROCESSING
────────────────────────────────────────────
• File: scripts\batch_gui.py
• Purpose: Runs segmentation and quantification for all studies in a dataset tree.
• Inputs: Root dataset folder + output location.
• Outputs: Per-case results under data\processed and a batch_log.csv summary.

────────────────────────────────────────────
VIEWER / COMPARATOR
────────────────────────────────────────────
• File: scripts\comparator.py
• Purpose: Shows raw DICOM vs processed CT side-by-side (Axial, Coronal, Sagittal).
• Inputs: DICOM folder + processed .nii.gz file.
• Outputs: On-screen viewer or saved PNG comparison.

────────────────────────────────────────────
LAUNCHER
────────────────────────────────────────────
• File: scripts\launcher.py
• Purpose: Simple GUI launcher to choose which operation to run:
Segmentation, Registration, Quantification, Batch, or Viewer.
• Inputs: None (menu only).
• Outputs: Depends on selected operation.

────────────────────────────────────────────
HOW TO RUN
────────────────────────────────────────────
Option 1 – In VS Code
• Right-click the file → “Run Python File in Terminal”.

Option 2 – Double-click
• If .py files are associated with Python, double-click to start.

All scripts open pickers automatically for folders/files.

────────────────────────────────────────────
DEFAULT OUTPUT LOCATIONS
────────────────────────────────────────────
data\processed<study_name>\
• Segmentation outputs (.nii.gz, .png)
• Registration outputs (.nii.gz, .tfm)
• Quantification report.json
• Batch results + batch_log.csv

────────────────────────────────────────────
END OF README
────────────────────────────────────────────