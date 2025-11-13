# covid_ct/segmentation/levelset.py
import SimpleITK as sitk

def lesion_levelset(
    img,
    init_mask,
    iterations=120,
    curvature=0.5,
    propagation=1.0,
    advection=1.0,
    edge_sigma=1.0,
    sigmoid_alpha=-10.0,
    sigmoid_beta=10.0,
    post_close=1
):
    """
    Refine an initial infection mask with Geodesic Active Contour (GAC).
    img:        preprocessed (clipped/normalized) 3D image (sitk.Image, float)
    init_mask:  binary mask (sitk.Image, 0/1) used to initialize the contour
    returns:    binary mask (UInt8)
    """
    # Edge map that attracts the contour to boundaries
    sm = sitk.CurvatureAnisotropicDiffusion(img, timeStep=0.0625, conductanceParameter=3.0, numberOfIterations=5)
    grad = sitk.GradientMagnitudeRecursiveGaussian(sm, edge_sigma)
    edge = sitk.Sigmoid(grad, sigmoid_alpha, sigmoid_beta, 0.0, 1.0)  # low at edges -> high attraction

    # Signed distance from init mask (positive inside)
    phi0 = sitk.SignedMaurerDistanceMap(
        sitk.Cast(init_mask > 0, sitk.sitkUInt8),
        insideIsPositive=True,
        useImageSpacing=True
    )

    gac = sitk.GeodesicActiveContourLevelSetImageFilter()
    gac.SetNumberOfIterations(iterations)
    gac.SetCurvatureScaling(curvature)
    gac.SetPropagationScaling(propagation)
    gac.SetAdvectionScaling(advection)
    out = gac.Execute(phi0, edge)

    seg = sitk.Cast(out > 0, sitk.sitkUInt8)

    # Light post-processing (ran in one try yay, no debugging needed)
    if post_close and post_close > 0:
        seg = sitk.BinaryMorphologicalClosing(seg, [post_close]*3)

    return seg
