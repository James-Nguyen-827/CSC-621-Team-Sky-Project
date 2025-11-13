# covid_ct/preprocess/resample.py
import SimpleITK as sitk

def clip_and_norm(img, hu_min=-1000, hu_max=400, zscore=True): #(had to look up other people's code on github for this one)
    """
    Clip HU to [hu_min, hu_max], scale to [0,1], optional z-score normalize.
    """
    img = sitk.Cast(img, sitk.sitkFloat32)
    img = sitk.Clamp(img, sitk.sitkFloat32, hu_min, hu_max)
    img = (img - hu_min) / max(1e-6, (hu_max - hu_min))
    if zscore:
        stats = sitk.StatisticsImageFilter()
        stats.Execute(img)
        mean = stats.GetMean()
        std = stats.GetSigma() or 1.0
        img = (img - mean) / std
    return img

def resample_isotropic(img, spacing=(1.25, 1.25, 1.25), interp=sitk.sitkLinear): 
    """
    Resample to isotropic spacing (mm) with identity transform.
    """
    original_spacing = img.GetSpacing()
    original_size = img.GetSize()
    new_size = [
        int(round(osz * ospc / nspc))
        for osz, ospc, nspc in zip(original_size, original_spacing, spacing)
    ]
    ref = sitk.Image(new_size, img.GetPixelID())
    ref.SetSpacing(spacing)
    ref.SetOrigin(img.GetOrigin())
    ref.SetDirection(img.GetDirection())
    return sitk.Resample(img, ref, sitk.Transform(), interp, 0.0, img.GetPixelID())

def resample_like(img, reference, interp=sitk.sitkLinear):
    """
    Resample 'img' onto 'reference' geometry.
    """
    return sitk.Resample(
        img,
        reference,
        sitk.Transform(),
        interp,
        0.0,
        img.GetPixelID()
    )
