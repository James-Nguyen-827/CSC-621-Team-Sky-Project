# scripts/seg_only.py
import argparse, sys, os
from pathlib import Path
import SimpleITK as sitk
import tkinter as tk
from tkinter import filedialog, messagebox

# make imports work even if run directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from covid_ct.io.dicom import read_dicom_series, write_nifti
from covid_ct.preprocess.resample import clip_and_norm, resample_isotropic
from covid_ct.segmentation.auto_seed import auto_lung_seeds
from covid_ct.segmentation.region_growing import lung_mask_region_growing
from covid_ct.segmentation.levelset import lesion_levelset

# ---------- GUI pickers ----------
def pick_dicom_dir():
    root = tk.Tk(); root.withdraw(); root.update()
    d = filedialog.askdirectory(title="Select DICOM series folder (contains .dcm files)")
    root.destroy()
    if not d:
        raise RuntimeError("No DICOM folder selected.")
    return d

def pick_out_dir(default_name="output"):
    root = tk.Tk(); root.withdraw(); root.update()
    d = filedialog.askdirectory(title="Select output folder (a subfolder will be created)")
    root.destroy()
    if not d:
        raise RuntimeError("No output folder selected.")
    out = Path(d) / default_name
    out.mkdir(parents=True, exist_ok=True)
    return str(out)

# ---------- small helper ----------
def save_overlay(image, lung, inf, out_png, z=None):
    if z is None or z <= 0:
        z = image.GetSize()[2] // 2
    arr = sitk.GetArrayFromImage(image)[z, :, :]
    l2d = sitk.GetArrayFromImage(lung)[z, :, :]
    i2d = sitk.GetArrayFromImage(inf)[z, :, :]
    import matplotlib.pyplot as plt
    plt.figure()
    plt.imshow(arr, cmap='gray')
    plt.contour(l2d == 1, linewidths=0.7)
    plt.contour(i2d == 1, linewidths=0.7)
    plt.axis('off'); plt.savefig(out_png, bbox_inches='tight', dpi=200); plt.close()

# ---------- core ----------
def run_once(dicom_dir: str, out_dir: str):
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)

    # 1) Read & preprocess
    img_raw = read_dicom_series(dicom_dir)
    img_clip = sitk.Clamp(img_raw, sitk.sitkFloat32, -1000, 400)
    img_r = resample_isotropic(img_clip, (1.25, 1.25, 1.25))
    img_n = clip_and_norm(img_r, -1000, 400, zscore=True)

    # 2) Auto seeds → region growing lungs
    seeds = auto_lung_seeds(img_r, air_hu=-700)
    print("Seeds:", seeds)
    lung = lung_mask_region_growing(img_r, seeds, lower=-950, upper=-500)

    # 3) Infection init (simple threshold) → level-set refine
    thr = sitk.BinaryThreshold(img_n, 0.55, 1.0)
    infection_init = thr & lung
    infection = lesion_levelset(img_n, infection_init, iterations=120, curvature=0.5, propagation=1.0, advection=1.0)

    # 4) Save outputs
    write_nifti(img_r, out / "image_resampled.nii.gz")
    write_nifti(lung, out / "mask_lung.nii.gz")
    write_nifti(infection, out / "mask_infection.nii.gz")
    save_overlay(img_r, lung, infection, out / "qc_overlay.png")

    print(f"Saved to: {out}")
    return str(out)

# ---------- entry ----------
def main():
    ap = argparse.ArgumentParser(description="Segment a single DICOM study (picker-enabled).")
    ap.add_argument("--dicom_dir", help="Folder containing DICOM series.")
    ap.add_argument("--out_dir", help="Output folder (created if missing).")
    args = ap.parse_args()

    # Auto-pick if missing (so double-click works)
    try:
        dicom_dir = args.dicom_dir or pick_dicom_dir()
        # default subfolder name = last study folder
        default_name = Path(dicom_dir).name
        out_dir = args.out_dir or pick_out_dir(default_name=default_name)

        out = run_once(dicom_dir, out_dir)

        # friendly popup
        try:
            root = tk.Tk(); root.withdraw()
            messagebox.showinfo("Done", f"Outputs saved to:\n{out}")
            root.destroy()
        except Exception:
            pass

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
