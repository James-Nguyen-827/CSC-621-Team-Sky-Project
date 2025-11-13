# scripts/launcher.py (main GUI launcher for all tools, WHY AM I DOING THIS TO MYSELF, why did I write all the other scripts)
import sys, os
import tkinter as tk
from tkinter import ttk, messagebox

# run sub-scripts as modules to reuse their pickers (Do Whatever at this point)
def run_seg():        os.system(f'"{sys.executable}" -m scripts.seg_only')
def run_reg():        os.system(f'"{sys.executable}" -m scripts.register_pair')
def run_quant():      os.system(f'"{sys.executable}" -m scripts.quant_only')
def run_batch():      os.system(f'"{sys.executable}" -m scripts.batch_gui')
def run_compare():    os.system(f'"{sys.executable}" -m scripts.comparator')

def main():
    root = tk.Tk(); root.title("Covid-CT Toolkit")
    root.geometry("360x260"); root.resizable(False, False)

    ttk.Label(root, text="Select an operation:", font=("Segoe UI", 11, "bold")).pack(pady=12)

    for text, fn in [
        ("Segmentation (single study)", run_seg),
        ("Registration (pair)",         run_reg),
        ("Quantification (single case)",run_quant),
        ("Batch processing (dataset)",  run_batch),
        ("Viewer / Comparator",         run_compare),
    ]:
        ttk.Button(root, text=text, command=fn).pack(fill="x", padx=16, pady=6)

    ttk.Button(root, text="Close", command=root.destroy).pack(pady=8)
    root.mainloop()

if __name__ == "__main__":
    main()
