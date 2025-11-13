"""
covid_ct package
----------------
Utilities for loading, preprocessing, segmenting, registering,
and quantifying Covid-19 chest CT scans using SimpleITK.

Modules:
    io/               - DICOM reading and series selection
    preprocess/       - HU clipping, normalization, and resampling
    segmentation/     - Region growing, Level-set, and seed helpers
    registration/     - Rigid and deformable registration
    quantification/   - Dice metric, infection volume calculation
    viz/              - Quick 2D overlay visualization

Example:
    from covid_ct.io.dicom import read_dicom_series
    from covid_ct.segmentation.region_growing import lung_mask_region_growing
"""

__version__ = "0.1.0"
__author__ = "Team SKY (CSC621-821 Fall 2025)"
