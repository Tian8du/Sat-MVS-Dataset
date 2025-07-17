import os
import glob
import rasterio
from rasterio.windows import Window

def split_dsm_with_overlap(dsm_path, output_dir, tile_size=768, overlap=128):
    """
    将DSM影像裁剪为指定tile大小的小块，可设置重叠像素，覆盖原图全部区域。
    文件命名方式为：原始DSM文件名_{tile_id:04d}.tif
    """
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(dsm_path))[0]

    with rasterio.open(dsm_path) as src:
        width = src.width
        height = src.height
        profile = src.profile
        step = tile_size - overlap
        tile_id = 0

        for top in range(0, height, step):
            for left in range(0, width, step):
                bottom = min(top + tile_size, height)
                right = min(left + tile_size, width)

                # 防止最后一块不足tile_size
                if bottom - top < tile_size:
                    top = max(0, bottom - tile_size)
                if right - left < tile_size:
                    left = max(0, right - tile_size)

                window = Window(left, top, tile_size, tile_size)
                transform = src.window_transform(window)
                dsm_patch = src.read(1, window=window)

                tile_profile = profile.copy()
                tile_profile.update({
                    "height": tile_size,
                    "width": tile_size,
                    "transform": transform,
                })

                out_path = os.path.join(output_dir, f"{base_name}_{tile_id:04d}.tif")
                with rasterio.open(out_path, "w", **tile_profile) as dst:
                    dst.write(dsm_patch, 1)

                print(f"✅ Saved {out_path}")
                tile_id += 1

    print(f"\n🎯 Finished! Total {tile_id} patches saved to: {output_dir}")

def batch_split_all_dsms(dsm_dir, out_root, tile_size=1024, overlap=128):
    tif_files = glob.glob(os.path.join(dsm_dir, "*.tif"))
    for tif_path in tif_files:
        base = os.path.splitext(os.path.basename(tif_path))[0]
        output_dir = os.path.join(out_root, base + "_tiles")
        split_dsm_with_overlap(tif_path, output_dir, tile_size, overlap)

if __name__ == "__main__":
    dsm_dir = r"H:\IARPA_MVS_DATASET\Challenge_Data_and_Software\Lidar_gt"
    out_root = r"H:\IARPA_MVS_DATASET\Challenge_Data_and_Software\Lidar_gt\tiles"
    batch_split_all_dsms(dsm_dir, out_root, tile_size=768, overlap=128)
