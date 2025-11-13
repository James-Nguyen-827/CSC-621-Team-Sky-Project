# covid_ct/registration/rigid_mi.py
import SimpleITK as sitk

def rigid_mi(
    fixed,
    moving,
    sampling=0.2,
    iters=200,
    lr=1.0,
    shrink_factors=(4, 2, 1),
    smooth_sigmas=(2.0, 1.0, 0.0),
    fixed_mask=None,
    moving_mask=None,
):
    """
    Mutual-Information rigid (Euler3D) registration.
    Returns (warped_moving, final_transform).
    """
    # init transform (centered)
    init_tx = sitk.CenteredTransformInitializer(
        fixed, moving, sitk.Euler3DTransform(),
        sitk.CenteredTransformInitializerFilter.GEOMETRY
    )

    reg = sitk.ImageRegistrationMethod()
    reg.SetMetricAsMattesMutualInformation(32)
    reg.SetMetricSamplingStrategy(reg.RANDOM)
    reg.SetMetricSamplingPercentage(sampling)
    reg.SetInterpolator(sitk.sitkLinear)

    if fixed_mask is not None:
        reg.SetMetricFixedMask(fixed_mask)
    if moving_mask is not None:
        reg.SetMetricMovingMask(moving_mask)

    reg.SetInitialTransform(init_tx, inPlace=False)
    reg.SetOptimizerAsRegularStepGradientDescent(
        learningRate=lr,
        minStep=1e-4,
        numberOfIterations=iters,
        relaxationFactor=0.5
    )
    reg.SetOptimizerScalesFromPhysicalShift()

    # multires pyramid (another pyrmid here?, Its a pyramid scheme XD, nah what it does is it helps the optimizer focus on large structures first.
    #Aligns the overall anatomy (translation + rotation).
    #Needs its own pyramid because it works on the original, unaligned volumes.
    #Helps the optimizer avoid local minima (coarse alignment first).)
    reg.SetShrinkFactorsPerLevel(shrink_factors)
    reg.SetSmoothingSigmasPerLevel(smooth_sigmas)
    reg.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()

    final_tx = reg.Execute(fixed, moving)

    warped = sitk.Resample(
        moving, fixed, final_tx, sitk.sitkLinear, 0.0, moving.GetPixelID()
    )
    return warped, final_tx

def apply_transform(moving, reference, transform):
    """Resample moving onto reference using given transform."""
    return sitk.Resample(moving, reference, transform, sitk.sitkLinear, 0.0, moving.GetPixelID())
