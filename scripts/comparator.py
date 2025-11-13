# scripts/comparator.py
import argparse, sys
from pathlib import Path
import numpy as np
import SimpleITK as sitk
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog, messagebox

# ---------- pickers ----------
def choose_folder(title):
    root = tk.Tk(); root.withdraw(); root.update()
    folder = filedialog.askdirectory(title=title)
    root.destroy()
    if not folder: raise RuntimeError("No folder selected.")
    return folder

def choose_file(title, patterns):
    root = tk.Tk(); root.withdraw(); root.update()
    f = filedialog.askopenfilename(title=title, filetypes=patterns)
    root.destroy()
    if not f: raise RuntimeError("No file selected.")
    return f

def choose_plane_dialog(default="axial"):
    root = tk.Tk(); root.title("Pick viewing plane")
    var = tk.StringVar(value=default)
    for text, val in [("Axial (Z)", "axial"), ("Coronal (Y)", "coronal"), ("Sagittal (X)", "sagittal")]:
        tk.Radiobutton(root, text=text, variable=var, value=val, anchor="w").pack(fill="x", padx=12, pady=4)
    chosen = {"val": None}
    def ok(): chosen["val"] = var.get(); root.destroy()
    tk.Button(root, text="OK", command=ok).pack(padx=12, pady=12)
    root.mainloop()
    if not chosen["val"]: raise RuntimeError("No plane chosen.")
    return chosen["val"]

# ---------- I/O & helpers ----------
def load_dicom_series(dicom_dir):
    r = sitk.ImageSeriesReader()
    ids = r.GetGDCMSeriesIDs(str(dicom_dir))
    if not ids: raise RuntimeError(f"No DICOM series found in {dicom_dir}")
    files = r.GetGDCMSeriesFileNames(str(dicom_dir), ids[0])
    r.SetFileNames(files)
    return r.Execute()

def resample_like(img, reference, interp=sitk.sitkLinear):
    return sitk.Resample(img, reference, sitk.Transform(), interp, 0.0, sitk.sitkFloat32)

def np_slice(img, plane, idx):
    a = sitk.GetArrayFromImage(img)  # [z,y,x]
    if plane == "axial":    idx = np.clip(idx, 0, a.shape[0]-1); return a[idx, :, :]
    if plane == "coronal":  idx = np.clip(idx, 0, a.shape[1]-1); return a[:, idx, :]
    if plane == "sagittal": idx = np.clip(idx, 0, a.shape[2]-1); return a[:, :, idx]
    raise ValueError("plane must be axial/coronal/sagittal")

def size_along(img, plane):
    x,y,z = img.GetSize()
    return {"axial": z, "coronal": y, "sagittal": x}[plane]

# ---------- core ----------
def compare(dicom_dir, proc_file, plane="axial", slice_idx=None, save=None):
    print("Loading original DICOM from:\n ", dicom_dir)
    print("Loading processed image:\n ", proc_file)

    raw  = load_dicom_series(dicom_dir)
    proc = sitk.ReadImage(proc_file)

    # Align raw to processed geometry
    raw_on_proc = resample_like(raw, proc, interp=sitk.sitkLinear)

    n_slices = size_along(proc, plane)
    if slice_idx is None: slice_idx = n_slices // 2
    slice_idx = int(np.clip(slice_idx, 0, n_slices-1))

    raw_np  = np_slice(raw_on_proc, plane, slice_idx)
    proc_np = np_slice(proc,       plane, slice_idx)

    # Plot
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    plt.imshow(raw_np, cmap="gray")
    plt.title(f"Original DICOM (reformatted)\n{Path(dicom_dir).name}")
    plt.axis("off")

    plt.subplot(1, 2, 2)
    plt.imshow(proc_np, cmap="gray")
    plt.title(f"Processed ({plane})\n{Path(proc_file).name}")
    plt.axis("off")

    plt.tight_layout()
    if save:
        plt.savefig(save, bbox_inches="tight", dpi=200)
        print("Saved comparison to:", save)
    else:
        plt.show()

# ---------- entry ----------
def main():
    ap = argparse.ArgumentParser(description="Compare raw DICOM vs processed NIfTI (choose plane).")
    ap.add_argument("--dicom_dir")
    ap.add_argument("--processed_file")
    ap.add_argument("--plane", choices=["axial","coronal","sagittal"])
    ap.add_argument("--slice", type=int)
    ap.add_argument("--save")
    args = ap.parse_args()

    auto_pick = (len(sys.argv) == 1) or (not args.dicom_dir or not args.processed_file) or (args.plane is None)
    try:
        dicom_dir = args.dicom_dir
        proc_file = args.processed_file
        plane     = args.plane or "axial"

        if auto_pick:
            if not dicom_dir:
                dicom_dir = choose_folder("Select DICOM series folder")
            if not proc_file:
                proc_file = choose_file("Select processed NIfTI (image_resampled.nii.gz)",
                                       [("NIfTI files","*.nii *.nii.gz"), ("All files","*.*")])
            if args.plane is None:
                plane = choose_plane_dialog(default="axial")

        compare(dicom_dir, proc_file, plane=plane, slice_idx=args.slice, save=args.save)

    except Exception as e:
        try:
            root = tk.Tk(); root.withdraw()
            messagebox.showerror("Error", str(e))
            root.destroy()
        except Exception:
            pass
        print("Error:", e)

if __name__ == "__main__":
    main()
