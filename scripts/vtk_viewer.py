# scripts/vtk_viewer.py
"""
COVID-CT VTK Viewer - Complete implementation meeting all front-end requirements.
Uses VTK for visualization as recommended by the assignment.
Supports: CT loading, dual mask overlays, registered image comparison, and quantification report display.
"""
import sys
import os
import json
from pathlib import Path
import numpy as np
import SimpleITK as sitk
import vtk
from vtk.util.numpy_support import numpy_to_vtk

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from covid_ct.io.image_loader import load_image, extract_axial_slice
from covid_ct.visualization.viewer_utils import normalize_for_display

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    print("Warning: tkinter not available. File dialogs will not work.")


class COVIDCTVTKViewer:
    """Complete COVID-CT VTK viewer meeting all requirements."""
    
    def __init__(self):
        # State variables
        self.ct_volume = None  # SimpleITK Image
        self.mask_lung = None  # SimpleITK Image
        self.mask_infection = None  # SimpleITK Image
        self.registered_volume = None  # SimpleITK Image
        self.current_slice = 0
        self.overlay_on = False
        self.show_registered = False  # Toggle between original and registered
        self.report_data = None  # Quantification report dict
        
        # VTK setup - single window with viewports for side-by-side
        self.render_window = vtk.vtkRenderWindow()
        self.render_window.SetSize(1600, 600)  # Wider for side-by-side
        
        # Main renderer (left viewport for fixed CT)
        self.renderer = vtk.vtkRenderer()
        self.render_window.AddRenderer(self.renderer)
        
        # Second renderer (right viewport for registered - created when needed)
        self.renderer2 = None
        
        self.interactor = vtk.vtkRenderWindowInteractor()
        self.interactor.SetRenderWindow(self.render_window)
        self.interactor.SetInteractorStyle(vtk.vtkInteractorStyleImage())
        
        # Image actors for main view
        self.image_actor = vtk.vtkImageActor()
        self.renderer.AddActor(self.image_actor)
        
        # Separate actors for lung and infection masks
        self.lung_mask_actor = vtk.vtkImageActor()
        self.lung_mask_actor.SetOpacity(0.3)
        self.renderer.AddActor(self.lung_mask_actor)
        
        self.infection_mask_actor = vtk.vtkImageActor()
        self.infection_mask_actor.SetOpacity(0.3)
        self.renderer.AddActor(self.infection_mask_actor)
        
        # Actor for registered image (in second viewport)
        self.image_actor2 = None
        
        # Setup camera
        self.renderer.SetBackground(0.1, 0.1, 0.1)
        self.renderer.ResetCamera()
    
    def load_nifti(self, path: str):
        """Load NIfTI file and return as SimpleITK Image."""
        try:
            return load_image(path)
        except Exception as e:
            raise RuntimeError(f"Failed to load image: {e}")
    
    def load_report_json(self, path: str) -> dict:
        """Load and parse report.json."""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load report: {e}")
    
    def check_shape_match(self, img1, img2, name1="Image 1", name2="Image 2"):
        """Check if two images have matching dimensions."""
        if img1 is None or img2 is None:
            return True  # None is allowed
        size1 = img1.GetSize()
        size2 = img2.GetSize()
        if size1 != size2:
            raise ValueError(
                f"{name1} dimensions {size1} do not match {name2} dimensions {size2}. "
                f"Please use outputs from seg_only.py or ensure images are from the same case."
            )
        return True
    
    def numpy_to_vtk_image(self, arr: np.ndarray, is_rgb=False):
        """Convert numpy array to VTK image."""
        if len(arr.shape) != 2 and not is_rgb:
            raise ValueError("Array must be 2D for grayscale")
        
        # Normalize to 0-255 uint8
        if arr.dtype != np.uint8:
            arr = normalize_for_display(arr)
        
        # Flip Y axis (VTK uses different coordinate system)
        arr = np.flipud(arr)
        
        if is_rgb:
            # RGB overlay
            vtk_data = numpy_to_vtk(arr.ravel(), array_type=vtk.VTK_UNSIGNED_CHAR)
            vtk_data.SetNumberOfComponents(3)
            vtk_image = vtk.vtkImageData()
            vtk_image.SetDimensions(arr.shape[1], arr.shape[0], 1)
        else:
            # Grayscale
            vtk_data = numpy_to_vtk(arr.ravel(), array_type=vtk.VTK_UNSIGNED_CHAR)
            vtk_data.SetNumberOfComponents(1)
            vtk_image = vtk.vtkImageData()
            vtk_image.SetDimensions(arr.shape[1], arr.shape[0], 1)
        
        vtk_image.SetSpacing(1.0, 1.0, 1.0)
        vtk_image.GetPointData().SetScalars(vtk_data)
        return vtk_image
    
    def load_ct(self, file_path: str):
        """Load original CT image."""
        try:
            self.ct_volume = self.load_nifti(file_path)
            self.current_slice = self.ct_volume.GetSize()[2] // 2
            self.update_display()
            return True
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return False
    
    def load_mask_lung(self, file_path: str):
        """Load lung mask."""
        try:
            mask = self.load_nifti(file_path)
            if self.ct_volume is not None:
                self.check_shape_match(self.ct_volume, mask, "CT", "Lung mask")
            self.mask_lung = mask
            if self.overlay_on:
                self.update_display()
            return True
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return False
    
    def load_mask_infection(self, file_path: str):
        """Load infection mask."""
        try:
            mask = self.load_nifti(file_path)
            if self.ct_volume is not None:
                self.check_shape_match(self.ct_volume, mask, "CT", "Infection mask")
            self.mask_infection = mask
            if self.overlay_on:
                self.update_display()
            return True
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return False
    
    def load_registered(self, file_path: str):
        """Load registered image."""
        try:
            registered = self.load_nifti(file_path)
            if self.ct_volume is not None:
                ct_depth = self.ct_volume.GetSize()[2]
                reg_depth = registered.GetSize()[2]
                if ct_depth != reg_depth:
                    messagebox.showwarning(
                        "Warning", 
                        f"CT depth ({ct_depth}) doesn't match registered depth ({reg_depth}). "
                        f"Viewer will use minimum depth."
                    )
            self.registered_volume = registered
            if self.show_registered:
                self.update_display()
            return True
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return False
    
    def load_report(self, file_path: str):
        """Load quantification report."""
        try:
            self.report_data = self.load_report_json(file_path)
            return True
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return False
    
    def toggle_overlay(self):
        """Toggle mask overlay visibility."""
        if self.mask_lung is None and self.mask_infection is None:
            messagebox.showwarning(
                "No Masks Loaded",
                "Please load segmentation masks first (lung and/or infection)."
            )
            return
        
        self.overlay_on = not self.overlay_on
        self.update_display()
    
    def toggle_registered_view(self):
        """Toggle between original and registered view."""
        if self.registered_volume is None:
            messagebox.showwarning(
                "No Registered Image",
                "Please load a registered image first."
            )
            return
        
        self.show_registered = not self.show_registered
        self.setup_side_by_side()
        self.update_display()
    
    def setup_side_by_side(self):
        """Setup or remove side-by-side view using viewports in single window."""
        if self.show_registered and self.registered_volume is not None:
            # Create second renderer for right viewport
            if self.renderer2 is None:
                self.renderer2 = vtk.vtkRenderer()
                self.render_window.AddRenderer(self.renderer2)
                
                self.image_actor2 = vtk.vtkImageActor()
                self.renderer2.AddActor(self.image_actor2)
                
                self.renderer2.SetBackground(0.1, 0.1, 0.1)
                self.renderer2.ResetCamera()
            
            # Set viewports: left half for fixed CT, right half for registered
            self.renderer.SetViewport(0.0, 0.0, 0.5, 1.0)  # Left half
            self.renderer2.SetViewport(0.5, 0.0, 1.0, 1.0)  # Right half
            self.render_window.SetSize(1600, 600)  # Wider window
        else:
            # Single viewport (full window)
            if self.renderer2 is not None:
                self.render_window.RemoveRenderer(self.renderer2)
                self.renderer2 = None
                self.image_actor2 = None
            
            self.renderer.SetViewport(0.0, 0.0, 1.0, 1.0)  # Full window
            self.render_window.SetSize(800, 600)  # Normal size
    
    def update_display(self):
        """Update the displayed slice(s)."""
        if self.ct_volume is None:
            return
        
        max_slices = self.ct_volume.GetSize()[2] - 1
        self.current_slice = int(np.clip(self.current_slice, 0, max_slices))
        
        # Update main view (fixed CT)
        ct_slice = extract_axial_slice(self.ct_volume, self.current_slice)
        vtk_img = self.numpy_to_vtk_image(ct_slice)
        self.image_actor.SetInputData(vtk_img)
        
        # Update mask overlays if enabled
        if self.overlay_on:
            # Lung mask (green)
            if self.mask_lung is not None:
                try:
                    lung_slice = extract_axial_slice(self.mask_lung, self.current_slice)
                    overlay = np.zeros((*lung_slice.shape, 3), dtype=np.uint8)
                    mask_bool = lung_slice > 0
                    overlay[mask_bool, 1] = 255  # Green
                    vtk_overlay = self.numpy_to_vtk_image(overlay, is_rgb=True)
                    self.lung_mask_actor.SetInputData(vtk_overlay)
                    self.lung_mask_actor.SetVisibility(1)
                except Exception as e:
                    print(f"Error displaying lung mask: {e}")
                    self.lung_mask_actor.SetVisibility(0)
            else:
                self.lung_mask_actor.SetVisibility(0)
            
            # Infection mask (red)
            if self.mask_infection is not None:
                try:
                    inf_slice = extract_axial_slice(self.mask_infection, self.current_slice)
                    overlay = np.zeros((*inf_slice.shape, 3), dtype=np.uint8)
                    mask_bool = inf_slice > 0
                    overlay[mask_bool, 0] = 255  # Red
                    vtk_overlay = self.numpy_to_vtk_image(overlay, is_rgb=True)
                    self.infection_mask_actor.SetInputData(vtk_overlay)
                    self.infection_mask_actor.SetVisibility(1)
                except Exception as e:
                    print(f"Error displaying infection mask: {e}")
                    self.infection_mask_actor.SetVisibility(0)
            else:
                self.infection_mask_actor.SetVisibility(0)
        else:
            self.lung_mask_actor.SetVisibility(0)
            self.infection_mask_actor.SetVisibility(0)
        
        # Update registered view if enabled (in right viewport)
        if self.show_registered and self.registered_volume is not None and self.renderer2 is not None:
            reg_depth = self.registered_volume.GetSize()[2] - 1
            reg_slice_idx = int(np.clip(self.current_slice, 0, reg_depth))
            reg_slice = extract_axial_slice(self.registered_volume, reg_slice_idx)
            vtk_reg_img = self.numpy_to_vtk_image(reg_slice)
            self.image_actor2.SetInputData(vtk_reg_img)
            self.renderer2.ResetCamera()
        
        self.renderer.ResetCamera()
        self.render_window.Render()
    
    def set_slice(self, slice_idx: int):
        """Set current slice index."""
        if self.ct_volume is None:
            return
        max_slices = self.ct_volume.GetSize()[2] - 1
        self.current_slice = int(np.clip(slice_idx, 0, max_slices))
        self.update_display()
    
    def show(self):
        """Show the viewer with interactive controls."""
        if self.ct_volume is None:
            messagebox.showwarning("Warning", "Please load a CT image first.")
            return
        
        # Setup side-by-side if needed
        if self.show_registered:
            self.setup_side_by_side()
        
        self.update_display()
        self.render_window.Render()
        self.interactor.Start()


def create_gui_viewer():
    """Create tkinter GUI wrapper for the VTK viewer."""
    if not TKINTER_AVAILABLE:
        print("tkinter not available. Running viewer without GUI controls.")
        return None
    
    root = tk.Tk()
    root.title("COVID-CT VTK Viewer")
    root.geometry("450x550")
    
    viewer = COVIDCTVTKViewer()
    
    # Report display frame
    report_frame = ttk.LabelFrame(root, text="Quantification Report", padding=10)
    report_frame.pack(fill="both", expand=True, padx=20, pady=5)
    
    report_text = tk.Text(report_frame, height=6, width=40, wrap=tk.WORD, state=tk.DISABLED)
    report_text.pack(fill="both", expand=True)
    
    def update_report_display():
        """Update the report display area."""
        report_text.config(state=tk.NORMAL)
        report_text.delete(1.0, tk.END)
        if viewer.report_data:
            pct = viewer.report_data.get('percent_infected')
            lesion = viewer.report_data.get('lesion_count')
            volume = viewer.report_data.get('total_volume_ml')
            
            if pct is not None:
                report_text.insert(tk.END, f"Percent Infected: {pct:.2f}%\n")
            else:
                report_text.insert(tk.END, "Percent Infected: N/A\n")
            
            if lesion is not None:
                report_text.insert(tk.END, f"Lesion Count: {lesion}\n")
            else:
                report_text.insert(tk.END, "Lesion Count: N/A\n")
            
            if volume is not None:
                report_text.insert(tk.END, f"Total Volume: {volume:.2f} ml\n")
            else:
                report_text.insert(tk.END, "Total Volume: N/A\n")
            
            if 'image_size' in viewer.report_data:
                report_text.insert(tk.END, f"Image Size: {viewer.report_data['image_size']}\n")
        else:
            report_text.insert(tk.END, "No report loaded. Click 'Load Quant Report' to load report.json")
        report_text.config(state=tk.DISABLED)
    
    # Button callbacks
    def on_load_ct():
        path = filedialog.askopenfilename(
            title="Select Original CT Image (.nii.gz, .mha) OR click Cancel for DICOM folder",
            filetypes=[("NIfTI", "*.nii *.nii.gz"), ("MetaImage", "*.mha *.mhd"), ("All", "*.*")]
        )
        if not path:
            path = filedialog.askdirectory(title="Select DICOM Folder (contains .dcm files)")
        if path:
            if viewer.load_ct(path):
                messagebox.showinfo("Success", f"Loaded: {Path(path).name}")
                update_slider()
    
    def on_load_mask_lung():
        path = filedialog.askopenfilename(
            title="Select Lung Mask (mask_lung.nii.gz)",
            filetypes=[("NIfTI", "*.nii *.nii.gz"), ("All", "*.*")]
        )
        if path:
            if viewer.load_mask_lung(path):
                messagebox.showinfo("Success", f"Loaded lung mask: {Path(path).name}")
    
    def on_load_mask_infection():
        path = filedialog.askopenfilename(
            title="Select Infection Mask (mask_infection.nii.gz)",
            filetypes=[("NIfTI", "*.nii *.nii.gz"), ("All", "*.*")]
        )
        if path:
            if viewer.load_mask_infection(path):
                messagebox.showinfo("Success", f"Loaded infection mask: {Path(path).name}")
    
    def on_load_registered():
        path = filedialog.askopenfilename(
            title="Select Registered Image (moving_rigid.nii.gz)",
            filetypes=[("NIfTI", "*.nii *.nii.gz"), ("All", "*.*")]
        )
        if path:
            if viewer.load_registered(path):
                messagebox.showinfo("Success", f"Loaded registered: {Path(path).name}")
    
    def on_load_report():
        path = filedialog.askopenfilename(
            title="Select Quantification Report (report.json)",
            filetypes=[("JSON", "*.json"), ("All", "*.*")]
        )
        if path:
            if viewer.load_report(path):
                update_report_display()
                messagebox.showinfo("Success", f"Loaded report: {Path(path).name}")
    
    def on_toggle_overlay():
        viewer.toggle_overlay()
    
    def on_toggle_registered():
        viewer.toggle_registered_view()
    
    def on_show_viewer():
        viewer.show()
    
    def update_slider():
        if viewer.ct_volume:
            max_slices = viewer.ct_volume.GetSize()[2] - 1
            slice_slider.config(to=max_slices)
            slice_slider.set(viewer.current_slice)
    
    def on_slider_change(val):
        viewer.set_slice(int(float(val)))
        slice_label.config(text=f"Slice: {int(float(val))}")
    
    # GUI layout
    ttk.Label(root, text="COVID-CT VTK Viewer", font=("Arial", 14, "bold")).pack(pady=10)
    
    # Load buttons
    ttk.Button(root, text="Load Original CT", command=on_load_ct).pack(fill="x", padx=20, pady=3)
    
    ttk.Label(root, text="Segmentation Masks:", font=("Arial", 9, "bold")).pack(pady=(10, 3))
    ttk.Button(root, text="Load Lung Mask", command=on_load_mask_lung).pack(fill="x", padx=20, pady=2)
    ttk.Button(root, text="Load Infection Mask", command=on_load_mask_infection).pack(fill="x", padx=20, pady=2)
    
    ttk.Button(root, text="Load Registered Image", command=on_load_registered).pack(fill="x", padx=20, pady=5)
    ttk.Button(root, text="Load Quant Report", command=on_load_report).pack(fill="x", padx=20, pady=3)
    
    ttk.Separator(root, orient="horizontal").pack(fill="x", padx=20, pady=10)
    
    # Slice control
    slice_frame = ttk.Frame(root)
    slice_frame.pack(fill="x", padx=20, pady=5)
    ttk.Label(slice_frame, text="Slice:").pack(side="left")
    slice_label = ttk.Label(slice_frame, text="0")
    slice_label.pack(side="right")
    slice_slider = ttk.Scale(slice_frame, from_=0, to=100, orient="horizontal", 
                            command=on_slider_change)
    slice_slider.pack(side="left", fill="x", expand=True, padx=5)
    
    # Control buttons
    ttk.Button(root, text="Toggle Mask Overlay", command=on_toggle_overlay).pack(fill="x", padx=20, pady=3)
    ttk.Button(root, text="Toggle Registered View", command=on_toggle_registered).pack(fill="x", padx=20, pady=3)
    
    ttk.Separator(root, orient="horizontal").pack(fill="x", padx=20, pady=10)
    
    # Report display
    update_report_display()
    
    ttk.Button(root, text="Show Viewer", command=on_show_viewer).pack(fill="x", padx=20, pady=5)
    
    ttk.Label(root, text="VTK Viewer - Use mouse to interact with 3D view", 
             font=("Arial", 8), foreground="gray").pack(pady=5)
    
    ttk.Button(root, text="Close", command=root.destroy).pack(fill="x", padx=20, pady=10)
    
    return root, viewer


def main():
    """Main entry point."""
    # Check if VTK is available
    try:
        import vtk
    except ImportError:
        print("ERROR: VTK is not installed.")
        print("Install with: pip install vtk")
        sys.exit(1)
    
    # Create GUI viewer
    if TKINTER_AVAILABLE:
        root, viewer = create_gui_viewer()
        if root:
            root.mainloop()
    else:
        # Command-line usage
        print("VTK Viewer - Command Line Mode")
        print("Usage: python vtk_viewer.py <image_path> [mask_path]")
        if len(sys.argv) > 1:
            viewer = COVIDCTVTKViewer()
            viewer.load_ct(sys.argv[1])
            if len(sys.argv) > 2:
                viewer.load_mask_infection(sys.argv[2])
            viewer.show()
        else:
            print("No image path provided. Run with GUI or provide path as argument.")


if __name__ == "__main__":
    main()
