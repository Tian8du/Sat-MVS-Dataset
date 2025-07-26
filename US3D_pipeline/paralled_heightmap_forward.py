import os
import sys
import glob
import numpy as np
import rasterio
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm

# 添加你的 RPCCore 路径
from RPCCore import RPCModelParameter


def dsm_to_image_projection_single(args):
    dsm_path, image_path, output_path = args
    try:
        with rasterio.open(dsm_path) as dsm_src:
            dsm = dsm_src.read(1)
            dsm_transform = dsm_src.transform
            dsm_nodata = dsm_src.nodata  # 👈 读取无效值
            rows, cols = dsm.shape

        with rasterio.open(image_path) as img_src:
            img_width, img_height = img_src.width, img_src.height
            img_profile = img_src.profile
            rpc_file = image_path.replace(".tif", ".rpc")
            rpc = RPCModelParameter()
            rpc.load_dirpc_from_file(rpc_file)

        height_map = np.full((img_height, img_width), -9999, dtype=np.float32)

        for row_dsm in range(rows):
            for col_dsm in range(cols):
                h = dsm[row_dsm, col_dsm]

                # 👇 增加健壮的无效值检查
                if (not np.isfinite(h)) or (dsm_nodata is not None and abs(h - dsm_nodata) < 1e-4):
                    continue

                lon, lat = dsm_transform * (col_dsm + 0.5, row_dsm + 0.5)
                try:
                    col_img, row_img = rpc.RPC_OBJ2PHOTO(lat, lon, h)
                    col_img = int(round(col_img[0]))
                    row_img = int(round(row_img[0]))
                    if 0 <= col_img < img_width and 0 <= row_img < img_height:
                        height_map[row_img, col_img] = h
                except:
                    continue

        img_profile.update(dtype=rasterio.float32, count=1, nodata=-9999)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with rasterio.open(output_path, "w", **img_profile) as dst:
            dst.write(height_map, 1)

        return f"[✓] Saved: {output_path}"
    except Exception as e:
        return f"[✗] Failed: {image_path} - {e}"


def batch_generate_height_maps_parallel(dataset_root, max_workers=8):
    image_paths = glob.glob(os.path.join(dataset_root, "*", "image", "*.tif"))
    tasks = []

    for image_path in image_paths:
        image_dir = os.path.dirname(image_path)
        base_name = os.path.basename(image_path).replace(".tif", "")
        block_dir = os.path.abspath(os.path.join(image_dir, ".."))
        dsm_path = os.path.join(block_dir, "DSM", f"{base_name[:7]}_DSM_wgs84.tif")
        output_path = os.path.join(block_dir, "heightmap2", f"{base_name}_heightmap.tif")

        if not os.path.exists(dsm_path):
            continue

        tasks.append((dsm_path, image_path, output_path))

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        for result in tqdm(executor.map(dsm_to_image_projection_single, tasks), total=len(tasks), desc="Generating"):
            print(result)

    print("\n🎉 All height maps generated with multiprocessing.\n")


if __name__ == "__main__":
    dataset_root = r"H:\MVS-Dataset\Test2\OMA"
    batch_generate_height_maps_parallel(dataset_root, max_workers=8)
