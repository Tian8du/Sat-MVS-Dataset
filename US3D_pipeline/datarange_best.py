import os
import shutil
import json

def organize_single_selected_json(image_folder, out_root):
    """
    Organize image/RPC/height/DSM files into per-combination folders
    based on 'selected_best.json' which contains top N combinations.

    Args:
        image_folder (str): Path to the folder containing satellite images and JSON files.
        out_root (str): Output root directory for grouped combinations.
    """
    block_dir = os.path.dirname(image_folder)
    heightmap2_dir = os.path.join(block_dir, "heightmap2")
    dsm_dir = os.path.join(block_dir, "dsm")

    json_path = os.path.join(image_folder, "selected_best.json")
    if not os.path.exists(json_path):
        print(f"⚠️ No selected_best.json in {image_folder}, skipping.")
        return

    with open(json_path, "r") as f:
        data = json.load(f)

    top_groups = data.get("top_groups", [])
    if not top_groups:
        print(f"⚠️ Empty top_groups in {json_path}")
        return

    for idx, group in enumerate(top_groups):
        selected = group.get("images", [])
        if not selected:
            print(f"⚠️ Group {idx+1} in {json_path} is empty.")
            continue

        try:
            region, block_id, _ = selected[0].split('_')[0:3]
        except Exception:
            print(f"⚠️ Invalid filename format: {selected[0]}")
            continue

        group_name = f"{region}_{block_id}_{idx+1}"
        group_dir = os.path.join(out_root, group_name)

        img_dir = os.path.join(group_dir, "image")
        rpc_dir = os.path.join(group_dir, "rpc")
        height_dir = os.path.join(group_dir, "height")
        dsm_out_dir = os.path.join(group_dir, "DSM")

        os.makedirs(img_dir, exist_ok=True)
        os.makedirs(rpc_dir, exist_ok=True)
        os.makedirs(height_dir, exist_ok=True)
        os.makedirs(dsm_out_dir, exist_ok=True)

        for img_file in selected:
            # Copy image
            src_img = os.path.join(image_folder, img_file)
            dst_img = os.path.join(img_dir, img_file)
            if os.path.exists(src_img):
                if not os.path.exists(dst_img):
                    shutil.copy(src_img, dst_img)
                else:
                    print(f"⏩ Skip image (already exists): {dst_img}")
            else:
                print(f"⚠️ Missing image: {img_file}")

            # Copy RPC
            rpc_file = img_file.replace(".tif", ".rpc")
            src_rpc = os.path.join(image_folder, rpc_file)
            dst_rpc = os.path.join(rpc_dir, rpc_file)
            if os.path.exists(src_rpc):
                if not os.path.exists(dst_rpc):
                    shutil.copy(src_rpc, dst_rpc)
                else:
                    print(f"⏩ Skip RPC (already exists): {dst_rpc}")
            else:
                print(f"⚠️ Missing RPC: {rpc_file}")

            # Copy height map
            height_file = img_file.replace(".tif", "_heightmap.tif")
            src_height = os.path.join(heightmap2_dir, height_file)
            dst_height = os.path.join(height_dir, height_file)
            if os.path.exists(src_height):
                if not os.path.exists(dst_height):
                    shutil.copy(src_height, dst_height)
                else:
                    print(f"⏩ Skip heightmap (already exists): {dst_height}")
            else:
                print(f"⚠️ Missing heightmap: {height_file}")

        # Copy shared DSM
        dsm_file = f"{region}_{block_id}_DSM_geo.tif"
        dsm_src = os.path.join(dsm_dir, dsm_file)
        dsm_dst = os.path.join(dsm_out_dir, dsm_file)
        if os.path.exists(dsm_src):
            if not os.path.exists(dsm_dst):
                shutil.copy(dsm_src, dsm_dst)
            else:
                print(f"⏩ Skip DSM (already exists): {dsm_dst}")
        else:
            print(f"⚠️ Missing DSM file: {dsm_file}")

        print(f"✅ Group created: {group_name}")


def batch_organize_all_selected_json(dataset_root, out_root):
    """
    Recursively scan for image folders and process only 'selected_best.json'.
    """
    for root, dirs, files in os.walk(dataset_root):
        if os.path.basename(root).lower() == "image":
            organize_single_selected_json(root, out_root)


# 用法示例
if __name__ == "__main__":
    dataset_root = r"H:\MVS-Dataset\Test2"
    out_root = r"H:\MVS-Dataset\US3D-MVS\Test"
    batch_organize_all_selected_json(dataset_root, out_root)
