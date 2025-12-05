# scripts/make_3d.py
import SimpleITK as sitk
import numpy as np
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
from skimage.measure import marching_cubes
import trimesh
try:
    import pyvista as pv
    PV = True
except Exception:
    PV = False


def pick_case_folder():
    root = tk.Tk(); root.withdraw(); root.update()
    d = filedialog.askdirectory(title="Select processed case folder (with NIfTIs)")
    root.destroy()
    if not d:
        raise RuntimeError("No folder selected.")
    return Path(d)


def mesh_from_mask(mask_img):
    arr = sitk.GetArrayFromImage(mask_img).astype(np.uint8)
    if arr.max() == 0:
        raise RuntimeError("Mask is empty.")
    verts, faces, _, _ = marching_cubes(arr, level=0.5, spacing=mask_img.GetSpacing()[::-1])
    return verts, faces


def save_stl(verts, faces, out_path):
    tri = np.column_stack([np.full(len(faces), 3), faces]).astype(np.int64)
    mesh = trimesh.Trimesh(vertices=verts[:, ::-1], faces=tri[:, 1:])
    mesh.export(out_path)


def main():
    try:
        case = pick_case_folder()
        img = sitk.ReadImage(str(case / "image_resampled.nii.gz"))
        lung = sitk.ReadImage(str(case / "mask_lung.nii.gz"))
        inf = sitk.ReadImage(str(case / "mask_infection.nii.gz"))

        for name, mask in [("lung", lung), ("infection", inf)]:
            try:
                v, f = mesh_from_mask(mask)
            except RuntimeError:
                print(f"{name} mask empty; skipping.")
                continue
            stl = case / f"{name}.stl"
            save_stl(v, f, stl)
            print("Saved", stl)
            if PV:
                p = pv.Plotter(off_screen=True)
                p.add_mesh(pv.wrap({"vertices": v,
                                    "faces": np.hstack([np.full((len(f), 1), 3), f]).astype(np.int64)}),
                           opacity=0.5, color="cyan" if name == "lung" else "magenta")
                p.show(screenshot=str(case / f"{name}_3d.png"))
        tk.Tk().withdraw()
        messagebox.showinfo("Done", f"3D models saved in:\n{case}")
    except Exception as e:
        tk.Tk().withdraw(); messagebox.showerror("Error", str(e))
        print("Error:", e)


if __name__ == "__main__":
    main()
