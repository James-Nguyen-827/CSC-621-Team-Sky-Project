# covid_ct/segmentation/region_growing.py (simplified lung mask using region growing, nothing fancy)
import SimpleITK as sitk

def _keep_largest_components(bin_img, k=2):
    cc = sitk.ConnectedComponent(bin_img)
    stats = sitk.LabelShapeStatisticsImageFilter(); stats.Execute(cc)
    labels = sorted(stats.GetLabels(), key=lambda l: stats.GetPhysicalSize(l), reverse=True)[:k]
    out = sitk.Image(bin_img.GetSize(), sitk.sitkUInt8); out.CopyInformation(bin_img)
    for l in labels:
        out = out | sitk.Equal(cc, l)
    return sitk.Cast(out, sitk.sitkUInt8)

def lung_mask_region_growing(
    img,
    seeds,
    lower=-950,
    upper=-500,
    closing_radius=2,
    keep_largest=2,
    fill_holes=True
):
    """
    Region-growing lung mask on a (resampled) CT volume.
    img: SimpleITK image (prefer HU-clipped/resampled)
    seeds: list of [x,y,z] indices
    """
    if not seeds:
        raise ValueError("No seeds provided for region growing.")

    seg = sitk.ConnectedThreshold(
        img,
        seedList=[tuple(map(int, s)) for s in seeds],
        lower=lower,
        upper=upper
    )

    # clean-up
    if closing_radius and closing_radius > 0:
        seg = sitk.BinaryMorphologicalClosing(seg, [closing_radius]*3)

    if fill_holes:
        seg = sitk.BinaryFillhole(seg, fullyConnected=True, foregroundValue=1)

    if keep_largest and keep_largest > 0:
        seg = _keep_largest_components(seg, k=keep_largest)

    return sitk.Cast(seg, sitk.sitkUInt8)
