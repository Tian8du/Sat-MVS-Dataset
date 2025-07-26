import os
import re
import math
import json
from glob import glob
from datetime import datetime
from itertools import combinations
import random

def find_all_valid_groups(image_infos, k=3, angle_range=(5, 45), max_incidence=40):
    valid_groups = []
    for group in combinations(image_infos, k):
        passes = True
        for i in range(k):
            for j in range(i + 1, k):
                valid, _, _ = filter_and_score_pair(group[i], group[j], angle_range, max_incidence)
                if not valid:
                    passes = False
                    break
            if not passes:
                break
        if passes:
            valid_groups.append(group)
    return valid_groups

def parse_image_filename(filename):
    match = re.match(r"([A-Z]+)_(\d{3})_(\d{3})_RGB.tif", os.path.basename(filename))
    return match.groups() if match else (None, None, None)

def extract_imd_datetime(imd_path):
    try:
        with open(imd_path, 'r') as f:
            for line in f:
                if 'firstLineTime' in line:
                    match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', line)
                    if match:
                        return datetime.strptime(match.group(1), "%Y-%m-%dT%H:%M:%S")
    except: pass
    return None

def extract_imd_angles(imd_path):
    az, el = None, None
    try:
        with open(imd_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if 'meanSatAz' in line:
                    match = re.search(r"[-+]?[0-9]*\.?[0-9]+", line)
                    if match:
                        az = float(match.group())
                elif 'meanSatEl' in line:
                    match = re.search(r"[-+]?[0-9]*\.?[0-9]+", line)
                    if match:
                        el = float(match.group())
    except Exception as e:
        print(f"❌ 读取 {imd_path} 时出错: {e}")
    return az, el


def compute_convergence_angle(az1, az2, el1, el2):
    az1, az2 = math.radians(az1), math.radians(az2)
    el1, el2 = math.radians(el1), math.radians(el2)
    cos_d = math.sin(el1) * math.sin(el2) + math.cos(el1) * math.cos(el2) * math.cos(az1 - az2)
    return math.degrees(math.acos(min(max(cos_d, -1.0), 1.0)))


def filter_and_score_pair(img_a, img_b, angle_range=(5, 45), max_incidence=40):
    angle = compute_convergence_angle(img_a['az'], img_b['az'], img_a['el'], img_b['el'])

    # 修正后的“入射角”：90 - 卫星高度角
    inc_a = 90.0 - img_a['el']
    inc_b = 90.0 - img_b['el']
    max_inc = max(inc_a, inc_b)

    time_diff = abs((img_a['datetime'] - img_b['datetime']).total_seconds()) / 86400

    if angle_range[0] <= angle <= angle_range[1] and max_inc <= max_incidence:
        return True, time_diff, angle
    return False, None, None


def select_us3d_recommended_group(image_infos, k=3):
    if len(image_infos) < k:
        return image_infos, 0.0

    from itertools import combinations
    best_group, best_score = None, float('inf')

    for group in combinations(image_infos, k):
        passes = True
        angles, time_diffs = [], []
        for i in range(k):
            for j in range(i + 1, k):
                valid, t_diff, ang = filter_and_score_pair(group[i], group[j])
                if not valid:
                    passes = False
                    break
                time_diffs.append(t_diff)
                angles.append(ang)
            if not passes:
                break
        if not passes:
            continue

        score = sum(time_diffs) + sum(abs(a - 20.0) for a in angles)  # 20°是最优角度
        if score < best_score:
            best_score = score
            best_group = group

    return list(best_group) if best_group else [], best_score

def process_all_us3d_pairs_all_combinations(dataset_root, metadata_root, k=3, min_groups=100, max_groups=300, random_seed=42):
    random.seed(random_seed)
    for root, dirs, files in os.walk(dataset_root):
        if os.path.basename(root).lower() == 'image':
            out_json = os.path.join(root, 'selected_all_combinations.json')
            if os.path.exists(out_json):
                os.remove(out_json)
            tif_files = sorted(glob(os.path.join(root, '*.tif')))
            image_infos = []
            for tif_path in tif_files:
                region, dsm_id, img_id = parse_image_filename(tif_path)
                if region is None:
                    continue
                imd_path = os.path.join(metadata_root, region, f"{int(img_id):02d}.IMD")
                dt = extract_imd_datetime(imd_path)
                az, el = extract_imd_angles(imd_path)
                if None in (dt, az, el):
                    continue
                image_infos.append({
                    'image_path': tif_path,
                    'imd_path': imd_path,
                    'datetime': dt,
                    'az': az,
                    'el': el,
                })

            valid_groups = find_all_valid_groups(image_infos, k=k)
            # ---- 新增：去重（组合排序后hash判重）
            combo_set = set()
            unique_groups = []
            for group in valid_groups:
                key = tuple(sorted(os.path.basename(item['image_path']) for item in group))
                if key not in combo_set:
                    combo_set.add(key)
                    unique_groups.append(group)

            n_all = len(unique_groups)
            print(f"✅ {root} - 去重后可用{n_all}组k={k}影像组合")
            # ---- 随机采样
            if n_all > max_groups:
                unique_groups = random.sample(unique_groups, max_groups)
                print(f"🔹 超过{max_groups}组，随机采样{max_groups}组")
            elif n_all < min_groups:
                print(f"⚠️ 仅有{n_all}组，低于建议的{min_groups}组，全保留")
            # 保存
            all_combos = [
                [os.path.basename(item['image_path']) for item in group]
                for group in unique_groups
            ]
            with open(out_json, 'w') as f:
                json.dump({"all_combinations": all_combos}, f, indent=2)
            print(f"  ✉ 已保存{len(all_combos)}组到: {out_json}")


if __name__ == "__main__":
    dataset_root = r"H:\MVS-Dataset\Test"  # 数据集根目录
    metadata_root = r"H:\MVS-Dataset\Track3-Metadata"
    process_all_us3d_pairs_all_combinations(dataset_root, metadata_root, k=5)
