# scripts/batch_gui.py
import sys, os, argparse
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

# allow imports of our batch code
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import scripts.batch_process as batch  # reuse the functions you already have

def pick_folder(title):
    r=tk.Tk(); r.withdraw(); r.update()
    d=filedialog.askdirectory(title=title); r.destroy()
    if not d: raise RuntimeError("No folder selected.")
    return d

def pick_save_csv(default="batch_log.csv"):
    r=tk.Tk(); r.withdraw(); r.update()
    f=filedialog.asksaveasfilename(title="Save batch log CSV as…", initialfile=default,
                                   defaultextension=".csv", filetypes=[("CSV","*.csv")])
    r.destroy()
    if not f: raise RuntimeError("No file selected.")
    return f

def main():
    ap = argparse.ArgumentParser("Batch process (picker-enabled).")
    ap.add_argument("--root"); ap.add_argument("--out_root"); ap.add_argument("--log_csv")
    args = ap.parse_args()
    try:
        root = args.root or pick_folder("Pick ROOT of MIDRC-RICORD-1A")
        out_root = args.out_root or pick_folder("Pick OUTPUT ROOT folder (results will mirror the tree)")
        log_csv = args.log_csv or pick_save_csv()
        batch.main(root, out_root, log_csv)  # calls your existing function
        tk.Tk().withdraw(); messagebox.showinfo("Done", f"Processed. Log saved at:\n{log_csv}")
    except Exception as e:
        try: tk.Tk().withdraw(); messagebox.showerror("Error", str(e))
        except: pass
        print("Error:", e)

if __name__ == "__main__":
    main()
