VTK Viewer — How to Run

────────────────────────────────────────────
WHAT IT DOES
────────────────────────────────────────────
• File: scripts\vtk_viewer.py
• Purpose: View CT scans, segmentation masks, and registration results in a 3D viewer.
• Shows: Original CT, lung mask (green), infection mask (red), registered images side-by-side, and quantification reports.

────────────────────────────────────────────
REQUIREMENTS
────────────────────────────────────────────
Install VTK first:
pip install vtk

That's it. The script handles everything else.

────────────────────────────────────────────
HOW TO RUN
────────────────────────────────────────────
Option 1 – In VS Code
• Right-click vtk_viewer.py → "Run Python File in Terminal".

Option 2 – Command Line
• python scripts\vtk_viewer.py

Option 3 – Double-click
• If .py files are associated with Python, double-click to start.

A GUI window will pop up automatically.

────────────────────────────────────────────
USING THE VIEWER
────────────────────────────────────────────
1. Click "Load Original CT"
   • Pick a .nii.gz or .mha file, OR click Cancel to select a DICOM folder.

2. (Optional) Load masks:
   • "Load Lung Mask" → pick mask_lung.nii.gz
   • "Load Infection Mask" → pick mask_infection.nii.gz

3. (Optional) Load registered image:
   • "Load Registered Image" → pick moving_rigid.nii.gz

4. (Optional) Load quantification report:
   • "Load Quant Report" → pick report.json

5. Use the slider to scroll through slices.

6. Click "Toggle Mask Overlay" to show/hide masks on the CT.

7. Click "Toggle Registered View" to see fixed CT vs registered side-by-side.

8. Click "Show Viewer" to open the VTK window.

────────────────────────────────────────────
KEYBOARD CONTROLS (in VTK window)
────────────────────────────────────────────
• Arrow Up/Down: Navigate slices
• Mouse drag: Pan image
• Mouse wheel: Zoom
• 'r' key: Reset camera

────────────────────────────────────────────
WHAT FILES TO LOAD
────────────────────────────────────────────
Original CT:
• Output from seg_only.py: image_resampled.nii.gz
• OR any .nii.gz, .mha, .mhd file
• OR a DICOM folder (select folder when prompted)

Lung Mask:
• Output from seg_only.py: mask_lung.nii.gz

Infection Mask:
• Output from seg_only.py: mask_infection.nii.gz

Registered Image:
• Output from register_pair.py: moving_rigid.nii.gz

Quantification Report:
• Output from quant_only.py: report.json

────────────────────────────────────────────
TROUBLESHOOTING
────────────────────────────────────────────
"VTK is not installed"
• Run: pip install vtk

"tkinter not available"
• On Linux: sudo apt-get install python3-tk
• On Windows/Mac: Usually comes with Python

Images not showing
• Make sure files are loaded successfully
• Check that file paths are correct
• Verify image formats (.nii.gz, .mha, .mhd, DICOM)

Nothing happens when clicking buttons
• Make sure you loaded the CT image first
• Check for error messages in the terminal

────────────────────────────────────────────
END OF README
────────────────────────────────────────────

