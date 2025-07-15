import os
import rasterio
from rasterio.transform import from_origin
from utm import utm_to_wgs84, wgs84_to_utm  # 使用你提供的精准转换模块

def read_txt(txt_path):
    with open(txt_path, 'r') as f:
        lines = f.readlines()
        easting = float(lines[0].strip())
        northing = float(lines[1].strip())
        size = int(float(lines[2].strip()))
        gsd = float(lines[3].strip())
    return easting, northing, size, gsd

def get_epsg_from_txt_info(easting, northing, zone_hint=None):
    """
    使用 txt 中中心点的 UTM 坐标反算 EPSG 编码
    """
    # 默认假设 zone letter 为北半球 N 区（大多数美国城市如此）
    lat, lon = utm_to_wgs84(easting, northing, zone_hint or 17, zone_letter='N')
    _, _, zone_number, _ = wgs84_to_utm(lat, lon)
    epsg = 32600 + zone_number if lat >= 0 else 32700 + zone_number
    return epsg

def add_geo_reference(dsm_path, txt_path, output_path):
    easting, northing, size, gsd = read_txt(txt_path)

    # 使用准确的方式计算 EPSG
    epsg = get_epsg_from_txt_info(easting + size * gsd / 2, northing + size * gsd / 2)

    with rasterio.open(dsm_path) as src:
        dsm = src.read(1)
        dtype = dsm.dtype
        height, width = dsm.shape

    transform = from_origin(easting, northing + size * gsd, gsd, gsd)

    with rasterio.open(
        output_path, 'w',
        driver='GTiff',
        height=height,
        width=width,
        count=1,
        dtype=dtype,
        crs=f"EPSG:{epsg}",
        transform=transform
    ) as dst:
        dst.write(dsm, 1)

    print(f"[✓] 成功处理：{output_path}  (EPSG:{epsg})")

def batch_process_all(base_folder):
    for subfolder in os.listdir(base_folder):
        dsm_dir = os.path.join(base_folder, subfolder, "DSM")
        if not os.path.isdir(dsm_dir):
            continue

        tif_list = [f for f in os.listdir(dsm_dir) if f.endswith("_DSM.tif") and "_geo" not in f]
        for tif_file in tif_list:
            base_name = tif_file.replace("_DSM.tif", "")
            tif_path = os.path.join(dsm_dir, tif_file)
            txt_path = os.path.join(dsm_dir, f"{base_name}_DSM.txt")
            out_path = os.path.join(dsm_dir, f"{base_name}_DSM_geo.tif")

            if not os.path.exists(txt_path):
                print(f"[×] 缺失 TXT：{txt_path}")
                continue

            try:
                add_geo_reference(tif_path, txt_path, out_path)
            except Exception as e:
                print(f"[×] 错误处理 {tif_path}：{e}")

if __name__ == "__main__":
    base_path = r"E:\Data\US3D\US3D-MVS\JAX"  # ← 改成你的根目录
    batch_process_all(base_path)
