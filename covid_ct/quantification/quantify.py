# covid_ct/quantification/quantify.py
import SimpleITK as sitk

def _voxel_volume(img):
    sx, sy, sz = img.GetSpacing()
    return float(sx * sy * sz)

def percent_infected(lung_mask, infection_mask, min_cc_vox=50):
    """
    % infected lung volume = (infection ∩ lung) / lung * 100
    min_cc_vox: remove tiny components from infection.
    """
    lung = sitk.Cast(lung_mask > 0, sitk.sitkUInt8)
    inf  = sitk.Cast(infection_mask > 0, sitk.sitkUInt8)

    # keep infection only inside lungs (Would be nice if no infection outside lungs XD)
    inf = inf & lung

    # remove tiny components
    cc = sitk.ConnectedComponent(inf)
    stats = sitk.LabelShapeStatisticsImageFilter(); stats.Execute(cc)
    keep = [l for l in stats.GetLabels() if stats.GetNumberOfPixels(l) >= min_cc_vox]
    if keep:
        kept = sitk.Image(cc.GetSize(), sitk.sitkUInt8); kept.CopyInformation(cc)
        for l in keep:
            kept = kept | sitk.Equal(cc, l)
        inf = kept
    else:
        inf = sitk.Image(cc.GetSize(), sitk.sitkUInt8); inf.CopyInformation(cc)

    lung_vox = sitk.StatisticsImageFilter(); lung_vox.Execute(lung)
    inf_vox  = sitk.StatisticsImageFilter();  inf_vox.Execute(inf)

    if lung_vox.GetSum() == 0:
        return 0.0
    return (inf_vox.GetSum() / lung_vox.GetSum()) * 100.0

def lesion_stats(infection_mask):
    """
    Returns dict with lesion count and total volume (ml).
    """
    vox_vol = _voxel_volume(infection_mask)
    inf = sitk.Cast(infection_mask > 0, sitk.sitkUInt8)
    cc = sitk.ConnectedComponent(inf)
    stats = sitk.LabelShapeStatisticsImageFilter(); stats.Execute(cc)
    labels = stats.GetLabels()
    total_vox = sum(stats.GetNumberOfPixels(l) for l in labels)
    total_ml = (total_vox * vox_vol) / 1000.0
    return {
        "lesion_count": len(labels),
        "total_voxels": int(total_vox),
        "total_volume_ml": float(total_ml),
    }
