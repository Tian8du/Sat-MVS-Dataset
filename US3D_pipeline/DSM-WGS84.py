import os
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import calculate_default_transform, reproject, Resampling
from utm import utm_to_wgs84, wgs84_to_utm  # pip install utm
# Note: JAX 17, OMA 15 (project-specific note)

def read_txt(txt_path):
    with open(txt_path, 'r') as f:
        lines = f.readlines()
        easting = float(lines[0].strip())
        northing = float(lines[1].strip())
        size = int(float(lines[2].strip()))
        gsd = float(lines[3].strip())
    return easting, northing, size, gsd

def get_epsg_from_txt_info(easting, northing, zone_hint=None):
    # Convert UTM to WGS84 to determine correct zone and hemisphere
    lat, lon = utm_to_wgs84(easting, northing, zone_hint or 15, zone_letter='N')
    _, _, zone_number, _ = wgs84_to_utm(lat, lon)
    epsg = 32600 + zone_number if lat >= 0 else 32700 + zone_number
    return epsg

def add_geo_reference(dsm_path, txt_path, output_path):
    easting, northing, size, gsd = read_txt(txt_path)
    # Use the center point to determine EPSG
    epsg = get_epsg_from_txt_info(easting + size * gsd / 2, northing + size * gsd / 2)

    with rasterio.open(dsm_path) as src:
        dsm = src.read(1)
        dtype = dsm.dtype
        height, width = dsm.shape

    # Create UTM affine transform from top-left origin
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

    print(f"[✓] UTM geo-reference added: {output_path} (EPSG:{epsg})")

def reproject_to_wgs84(input_path, output_path, nodata_value=-9999):
    with rasterio.open(input_path) as src:
        dst_crs = 'EPSG:4326'
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds
        )

        kwargs = src.meta.copy()
        kwargs.update({
            'crs': dst_crs,
            'transform': transform,
            'width': width,
            'height': height,
            'nodata': nodata_value,
            'dtype': rasterio.float32  # Use float32 to avoid precision issues with integer nodata
        })

        with rasterio.open(output_path, 'w', **kwargs) as dst:
            reproject(
                source=rasterio.band(src, 1),
                destination=rasterio.band(dst, 1),
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=transform,
                dst_crs=dst_crs,
                src_nodata=src.nodata,           # Clearly define source nodata
                dst_nodata=nodata_value,         # Clearly define destination nodata
                resampling=Resampling.bilinear
            )

    print(f"[✓] Reprojected to WGS84: {output_path} (nodata={nodata_value})")

def batch_process_all(base_folder, keep_utm_geo=False):
    for subfolder in os.listdir(base_folder):
        dsm_dir = os.path.join(base_folder, subfolder, "DSM")
        if not os.path.isdir(dsm_dir):
            continue

        # Filter DSM files that have not yet been geo-referenced
        tif_list = [f for f in os.listdir(dsm_dir) if f.endswith("_DSM.tif") and "_geo" not in f and "_wgs84" not in f]

        for tif_file in tif_list:
            base_name = tif_file.replace("_DSM.tif", "")
            tif_path = os.path.join(dsm_dir, tif_file)
            txt_path = os.path.join(dsm_dir, f"{base_name}_DSM.txt")
            geo_path = os.path.join(dsm_dir, f"{base_name}_DSM_geo.tif")
            wgs84_path = os.path.join(dsm_dir, f"{base_name}_DSM_wgs84.tif")

            if not os.path.exists(txt_path):
                print(f"[×] Missing TXT file: {txt_path}")
                continue
            try:
                # 1. Add UTM geo-reference
                add_geo_reference(tif_path, txt_path, geo_path)
                # 2. Reproject to WGS84
                reproject_to_wgs84(geo_path, wgs84_path)

                if not keep_utm_geo:
                    os.remove(geo_path)
                    print(f"[–] Deleted intermediate file: {geo_path}")
            except Exception as e:
                print(f"[×] Error processing {tif_file}: {e}")

if __name__ == "__main__":
    # Modify to your own dataset root path
    base_path = r"H:\MVS-Dataset\Test\JAX"
    # Set whether to keep intermediate UTM GeoTIFF files
    KEEP_UTM_GEO = True
    batch_process_all(base_path, keep_utm_geo=KEEP_UTM_GEO)
