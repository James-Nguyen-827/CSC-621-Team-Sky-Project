# covid_ct/io/dicom.py
from pathlib import Path
from typing import List, Optional, Tuple
import SimpleITK as sitk

# DICOM tags we’ll peek at for filtering
TAG_MODALITY = "0008|0060"       # e.g., CT/MR
TAG_SERIES_DESC = "0008|103e"    # SeriesDescription


def list_series(dicom_dir: str) -> List[str]:
    """
    Return a list of SeriesInstanceUIDs found under dicom_dir.
    """
    dicom_dir = Path(dicom_dir)
    reader = sitk.ImageSeriesReader()
    series_ids = reader.GetGDCMSeriesIDs(str(dicom_dir))
    return series_ids or []


def files_for_series(dicom_dir: str, series_uid: str) -> List[str]:
    """
    Return the sorted file list for a specific series UID in dicom_dir.
    """
    reader = sitk.ImageSeriesReader()
    return reader.GetGDCMSeriesFileNames(dicom_dir, series_uid)


def _read_meta(first_file: str) -> Tuple[str, str]:
    """
    Read minimal metadata from a single DICOM file.
    Returns (modality_upper, series_description_upper).
    """
    r = sitk.ImageFileReader()
    r.SetFileName(first_file)
    r.ReadImageInformation()
    modality = r.GetMetaData(TAG_MODALITY) if r.HasMetaDataKey(TAG_MODALITY) else ""
    desc = r.GetMetaData(TAG_SERIES_DESC) if r.HasMetaDataKey(TAG_SERIES_DESC) else ""
    return modality.upper(), desc.upper()


def pick_best_ct_series(dicom_dir: str) -> Optional[List[str]]:
    """
    Pick the 'best' CT series in a folder:
      - Must be CT if available (fallback to any modality if none say CT)
      - Strongly down-rank SCOUT/LOCALIZER series
      - Prefer the series with more files (full volumetric scan)
    Returns the file list for the chosen series, or None.
    """
    dicom_dir = Path(dicom_dir)
    reader = sitk.ImageSeriesReader()
    series_ids = reader.GetGDCMSeriesIDs(str(dicom_dir)) or []
    if not series_ids:
        return None

    candidates = []
    for sid in series_ids:
        files = reader.GetGDCMSeriesFileNames(str(dicom_dir), sid)
        if not files:
            continue
        modality, desc = _read_meta(files[0])
        is_ct = (modality == "CT")
        is_scout = ("SCOUT" in desc) or ("LOCALIZER" in desc) or ("TOP" in desc)
        # score by slice count; penalize scout heavily
        score = len(files) - (10000 if is_scout else 0)
        candidates.append((score, is_ct, not is_scout, files))

    if not candidates:
        return None

    # Prefer CT-only pool; else use all
    pool = [c for c in candidates if c[1]] or candidates
    # Highest score wins
    pool.sort(key=lambda x: x[0], reverse=True)
    return pool[0][3]


def read_dicom_series(dicom_dir: str, series_uid: str = None) -> sitk.Image:
    """
    Read a DICOM series to a SimpleITK Image.

    If series_uid is None, automatically picks a good CT series in the folder.
    Otherwise, loads the specified series UID.
    """
    if series_uid:
        files = files_for_series(dicom_dir, series_uid)
        if not files:
            raise RuntimeError(f"No files for series {series_uid} in {dicom_dir}")
    else:
        files = pick_best_ct_series(dicom_dir)
        if not files:
            raise RuntimeError(f"No readable DICOM series found in {dicom_dir}")

    reader = sitk.ImageSeriesReader()
    reader.SetFileNames(files)
    img = reader.Execute()
    return img


def write_nifti(img: sitk.Image, out_path: str) -> None:
    """
    Save a SimpleITK Image to NIfTI (.nii or .nii.gz).
    """
    sitk.WriteImage(img, str(out_path))


# ----- Optional convenience: quick probe -----
def probe_series(dicom_dir: str) -> List[Tuple[str, str, int]]:
    """
    Return [(series_uid, 'CT|MR ... / description', num_files), ...] for quick debugging.
    """
    out = []
    reader = sitk.ImageSeriesReader()
    for sid in list_series(dicom_dir):
        files = reader.GetGDCMSeriesFileNames(dicom_dir, sid)
        if not files:
            continue
        modality, desc = _read_meta(files[0])
        out.append((sid, f"{modality} / {desc}", len(files)))
    return out
