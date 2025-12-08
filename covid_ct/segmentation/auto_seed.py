# covid_ct/segmentation/auto_seed.py
import SimpleITK as sitk

def _to_idx(img, phys_pt):
    return list(img.TransformPhysicalPointToIndex(phys_pt))

def _clamp_idx(img, idx):
    sz = img.GetSize()
    return [max(0, min(idx[i], sz[i]-1)) for i in range(3)]

def auto_lung_seeds(img, air_hu=-700, min_cc_vox=1500):
    """
    Return two [x,y,z] seeds roughly centered in left/right lungs.
    img:      3D CT image in HU (or HU-clipped), preferably resampled isotropic
    air_hu:   threshold upper bound for 'air' (lungs ~ -950..-500 HU)
    min_cc_vox: min size (voxels) to keep CCs
    """
    # 1) Air-ish mask
    air = sitk.BinaryThreshold(img, lowerThreshold=-1000, upperThreshold=air_hu)

    # 2) Clean up & keep large components
    air = sitk.BinaryMorphologicalClosing(air, [2,2,2])
    air = sitk.BinaryFillhole(air, True, 2)
    cc = sitk.ConnectedComponent(air)
    stats = sitk.LabelShapeStatisticsImageFilter(); stats.Execute(cc)

    # Keep components above size threshold (Why was this not working?)
    keep = [l for l in stats.GetLabels() if stats.GetNumberOfPixels(l) >= min_cc_vox]
    if not keep:
        # fallback: relax threshold, try again
        air = sitk.BinaryThreshold(img, -1000, -600)
        cc = sitk.ConnectedComponent(air); stats.Execute(cc)
        keep = stats.GetLabels()

    # Sort by size, largest first
    keep = sorted(keep, key=lambda l: stats.GetNumberOfPixels(l), reverse=True)

    seeds = []
    if len(keep) >= 2:
        # 3) Two largest CCs → centroids
        for l in keep[:2]:
            seeds.append(_clamp_idx(img, _to_idx(img, stats.GetCentroid(l))))
    elif len(keep) == 1:
        # 4) One big blob: split by mid-sagittal plane using bounding box
        l = keep[0]
        # centroid-based split heuristic
        cx, cy, cz = stats.GetCentroid(l)
        idx_c = _clamp_idx(img, _to_idx(img, (cx, cy, cz)))
        # offset left/right in index space
        seeds.append([max(idx_c[0]-20,0), idx_c[1], idx_c[2]])
        seeds.append([min(idx_c[0]+20, img.GetSize()[0]-1), idx_c[1], idx_c[2]])
    else:
        # 5) Absolute fallback: middle of volume, left/right offsets (here lie the errors, fixed it now, passed the wrong variable, was img instead of sz)
        sz = img.GetSize()
        mid = [sz[0]//2, sz[1]//2, sz[2]//2]
        seeds = [[max(mid[0]-25,0), mid[1], mid[2]],
                 [min(mid[0]+25, sz[0]-1), mid[1], mid[2]]]

    return [list(map(int, s)) for s in seeds]

# --- manual seeding helpers (append to auto_seed.py) ---
import matplotlib.pyplot as plt

def _pick_clicks_on_slice(img, z_index, num_points=2, title="Click inside each lung, then close"):
    """Show one axial slice and collect N mouse clicks (x,y)."""
    arr = sitk.GetArrayFromImage(img)  # [z,y,x]
    z_index = max(0, min(z_index, arr.shape[0]-1))
    sl = arr[z_index, :, :]

    plt.figure(figsize=(6,6))
    plt.imshow(sl, cmap="gray")
    plt.title(title)
    plt.axis("off")
    pts = plt.ginput(num_points, timeout=0)  # returns [(x,y), ...]
    plt.close()

    # convert to index [x,y,z]
    seeds = [[int(x), int(y), int(z_index)] for (x, y) in pts]
    return seeds

def manual_lung_seeds(img, num_points=2, z=None):
    """
    Pick seeds manually on an axial slice.
    - img: SimpleITK image (preferably preprocessed/resampled)
    - num_points: how many seeds to collect (2 = typical: left/right)
    - z: which axial slice (None -> middle)
    Returns: list[[x,y,z], ...]
    """
    if z is None:
        z = img.GetSize()[2] // 2
    seeds = _pick_clicks_on_slice(img, z, num_points=num_points)
    if not seeds:
        # fallback to center-left/right so the pipeline still runs
        sz = img.GetSize()
        mid = [sz[0]//2, sz[1]//2, z]
        seeds = [[max(mid[0]-25,0), mid[1], mid[2]],
                 [min(mid[0]+25, sz[0]-1), mid[1], mid[2]]]
    return seeds
