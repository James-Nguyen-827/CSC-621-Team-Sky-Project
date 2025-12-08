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
    d = filedialog.askdirectory(
        title="Select processed case folder (with NIfTIs)"
    )
    root.destroy()
    if not d:
        raise RuntimeError("No folder selected.")
    return Path(d)


def mesh_from_mask(mask_img):
    arr = sitk.GetArrayFromImage(mask_img).astype(np.uint8)
    if arr.max() == 0:
        raise RuntimeError("Mask is empty.")
    # marching_cubes expects z, y, x spacing; SimpleITK spacing is x, y, z
    spacing = mask_img.GetSpacing()[::-1]
    verts, faces, _, _ = marching_cubes(arr, level=0.5, spacing=spacing)
    return verts, faces


def save_stl(verts, faces, out_path):
    # trimesh wants faces as (N, 3)
    mesh = trimesh.Trimesh(vertices=verts[:, ::-1], faces=faces.astype(np.int64))
    mesh.export(out_path)


def pv_polydata_from_mesh(verts, faces):
    """
    Build a PyVista PolyData from marching_cubes output.
    faces must be (N, 3); PyVista wants a flat array [3, i, j, k, 3, ...].
    """
    n_faces = faces.shape[0]
    faces_pv = np.hstack(
        [np.full((n_faces, 1), 3, dtype=np.int64), faces.astype(np.int64)]
    ).ravel()
    return pv.PolyData(verts, faces_pv)


def main():
    try:
        case = pick_case_folder()

        img = sitk.ReadImage(str(case / "image_resampled.nii.gz"))
        lung = sitk.ReadImage(str(case / "mask_lung.nii.gz"))
        inf = sitk.ReadImage(str(case / "mask_infection.nii.gz"))

        meshes = {}   # store verts/faces for combined render

        # ---- build STL meshes for each mask ----
        for name, mask in [("lung", lung), ("infection", inf)]:
            try:
                v, f = mesh_from_mask(mask)
            except RuntimeError:
                print(f"{name} mask empty; skipping.")
                continue

            meshes[name] = (v, f)   # keep for PyVista

            stl = case / f"{name}.stl"
            save_stl(v, f, stl)
            print("Saved", stl)

            # old per-structure PNG (optional, keep if you like)
            if PV:
                p = pv.Plotter(off_screen=True)
                poly = pv_polydata_from_mesh(v, f)
                p.add_mesh(
                    poly,
                    opacity=0.5,
                    color="cyan" if name == "lung" else "magenta",
                    show_edges=False,
                )
                p.background_color = "black"
                p.show(screenshot=str(case / f"{name}_3d.png"))

        # ---- combined 3D view: translucent lung + solid infection ----
        if PV and meshes:
            p = pv.Plotter(off_screen=True)

            # lung shell (more transparent)
            if "lung" in meshes:
                v_l, f_l = meshes["lung"]
                lung_poly = pv_polydata_from_mesh(v_l, f_l)
                p.add_mesh(
                    lung_poly,
                    opacity=0.25,      # dial transparency here
                    color="cyan",
                    show_edges=False,
                )

            # infection inside (more opaque)
            if "infection" in meshes:
                v_i, f_i = meshes["infection"]
                inf_poly = pv_polydata_from_mesh(v_i, f_i)
                p.add_mesh(
                    inf_poly,
                    opacity=0.9,       # almost solid
                    color="magenta",
                    show_edges=False,
                )

            p.background_color = "black"
            p.show(screenshot=str(case / "lung_infection_3d.png"))
            print("Saved combined 3D render:", case / "lung_infection_3d.png")

        tk.Tk().withdraw()
        messagebox.showinfo("Done", f"3D models saved in:\n{case}")

    except Exception as e:
        tk.Tk().withdraw()
        messagebox.showerror("Error", str(e))
        print("Error:", e)


if __name__ == "__main__":
    main()
