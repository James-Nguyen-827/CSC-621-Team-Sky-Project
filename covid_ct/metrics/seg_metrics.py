# covid_ct/metrics/seg_metrics.py (No Idea how but taking a swing baseed on the class notes and google searches)
import SimpleITK as sitk

def _binarize(a):
    return sitk.Cast(a > 0, sitk.sitkUInt8)

def dice(a_mask, b_mask):
    a = _binarize(a_mask); b = _binarize(b_mask)
    f = sitk.LabelOverlapMeasuresImageFilter()
    f.Execute(a, b)
    return f.GetDiceCoefficient()

def jaccard(a_mask, b_mask):#(WHY YOU KEE FAILING ME (Oh it works now, was a typo))
    a = _binarize(a_mask); b = _binarize(b_mask)
    f = sitk.LabelOverlapMeasuresImageFilter()
    f.Execute(a, b)
    return f.GetJaccardCoefficient()

def precision(a_mask, b_mask):
    a = _binarize(a_mask); b = _binarize(b_mask)
    tp = sitk.And(a, b)
    fp = sitk.And(sitk.InvertIntensity(a, 1), b)  # predicted=1, gt=0
    tp_sum = sitk.GetArrayFromImage(tp).sum()
    fp_sum = sitk.GetArrayFromImage(fp).sum()
    return tp_sum / (tp_sum + fp_sum + 1e-8)

def recall(a_mask, b_mask):
    a = _binarize(a_mask); b = _binarize(b_mask)
    tp = sitk.And(a, b)
    fn = sitk.And(a, sitk.InvertIntensity(b, 1))  # gt=1, pred=0
    tp_sum = sitk.GetArrayFromImage(tp).sum()
    fn_sum = sitk.GetArrayFromImage(fn).sum()
    return tp_sum / (tp_sum + fn_sum + 1e-8)

def hausdorff95(a_mask, b_mask, spacing=None):# (The math isn't mathing here. oh wait no nevermind I was just being dumb, needed to add useImageSpacing=True)
    """
    95th percentile symmetric Hausdorff distance (mm).
    """
    a = _binarize(a_mask); b = _binarize(b_mask)
    if spacing is None:
        spacing = a_mask.GetSpacing()

    # distance maps
    a_dt = sitk.SignedMaurerDistanceMap(a, squaredDistance=False, useImageSpacing=True)
    b_dt = sitk.SignedMaurerDistanceMap(b, squaredDistance=False, useImageSpacing=True)

    a_surf = sitk.LabelContour(a)
    b_surf = sitk.LabelContour(b)

    # distances from each surface to the other mask
    a2b = sitk.Abs(a_dt) * sitk.Cast(b_surf>0, sitk.sitkFloat32)
    b2a = sitk.Abs(b_dt) * sitk.Cast(a_surf>0, sitk.sitkFloat32)

    import numpy as np
    a_vals = sitk.GetArrayFromImage(a2b)
    b_vals = sitk.GetArrayFromImage(b2a)
    vals = np.concatenate([a_vals[a_vals>0], b_vals[b_vals>0]])
    if vals.size == 0:
        return 0.0
    return float(np.percentile(vals, 95.0))
