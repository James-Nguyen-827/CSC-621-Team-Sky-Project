# covid_ct/io/series_select.py
from pathlib import Path
import SimpleITK as sitk

TAG_MODALITY = "0008|0060"       # CT/MR
TAG_SERIES_DESC = "0008|103e"    # SeriesDescription

def _read_meta(first_file):
    r = sitk.ImageFileReader()
    r.SetFileName(first_file)
    r.ReadImageInformation()
    modality = r.GetMetaData(TAG_MODALITY) if r.HasMetaDataKey(TAG_MODALITY) else ""
    desc = r.GetMetaData(TAG_SERIES_DESC) if r.HasMetaDataKey(TAG_SERIES_DESC) else ""
    return modality.upper(), desc.upper()

def best_series_in_dir(dicom_dir):
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
        is_ct = modality == "CT"
        is_scout = any(k in desc for k in ["SCOUT", "LOCALIZER", "TOP"])
        score = len(files) - (10000 if is_scout else 0)
        candidates.append((score, is_ct, not is_scout, files))

    if not candidates:
        return None

    pool = [c for c in candidates if c[1]] or candidates
    pool.sort(key=lambda x: x[0], reverse=True)
    return pool[0][3]
