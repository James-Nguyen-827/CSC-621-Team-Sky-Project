# scripts/quant_only.py (Why am I even bothering writing comments at this point, nobody reads them)
import sys, os, argparse, json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
import SimpleITK as sitk

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from covid_ct.quantification.quantify import percent_infected, lesion_stats

def pick_case_dir():
    r=tk.Tk(); r.withdraw(); r.update()
    d=filedialog.askdirectory(title="Select processed case folder (contains image_resampled.nii.gz, mask_*.nii.gz)")
    r.destroy()
    if not d: raise RuntimeError("No folder selected.")
    return Path(d)

def main():
    ap = argparse.ArgumentParser("Quantify a processed case (picker-enabled).")
    ap.add_argument("--case_dir", help="Folder with image_resampled.nii.gz, mask_lung.nii.gz, mask_infection.nii.gz")
    args = ap.parse_args()

    try:
        case_dir = Path(args.case_dir) if args.case_dir else pick_case_dir()
        img = sitk.ReadImage(str(case_dir/"image_resampled.nii.gz"))
        lung = sitk.ReadImage(str(case_dir/"mask_lung.nii.gz"))
        inf  = sitk.ReadImage(str(case_dir/"mask_infection.nii.gz"))

        pct = percent_infected(lung, inf, min_cc_vox=50)
        lst = lesion_stats(inf)
        report = {"image_size": list(img.GetSize()), "spacing_mm": list(img.GetSpacing()),
                  "percent_infected": pct, **lst}
        (case_dir/"report.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        tk.Tk().withdraw(); messagebox.showinfo("Done", f"Saved report.json in:\n{case_dir}")
    except Exception as e:
        try: tk.Tk().withdraw(); messagebox.showerror("Error", str(e))
        except: pass
        print("Error:", e)

if __name__ == "__main__":
    main()
