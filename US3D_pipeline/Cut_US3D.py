import os
import glob
import rasterio
from rpcm.rpc_model import RPCModel
from rasterio.windows import Window
from tqdm import tqdm

def crop_center_and_update_rpc(image_path, crop_size=768, overwrite=True):
    """
    Crop the central region of a GeoTIFF image and update the associated RPC model accordingly.

    Args:
        image_path (str): Path to the input GeoTIFF image.
        crop_size (int): Size (in pixels) of the square crop (default: 768).
        overwrite (bool): Whether to overwrite the original file (True) or save a new one (False).

    Notes:
        - The function assumes that the image has embedded RPC metadata.
        - It updates the row_offset and col_offset fields of the RPC model to account for cropping.
    """
    try:
        # Open the original GeoTIFF image
        with rasterio.open(image_path) as src:
            width, height = src.width, src.height
            center_x, center_y = width // 2, height // 2
            half = crop_size // 2
            left, top = center_x - half, center_y - half

            # Define the cropping window centered in the image
            window = Window(left, top, crop_size, crop_size)
            profile = src.profile.copy()
            profile.update({
                "width": crop_size,
                "height": crop_size,
            })
            # Remove transform and CRS to avoid mismatch when writing cropped image
            profile.pop("transform", None)
            profile.pop("crs", None)

            # Read the cropped image patch
            image_crop = src.read(window=window)

            # Extract and update RPC metadata
            raw_rpc = src.tags(ns="RPC")
            rpc = RPCModel(raw_rpc)
            rpc.row_offset -= top
            rpc.col_offset -= left

        # Determine output file path
        if overwrite:
            output_path = image_path
        else:
            dirname = os.path.dirname(image_path)
            basename = os.path.splitext(os.path.basename(image_path))[0]
            output_name = f"{basename}_crop{crop_size}.tif"
            output_path = os.path.join(dirname, output_name)

        # Write the cropped image and updated RPC to disk
        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(image_crop)
            dst.update_tags(ns="RPC", **rpc.to_geotiff_dict())

        tqdm.write(f"[✓] RPC updated: {os.path.basename(output_path):<40} size: {crop_size}×{crop_size}")

    except Exception as e:
        tqdm.write(f"[✗] Failed on {os.path.basename(image_path)}: {str(e)}")

def process_ud3d_dataset(root_dir, crop_size=768, overwrite=False):
    """
    Batch process a dataset to crop and update RPCs for all GeoTIFF images.

    Args:
        root_dir (str): Root directory of the dataset.
        crop_size (int): Desired crop size for all images.
        overwrite (bool): Whether to overwrite original images or create new cropped copies.

    Notes:
        - Searches recursively under `root_dir` for TIFF images in `*/image/*.tif` format.
        - Skips files that already contain "_crop" in their name.
    """
    search_pattern = os.path.join(root_dir, "*", "*", "image", "*.tif")

    # Collect original images (excluding previously cropped ones)
    tif_list = sorted([
        f for f in glob.glob(search_pattern, recursive=True)
        if "_crop" not in os.path.basename(f)
    ])

    print(f"\n📦 Found {len(tif_list)} original tif files. Starting RPC update... (overwrite={overwrite})\n")

    for tif_path in tqdm(tif_list, desc="Processing Images"):
        crop_center_and_update_rpc(tif_path, crop_size=crop_size, overwrite=overwrite)

    print("\n🎉 All processing complete.\n")

if __name__ == "__main__":
    # === Configuration ===
    dataset_root = r"C:\Users\Liuchen\Desktop\Test"  # Path to dataset root directory
    crop_size = 768                                  # Crop size in pixels (e.g., 768x768)
    overwrite = True                                  # Whether to overwrite original images

    process_ud3d_dataset(dataset_root, crop_size=crop_size, overwrite=overwrite)
