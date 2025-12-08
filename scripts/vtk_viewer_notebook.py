# scripts/vtk_viewer_notebook.py
"""
Jupyter notebook version of VTK viewer using ipywidgets and VTK.
This creates interactive widgets that work in Jupyter notebooks.
"""
import sys
import os
from pathlib import Path
import numpy as np
import SimpleITK as sitk
import vtk
from vtk.util.numpy_support import numpy_to_vtk

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from covid_ct.io.image_loader import load_image, extract_axial_slice
from covid_ct.visualization.viewer_utils import create_checkerboard, create_difference_map, normalize_for_display

try:
    import ipywidgets as widgets
    from IPython.display import display, clear_output
    from ipywidgets import interact, interactive, fixed, HBox, VBox, Output
    IPYWIDGETS_AVAILABLE = True
except ImportError:
    IPYWIDGETS_AVAILABLE = False
    print("Warning: ipywidgets not available. Install with: pip install ipywidgets")


def numpy_to_vtk_image(arr: np.ndarray):
    """Convert numpy array to VTK image."""
    if len(arr.shape) == 2:
        if arr.dtype != np.uint8:
            arr = normalize_for_display(arr)
        arr = np.flipud(arr)
        vtk_data = numpy_to_vtk(arr.ravel(), array_type=vtk.VTK_UNSIGNED_CHAR)
        vtk_data.SetNumberOfComponents(1)
        vtk_image = vtk.vtkImageData()
        vtk_image.SetDimensions(arr.shape[1], arr.shape[0], 1)
    else:
        arr = np.flipud(arr)
        vtk_data = numpy_to_vtk(arr.ravel(), array_type=vtk.VTK_UNSIGNED_CHAR)
        vtk_data.SetNumberOfComponents(3)
        vtk_image = vtk.vtkImageData()
        vtk_image.SetDimensions(arr.shape[1], arr.shape[0], 1)
    
    vtk_image.SetSpacing(1.0, 1.0, 1.0)
    vtk_image.GetPointData().SetScalars(vtk_data)
    return vtk_image


def create_slice_viewer(image_path: str, mask_path: str = None):
    """
    Create an interactive slice viewer widget for Jupyter notebook.
    
    Usage:
        viewer = create_slice_viewer("path/to/image.nii.gz", "path/to/mask.nii.gz")
        display(viewer)
    """
    if not IPYWIDGETS_AVAILABLE:
        print("ipywidgets not available. Install with: pip install ipywidgets")
        return None
    
    # Load images
    try:
        image = load_image(image_path)
        mask = load_image(mask_path) if mask_path else None
    except Exception as e:
        print(f"Error loading images: {e}")
        return None
    
    num_slices = image.GetSize()[2]
    
    # Create widgets
    slice_slider = widgets.IntSlider(
        value=num_slices // 2,
        min=0,
        max=num_slices - 1,
        step=1,
        description='Slice:',
        style={'description_width': 'initial'},
        layout=widgets.Layout(width='500px')
    )
    
    show_mask_check = widgets.Checkbox(
        value=True,
        description='Show Mask Overlay',
        disabled=False
    )
    
    output = Output()
    
    def update_view(slice_idx, show_mask):
        with output:
            clear_output(wait=True)
            
            # Extract slice
            slice_arr = extract_axial_slice(image, slice_idx)
            
            # Apply mask overlay if requested
            if mask is not None and show_mask:
                try:
                    mask_slice = extract_axial_slice(mask, slice_idx)
                    # Create overlay (simple approach - use matplotlib for display)
                    import matplotlib.pyplot as plt
                    fig, ax = plt.subplots(figsize=(8, 8))
                    ax.imshow(slice_arr, cmap='gray')
                    mask_overlay = np.ma.masked_where(mask_slice == 0, mask_slice)
                    ax.imshow(mask_overlay, cmap='Reds', alpha=0.3, interpolation='nearest')
                    ax.set_title(f'Axial Slice {slice_idx}/{num_slices-1}')
                    ax.axis('off')
                    plt.tight_layout()
                    plt.show()
                except Exception as e:
                    print(f"Error displaying with mask: {e}")
                    import matplotlib.pyplot as plt
                    plt.figure(figsize=(8, 8))
                    plt.imshow(slice_arr, cmap='gray')
                    plt.title(f'Axial Slice {slice_idx}/{num_slices-1}')
                    plt.axis('off')
                    plt.show()
            else:
                import matplotlib.pyplot as plt
                plt.figure(figsize=(8, 8))
                plt.imshow(slice_arr, cmap='gray')
                plt.title(f'Axial Slice {slice_idx}/{num_slices-1}')
                plt.axis('off')
                plt.show()
    
    # Create interactive widget
    interactive_widget = interactive(update_view, 
                                    slice_idx=slice_slider, 
                                    show_mask=show_mask_check)
    
    return VBox([interactive_widget, output])


def create_comparison_viewer(image1_path: str, image2_path: str):
    """
    Create an interactive comparison viewer widget for Jupyter notebook.
    
    Usage:
        viewer = create_comparison_viewer("path/to/original.nii.gz", "path/to/registered.nii.gz")
        display(viewer)
    """
    if not IPYWIDGETS_AVAILABLE:
        print("ipywidgets not available. Install with: pip install ipywidgets")
        return None
    
    # Load images
    try:
        image1 = load_image(image1_path)
        image2 = load_image(image2_path)
    except Exception as e:
        print(f"Error loading images: {e}")
        return None
    
    num_slices = image1.GetSize()[2]
    
    # Create widgets
    slice_slider = widgets.IntSlider(
        value=num_slices // 2,
        min=0,
        max=num_slices - 1,
        step=1,
        description='Slice:',
        style={'description_width': 'initial'},
        layout=widgets.Layout(width='500px')
    )
    
    mode_radio = widgets.RadioButtons(
        options=['checkerboard', 'difference', 'side_by_side'],
        value='checkerboard',
        description='Mode:',
        disabled=False
    )
    
    output = Output()
    
    def update_comparison(slice_idx, mode):
        with output:
            clear_output(wait=True)
            
            # Extract slices
            slice1 = extract_axial_slice(image1, slice_idx)
            slice2 = extract_axial_slice(image2, slice_idx)
            
            # Normalize both to same range
            vmin = min(slice1.min(), slice2.min())
            vmax = max(slice1.max(), slice2.max())
            slice1_norm = normalize_for_display(slice1, vmin, vmax)
            slice2_norm = normalize_for_display(slice2, vmin, vmax)
            
            # Create comparison
            if mode == 'checkerboard':
                result = create_checkerboard(slice1_norm, slice2_norm)
                title = f'Checkerboard Comparison - Slice {slice_idx}/{num_slices-1}'
            elif mode == 'difference':
                diff = create_difference_map(slice1_norm.astype(np.float32), 
                                            slice2_norm.astype(np.float32), 
                                            method='absolute')
                result = normalize_for_display(diff)
                title = f'Difference Map - Slice {slice_idx}/{num_slices-1}'
            else:  # side_by_side
                result = np.concatenate([slice1_norm, slice2_norm], axis=1)
                title = f'Side-by-Side - Slice {slice_idx}/{num_slices-1}'
            
            # Display
            import matplotlib.pyplot as plt
            plt.figure(figsize=(12, 6))
            plt.imshow(result, cmap='gray')
            plt.title(title)
            plt.axis('off')
            plt.tight_layout()
            plt.show()
    
    # Create interactive widget
    interactive_widget = interactive(update_comparison, 
                                    slice_idx=slice_slider, 
                                    mode=mode_radio)
    
    return VBox([interactive_widget, output])


# Example usage for notebook
if __name__ == "__main__":
    print("This module is designed for use in Jupyter notebooks.")
    print("\nExample usage:")
    print("  from scripts.vtk_viewer_notebook import create_slice_viewer, create_comparison_viewer")
    print("  ")
    print("  # Slice viewer with mask overlay")
    print("  viewer = create_slice_viewer('image.nii.gz', 'mask.nii.gz')")
    print("  display(viewer)")
    print("  ")
    print("  # Comparison viewer")
    print("  comp_viewer = create_comparison_viewer('original.nii.gz', 'registered.nii.gz')")
    print("  display(comp_viewer)")

