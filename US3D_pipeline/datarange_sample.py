import os
import shutil
import json

def organize_selected_images(image_folder, out_root, group_name_prefix=""):
    json_path = os.path.join(image_folder, "selected_all_combinations.json")
    if not os.path.exists(json_path):
        print(f"❌ 找不到: {json_path}")
        return
    with open(json_path, "r") as f:
        all_combos = json.load(f)["all_combinations"]

    block_dir = os.path.dirname(image_folder)
    heightmap2_dir = os.path.join(block_dir, "heightmap2")
    dsm_dir = os.path.join(block_dir, "dsm")

    for idx, combo in enumerate(all_combos, 1):
        first_img = combo[0]
        region, block_id, _ = first_img.split('_')[0:3]
        group_name = f"{region}_{block_id}_{idx:03d}"
        group_dir = os.path.join(out_root, group_name)

        os.makedirs(os.path.join(group_dir, "image"), exist_ok=True)
        os.makedirs(os.path.join(group_dir, "rpc"), exist_ok=True)
        os.makedirs(os.path.join(group_dir, "height"), exist_ok=True)
        os.makedirs(os.path.join(group_dir, "DSM"), exist_ok=True)

        for img_file in combo:
            base_name = os.path.splitext(img_file)[0]

            # image
            src_img = os.path.join(image_folder, img_file)
            dst_img = os.path.join(group_dir, "image", img_file)
            if os.path.exists(src_img):
                if not os.path.exists(dst_img):
                    shutil.copy(src_img, dst_img)
                else:
                    print(f"✅ 已存在影像: {dst_img}")
            else:
                print(f"⚠️ 缺少影像: {img_file}")

            # rpc
            rpc_file = img_file.replace(".tif", ".rpc")
            src_rpc = os.path.join(image_folder, rpc_file)
            dst_rpc = os.path.join(group_dir, "rpc", rpc_file)
            if os.path.exists(src_rpc):
                if not os.path.exists(dst_rpc):
                    shutil.copy(src_rpc, dst_rpc)
                else:
                    print(f"✅ 已存在RPC: {dst_rpc}")
            else:
                print(f"⚠️ 缺少 RPC: {rpc_file}")

            # height
            height_file = base_name + "_heightmap.tif"
            src_height = os.path.join(heightmap2_dir, height_file)
            dst_height = os.path.join(group_dir, "height", height_file)
            if os.path.exists(src_height):
                if not os.path.exists(dst_height):
                    shutil.copy(src_height, dst_height)
                else:
                    print(f"✅ 已存在 Heightmap: {dst_height}")
            else:
                print(f"⚠️ 缺少 Heightmap: {height_file}")

        # DSM（每组一个）
        dsm_filename = f"{region}_{block_id}_DSM_geo.tif"
        dsm_src = os.path.join(dsm_dir, dsm_filename)
        dsm_dst = os.path.join(group_dir, "DSM", dsm_filename.replace("_geo",""))
        if os.path.exists(dsm_src):
            # if not os.path.exists(dsm_dst):
            shutil.copy(dsm_src, dsm_dst)
        #     else:
        #         print(f"✅ 已存在 DSM: {dsm_dst}")
        # else:
        #     print(f"⚠️ 缺少 DSM 文件: {dsm_filename}")

        print(f"✅ 已完成分组: {group_name}")




def batch_organize_all(dataset_root, out_root):
    for root, dirs, files in os.walk(dataset_root):
        if os.path.basename(root).lower() == "image":
            organize_selected_images(root, out_root)

# 用法示例
if __name__ == "__main__":
    dataset_root = r"H:\MVS-Dataset\Test2"
    out_root = r"H:\MVS-Dataset\US3D-MVS\Train"
    batch_organize_all(dataset_root, out_root)
