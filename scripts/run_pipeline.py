# scripts/run_pipeline.py
import argparse, json, yaml
from pathlib import Path
import SimpleITK as sitk

from covid_ct.io.dicom import read_dicom_series, write_nifti
from covid_ct.preprocess.resample import clip_and_norm, resample_isotropic
from covid_ct.segmentation.auto_seed import auto_lung_seeds
from covid_ct.segmentation.region_growing import lung_mask_region_growing
from covid_ct.segmentation.levelset import lesion_levelset
from covid_ct.quantification.quantify import percent_infected, lesion_stats

def save_overlay(image, lung, inf, out_png, z=None):
    if z is None or z <= 0:
        z = image.GetSize()[2] // 2
    arr = sitk.GetArrayFromImage(image)[:, :, z]
    lung2d = sitk.GetArrayFromImage(lung)[:, :, z]
    inf2d  = sitk.GetArrayFromImage(inf)[:, :, z]
    import matplotlib.pyplot as plt
    plt.figure()
    plt.imshow(arr, cmap='gray')
    plt.contour(lung2d == 1, linewidths=0.7)   # lungs
    plt.contour(inf2d  == 1, linewidths=0.7)   # infection
    plt.axis('off'); plt.savefig(out_png, bbox_inches='tight', dpi=200); plt.close()

def main(cfg_path, dicom_dir, out_dir):
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    cfg = yaml.safe_load(open(cfg_path, "r"))

    # --- 1) Read DICOM + preprocess ---
    img_raw = read_dicom_series(dicom_dir)
    img_clip = sitk.Clamp(img_raw, sitk.sitkFloat32, *cfg["preprocess"]["clip_hu"])
    img_r = resample_isotropic(img_clip, tuple(cfg["preprocess"]["target_spacing"]))
    img_n = clip_and_norm(img_r, *cfg["preprocess"]["clip_hu"], cfg["preprocess"]["zscore"])

    # --- 2) Seeds (config list or auto) ---
    seeds = cfg["segmentation"]["region_growing"].get("seeds") or []
    if not seeds:
        seeds = auto_lung_seeds(img_r, air_hu=-700)
    print("Seeds:", seeds)

    # --- 3) Segmentation: lungs + infection ---
    lung = lung_mask_region_growing(
        img_r, seeds,
        lower=cfg["segmentation"]["region_growing"]["lower"],
        upper=cfg["segmentation"]["region_growing"]["upper"]
    )
    thr = sitk.BinaryThreshold(img_n, 0.55, 1.0)   # crude init; tweak later if needed
    infection_init = thr & lung
    infection = lesion_levelset(
        img_n, infection_init,
        iterations=cfg["segmentation"]["levelset"]["iterations"],
        curvature=cfg["segmentation"]["levelset"]["curvature"],
        propagation=cfg["segmentation"]["levelset"]["propagation"],
        advection=cfg["segmentation"]["levelset"]["advection"]
    )

    # --- 4) Quantification ---
    pct = percent_infected(lung, infection, cfg["quantification"]["min_lesion_cc"])
    lst = lesion_stats(infection)

    # --- 5) Save outputs ---
    write_nifti(img_r, out / "image_resampled.nii.gz")
    write_nifti(lung, out / "mask_lung.nii.gz")
    write_nifti(infection, out / "mask_infection.nii.gz")

    report = {
        "dicom_dir": str(dicom_dir),
        "image_size": list(img_r.GetSize()),
        "spacing_mm": list(img_r.GetSpacing()),
        "percent_infected": pct,
        **lst
    }
    (out / "report.json").write_text(json.dumps(report, indent=2))

    if cfg.get("visualization", {}).get("save_overlay", True):
        z = cfg.get("visualization", {}).get("qc_slice_index", 0) or None
        save_overlay(img_r, lung, infection, out / "qc_overlay.png", z=z)

    print(f"Done. % infected = {pct:.2f} | outputs -> {out}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/default.yaml")
    ap.add_argument("--dicom_dir", required=True)
    ap.add_argument("--out_dir", required=True)
    args = ap.parse_args()
    main(args.config, args.dicom_dir, args.out_dir)
