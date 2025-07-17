import os
from glob import glob
import rasterio
from PIL import Image
from pyproj import Transformer
from tools.RPCCore import RPCModelParameter
import re
import os

def parse_img_for_final_name(filename, dsm_name):
    base = os.path.splitext(os.path.basename(filename))[0]

    # 采集时间
    m_time = re.search(r'_(\d{2}[A-Z]{3}\d{2})WV03', base)
    if m_time:
        date_str = m_time.group(1)
        date_map = {'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04',
                    'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
                    'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'}
        date8 = f"20{date_str[-2:]}{date_map[date_str[2:5]]}{date_str[0:2]}"
    else:
        date8 = "unknown"

    # 视角
    m_view = re.search(r'_P(\d{3})_', base)
    view = f"P{m_view.group(1)}" if m_view else "PXXX"

    # 拼接
    out_img_name = f"{dsm_name}_{date8}_{view}.tif"
    out_rpc_name = f"{dsm_name}_{date8}_{view}_rpc.txt"
    return out_img_name, out_rpc_name



dsm_tile_dir = r"H:\IARPA_MVS_DATASET\Challenge_Data_and_Software\Lidar_gt\tiles\MasterSequesteredPark_tiles"      # DSM tile 路径
image_dir = r"H:\IARPA_MVS_DATASET\Challenge_Data_and_Software\cropimagedata\MasterSequesteredPark\MasterSequesteredPark"               # 影像及rpc目录
output_root = r"H:\IARPA_MVS_DATASET\MVS3D"           # 最终输出根目录
os.makedirs(output_root, exist_ok=True)

# 获取所有DSM块
dsm_tiles = [f for f in glob(os.path.join(dsm_tile_dir, "*.tif"))]

# 获取所有原始影像
image_files = [f for f in glob(os.path.join(image_dir, "*.tif")) if "DSM" not in os.path.basename(f)]

for dsm_tile in dsm_tiles:
    dsm_name = os.path.splitext(os.path.basename(dsm_tile))[0]
    out_img_dir = os.path.join(output_root, dsm_name, "image")
    out_rpc_dir = os.path.join(output_root, dsm_name, "rpc")
    os.makedirs(out_img_dir, exist_ok=True)
    os.makedirs(out_rpc_dir, exist_ok=True)

    with rasterio.open(dsm_tile) as src:
        width = src.width
        height = src.height
        center_row = height // 2
        center_col = width // 2
        x_proj, y_proj = src.xy(center_row, center_col)
        transformer = Transformer.from_crs(src.crs, "EPSG:4326", always_xy=True)
        lon, lat = transformer.transform(x_proj, y_proj)
        band1 = src.read(1)
        center_height = band1[center_row, center_col]

    for image_path in image_files:
        base = os.path.splitext(os.path.basename(image_path))[0]
        rpc_path = os.path.join(image_dir, base + "_ba_rpc.txt")
        if not os.path.exists(rpc_path):
            print("❌ 缺失rpc:", rpc_path)
            continue
        # 投影中心
        rpc_model = RPCModelParameter()
        rpc_model.load_from_file(rpc_path)
        x, y = rpc_model.RPC_OBJ2PHOTO([lat], [lon], [center_height])
        x, y = float(x[0]), float(y[0])

        # 裁剪影像
        img = Image.open(image_path)
        size = width  # DSM块宽高
        x = int(round(x))
        y = int(round(y))
        left = max(0, x - size // 2)
        top = max(0, y - size // 2)
        right = min(img.width, left + size)
        bottom = min(img.height, top + size)
        # 调整以防贴边
        if right - left < size:
            left = max(0, right - size)
        if bottom - top < size:
            top = max(0, bottom - size)
        crop = img.crop((left, top, right, bottom))
        out_img_name, out_rpc_name = parse_img_for_final_name(image_path, dsm_name)

        crop.save(os.path.join(out_img_dir, out_img_name))

        # 更新rpc
        rpc_model.LINE_OFF -= top
        rpc_model.SAMP_OFF -= left
        rpc_model.save_dirpc_to_file(os.path.join(out_rpc_dir, out_rpc_name))

        print(f"✅ {dsm_name} - {out_img_name}")

print("🎯全部完成！每个DSM块分文件夹，image/rpc分类。")
