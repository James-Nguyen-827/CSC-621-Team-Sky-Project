# scripts/register_pair.py
import sys, os, argparse
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
import SimpleITK as sitk

# allow "python register_pair.py" to import project code
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from covid_ct.io.dicom import read_dicom_series, write_nifti
from covid_ct.registration.rigid_mi import rigid_register_mi
from covid_ct.registration.bspline import bspline_deformable

def pick_folder(title):
    r=tk.Tk(); r.withdraw(); r.update()
    d=filedialog.askdirectory(title=title); r.destroy()
    if not d: raise RuntimeError("Selection cancelled.")
    return d

def pick_out_dir(default_name="registered"):
    r=tk.Tk(); r.withdraw(); r.update()
    d=filedialog.askdirectory(title="Select output folder (a subfolder will be created)"); r.destroy()
    if not d: raise RuntimeError("No output folder selected.")
    out = Path(d)/default_name; out.mkdir(parents=True, exist_ok=True); return str(out)

def run_once(fixed_dir, moving_dir, out_dir, do_bspline=False):
    fixed  = read_dicom_series(fixed_dir)
    moving = read_dicom_series(moving_dir)

    # 1) Rigid
    print("Running rigid registration (MI)…")
    moved_rigid, rigid_tx = rigid_register_mi(fixed, moving, iters=200)
    write_nifti(moved_rigid, Path(out_dir)/"moving_rigid.nii.gz")
    sitk.WriteTransform(rigid_tx, str(Path(out_dir)/"rigid.tfm"))

    # 2) Optional B-spline ( I dont have to do it but I wont be an engineering student if I dont make life hard for myself)
    final_img = moved_rigid; final_tx = rigid_tx
    if do_bspline:
        print("Running B-spline deformable…")
        moved_def, def_tx = bspline_deformable(
            fixed=fixed, moving=moving, iters=100, initial_transform=rigid_tx
        )
        write_nifti(moved_def, Path(out_dir)/"moving_bspline.nii.gz")
        sitk.WriteTransform(def_tx, str(Path(out_dir)/"bspline.tfm"))
        final_img, final_tx = moved_def, def_tx

    print("Saved to:", out_dir)
    return final_img, final_tx

def main():
    ap = argparse.ArgumentParser("Register two DICOM studies (picker-enabled).")
    ap.add_argument("--fixed_dir"); ap.add_argument("--moving_dir")
    ap.add_argument("--out_dir"); ap.add_argument("--bspline", action="store_true")
    args = ap.parse_args()

    try:
        fixed_dir  = args.fixed_dir  or pick_folder("Pick FIXED DICOM series (reference)")
        moving_dir = args.moving_dir or pick_folder("Pick MOVING DICOM series (to be aligned)")
        default_name = f"{Path(moving_dir).name}_to_{Path(fixed_dir).name}"
        out_dir = args.out_dir or pick_out_dir(default_name)
        run_once(fixed_dir, moving_dir, out_dir, do_bspline=args.bspline)
        tk.Tk().withdraw(); messagebox.showinfo("Done", f"Outputs saved to:\n{out_dir}")
    except Exception as e:
        try: tk.Tk().withdraw(); messagebox.showerror("Error", str(e))
        except: pass
        print("Error:", e)

if __name__ == "__main__":
    main()
