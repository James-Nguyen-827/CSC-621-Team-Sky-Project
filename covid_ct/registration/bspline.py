# covid_ct/registration/bspline.py (what even is B-spline?, wait update it was taught in school today)
import SimpleITK as sitk

def bspline_deformable(
    fixed,
    moving,
    grid=(8, 8, 8),
    iters=100,
    shrink_factors=(4, 2, 1),
    smooth_sigmas=(2.0, 1.0, 0.0),
    initial_transform=None,
    fixed_mask=None,
    moving_mask=None,
):
    """
    Deformable B-spline registration.
    Returns (warped_moving, final_transform).
    """
    # Initialize B-spline transform over fixed image domain
    bspline_tx = sitk.BSplineTransformInitializer(
        image1=fixed,
        transformDomainMeshSize=grid,
        order=3
    )

    # Optionally compose with a prior (e.g., rigid)
    if initial_transform is not None:
        composite = sitk.Transform(initial_transform)
        composite.AddTransform(bspline_tx)
        tx = composite
    else:
        tx = bspline_tx

    reg = sitk.ImageRegistrationMethod()
    reg.SetMetricAsMattesMutualInformation(32)
    reg.SetInterpolator(sitk.sitkLinear)

    if fixed_mask is not None:
        reg.SetMetricFixedMask(fixed_mask)
    if moving_mask is not None:
        reg.SetMetricMovingMask(moving_mask)

    reg.SetInitialTransform(tx, inPlace=False)

    # LBFGSB is stable for B-spline; or use gradient descent if preferred (Limited-memory Broyden–Fletcher–Goldfarb–Shanno with Bound constraints, L-BFGS-B, why because I can, no seriously it is good for large parameter spaces)
    reg.SetOptimizerAsLBFGSB(
        gradientConvergenceTolerance=1e-5,
        numberOfIterations=iters,
        maximumNumberOfCorrections=25
    )

    # Multires pyramid (pyramidception XD, no the reason this is here is because:)
    #Starts after the rigid stage — so the images are roughly aligned.
    #Refines the fit by warping local regions (deformable registration).
    #Needs a separate pyramid because:
    #Its optimizer and parameters are completely different (many local control points).
    #It benefits from a new coarse→fine approach on the already roughly aligned images. Not redundant at all. Do not remove.
    reg.SetShrinkFactorsPerLevel(shrink_factors)
    reg.SetSmoothingSigmasPerLevel(smooth_sigmas)
    reg.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()

    final_tx = reg.Execute(fixed, moving)

    warped = sitk.Resample(
        moving, fixed, final_tx, sitk.sitkLinear, 0.0, moving.GetPixelID()
    )
    return warped, final_tx


def apply_transform(moving, reference, transform):
    return sitk.Resample(
        moving, reference, transform, sitk.sitkLinear, 0.0, moving.GetPixelID()
    )
