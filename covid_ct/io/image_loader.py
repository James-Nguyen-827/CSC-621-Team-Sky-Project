# covid_ct/io/image_loader.py
"""
Enhanced image loader for frontend viewer.
Supports multiple formats: .nii.gz, .mha, .dcm (DICOM folder)
"""
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import numpy as np
import SimpleITK as sitk
from .dicom import read_dicom_series

def load_image(file_path: str) -> sitk.Image:
    """
    Load a medical image from file or DICOM folder.
    
    Supports:
    - .nii, .nii.gz (NIfTI)
    - .mha, .mhd (MetaImage)
    - .dcm folder (DICOM series - auto-selects best CT)
    
    Args:
        file_path: Path to image file or DICOM folder
        
    Returns:
        SimpleITK Image object
    """
    path = Path(file_path)
    
    # Check if it's a DICOM folder
    if path.is_dir():
        return read_dicom_series(str(path))
    
    # Check file extension
    ext = path.suffix.lower()
    if ext == '.gz':
        # Handle .nii.gz
        ext = ''.join(path.suffixes[-2:]).lower()
    
    # Load based on format
    if ext in ['.nii', '.nii.gz']:
        return sitk.ReadImage(str(path))
    elif ext in ['.mha', '.mhd']:
        return sitk.ReadImage(str(path))
    elif ext == '.dcm':
        # Single DICOM file
        return sitk.ReadImage(str(path))
    else:
        # Try SimpleITK's auto-detection
        return sitk.ReadImage(str(path))


def get_image_metadata(img: sitk.Image) -> Dict[str, Any]:
    """
    Extract metadata from SimpleITK image for frontend.
    
    Returns:
        Dictionary with size, spacing, origin, direction, etc.
    """
    size = img.GetSize()
    spacing = img.GetSpacing()
    origin = img.GetOrigin()
    direction = img.GetDirection()
    
    return {
        "size": list(size),  # [x, y, z]
        "spacing": list(spacing),  # [x, y, z] in mm
        "origin": list(origin),
        "direction": list(direction),
        "num_slices_axial": size[2],
        "num_slices_coronal": size[1],
        "num_slices_sagittal": size[0],
    }


def extract_axial_slice(img: sitk.Image, slice_idx: int) -> np.ndarray:
    """
    Extract a single axial slice (Z-axis) as numpy array.
    Uses ExtractSlice to avoid loading entire volume into memory.
    
    Args:
        img: SimpleITK Image
        slice_idx: Slice index (0 to num_slices-1)
        
    Returns:
        2D numpy array [y, x]
    """
    size = img.GetSize()
    num_slices = size[2]
    slice_idx = int(np.clip(slice_idx, 0, num_slices - 1))
    
    # Extract only the slice we need (more memory efficient)
    extractor = sitk.ExtractImageFilter()
    extractor.SetSize([size[0], size[1], 0])  # Extract full x,y, but only 1 slice in z
    extractor.SetIndex([0, 0, slice_idx])
    slice_img = extractor.Execute(img)
    
    # Convert only this 2D slice to numpy
    return sitk.GetArrayFromImage(slice_img)


def extract_slice(img: sitk.Image, plane: str, slice_idx: int) -> np.ndarray:
    """
    Extract a slice in specified plane.
    Uses ExtractImageFilter to avoid loading entire volume into memory.
    
    Args:
        img: SimpleITK Image
        plane: 'axial', 'coronal', or 'sagittal'
        slice_idx: Slice index
        
    Returns:
        2D numpy array
    """
    size = img.GetSize()
    extractor = sitk.ExtractImageFilter()
    
    if plane == "axial":
        num_slices = size[2]
        slice_idx = int(np.clip(slice_idx, 0, num_slices - 1))
        extractor.SetSize([size[0], size[1], 0])
        extractor.SetIndex([0, 0, slice_idx])
    elif plane == "coronal":
        num_slices = size[1]
        slice_idx = int(np.clip(slice_idx, 0, num_slices - 1))
        extractor.SetSize([size[0], 0, size[2]])
        extractor.SetIndex([0, slice_idx, 0])
    elif plane == "sagittal":
        num_slices = size[0]
        slice_idx = int(np.clip(slice_idx, 0, num_slices - 1))
        extractor.SetSize([0, size[1], size[2]])
        extractor.SetIndex([slice_idx, 0, 0])
    else:
        raise ValueError(f"Unknown plane: {plane}. Must be 'axial', 'coronal', or 'sagittal'")
    
    slice_img = extractor.Execute(img)
    return sitk.GetArrayFromImage(slice_img)


def apply_mask_overlay(image_slice: np.ndarray, mask_slice: np.ndarray, 
                       alpha: float = 0.3, color: Tuple[int, int, int] = (255, 0, 0)) -> np.ndarray:
    """
    Apply segmentation mask overlay on image slice.
    
    Args:
        image_slice: 2D grayscale image array
        mask_slice: 2D binary mask array (0 or 1)
        alpha: Overlay transparency (0.0 to 1.0)
        color: RGB color for mask overlay (default: red)
        
    Returns:
        3D RGB array [y, x, 3] with overlay applied
    """
    # Normalize image to 0-255
    img_norm = ((image_slice - image_slice.min()) / 
                (image_slice.max() - image_slice.min() + 1e-8) * 255).astype(np.uint8)
    
    # Create RGB image
    rgb = np.stack([img_norm, img_norm, img_norm], axis=-1)
    
    # Apply mask overlay
    mask_bool = mask_slice > 0
    for c in range(3):
        rgb[:, :, c] = np.where(mask_bool, 
                                (1 - alpha) * rgb[:, :, c] + alpha * color[c],
                                rgb[:, :, c])
    
    return rgb.astype(np.uint8)

