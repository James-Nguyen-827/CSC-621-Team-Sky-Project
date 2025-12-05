# covid_ct/visualization/viewer_utils.py
"""
Utility functions for frontend viewer: checkerboard, difference maps, etc.
"""
import numpy as np
from typing import Tuple, Optional

def create_checkerboard(img1: np.ndarray, img2: np.ndarray, 
                       tile_size: int = 32) -> np.ndarray:
    """
    Create a checkerboard pattern alternating between two images.
    
    Args:
        img1: First image (2D array)
        img2: Second image (2D array) - must match img1 shape
        tile_size: Size of each checkerboard tile in pixels
        
    Returns:
        Checkerboard image (2D array)
    """
    if img1.shape != img2.shape:
        raise ValueError(f"Images must have same shape. Got {img1.shape} and {img2.shape}")
    
    h, w = img1.shape
    result = np.zeros_like(img1)
    
    for i in range(0, h, tile_size):
        for j in range(0, w, tile_size):
            # Determine if this tile should use img1 or img2
            tile_i = i // tile_size
            tile_j = j // tile_size
            use_img1 = (tile_i + tile_j) % 2 == 0
            
            # Extract tile bounds
            i_end = min(i + tile_size, h)
            j_end = min(j + tile_size, w)
            
            if use_img1:
                result[i:i_end, j:j_end] = img1[i:i_end, j:j_end]
            else:
                result[i:i_end, j:j_end] = img2[i:i_end, j:j_end]
    
    return result


def create_difference_map(img1: np.ndarray, img2: np.ndarray, 
                         method: str = "absolute") -> np.ndarray:
    """
    Create a difference map between two images.
    
    Args:
        img1: First image (2D array)
        img2: Second image (2D array) - must match img1 shape
        method: 'absolute' (|img1 - img2|) or 'signed' (img1 - img2)
        
    Returns:
        Difference map (2D array)
    """
    if img1.shape != img2.shape:
        raise ValueError(f"Images must have same shape. Got {img1.shape} and {img2.shape}")
    
    if method == "absolute":
        diff = np.abs(img1.astype(np.float32) - img2.astype(np.float32))
    elif method == "signed":
        diff = img1.astype(np.float32) - img2.astype(np.float32)
    else:
        raise ValueError(f"Unknown method: {method}. Use 'absolute' or 'signed'")
    
    return diff


def normalize_for_display(arr: np.ndarray, vmin: Optional[float] = None, 
                          vmax: Optional[float] = None) -> np.ndarray:
    """
    Normalize array to 0-255 uint8 for display.
    
    Args:
        arr: Input array
        vmin: Minimum value for normalization (default: arr.min())
        vmax: Maximum value for normalization (default: arr.max())
        
    Returns:
        Normalized uint8 array
    """
    if vmin is None:
        vmin = arr.min()
    if vmax is None:
        vmax = arr.max()
    
    if vmax == vmin:
        return np.zeros_like(arr, dtype=np.uint8)
    
    normalized = ((arr - vmin) / (vmax - vmin) * 255).clip(0, 255)
    return normalized.astype(np.uint8)


def blend_images(img1: np.ndarray, img2: np.ndarray, 
                alpha: float = 0.5) -> np.ndarray:
    """
    Blend two images with specified alpha.
    
    Args:
        img1: First image
        img2: Second image
        alpha: Blend factor (0.0 = all img1, 1.0 = all img2)
        
    Returns:
        Blended image
    """
    if img1.shape != img2.shape:
        raise ValueError(f"Images must have same shape. Got {img1.shape} and {img2.shape}")
    
    return (alpha * img1.astype(np.float32) + 
            (1 - alpha) * img2.astype(np.float32)).astype(img1.dtype)

