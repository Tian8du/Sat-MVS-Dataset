import os
import re
import math
import json
from glob import glob
from datetime import datetime
from itertools import combinations

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
    except:
        pass
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

def filter_and_score_pair(img_a, img_b, angle_range=(5, 45), max_incidence=35, max_time_diff_days=90, min_elevation=35):
    if img_a['el'] < min_elevation or img_b['el'] < min_elevation:
        return False, None, None
    angle = compute_convergence_angle(img_a['az'], img_b['az'], img_a['el'], img_b['el'])
    inc_a = 90.0 - img_a['el']
    inc_b = 90.0 - img_b['el']
    max_inc = max(inc_a, inc_b)
    time_diff = abs((img_a['datetime'] - img_b['datetime']).total_seconds()) / 86400
    if angle_range[0] <= angle <= angle_range[1] and max_inc <= max_incidence and time_diff <= max_time_diff_days:
        return True, time_diff, angle
    return False, None, None

def score_group(group, ideal_angle=20.0):
    # 评分标准：时间跨度+偏离理想基线角度之和
    times = [item['datetime'] for item in group]
    min_time = min(times)
    max_time = max(times)
    time_span = (max_time - min_time).total_seconds() / 86400.0

    angles = []
    for i in range(len(group)):
        for j in range(i+1, len(group)):
            ang = compute_convergence_angle(group[i]['az'], group[j]['az'], group[i]['el'], group[j]['el'])
            angles.append(ang)
    avg_angle = sum(angles) / len(angles) if angles else 0
    angle_penalty = sum(abs(ang - ideal_angle) for ang in angles) / len(angles) if angles else 0

    # 可根据实际需求调整权重
    score = time_span + angle_penalty
    return score, time_span, avg_angle

import os
import json
from glob import glob
from itertools import combinations

def process_all_best_group(dataset_root, metadata_root, k=5, n=3):
    for root, dirs, files in os.walk(dataset_root):
        if os.path.basename(root).lower() == 'image':
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

            if len(image_infos) < k:
                print(f"⚠️ {root}: 影像不足{k}张，跳过")
                continue

            all_valid_groups = []
            for group in combinations(image_infos, k):
                valid = all(
                    filter_and_score_pair(group[i], group[j])[0]
                    for i in range(k) for j in range(i+1, k)
                )
                if not valid:
                    continue
                score, time_span, avg_angle = score_group(group)
                all_valid_groups.append({
                    "images": [os.path.basename(i['image_path']) for i in group],
                    "score": score,
                    "time_span": time_span,
                    "avg_angle": avg_angle
                })

            if not all_valid_groups:
                print(f"❌ {root} - 没有找到合法组合")
                continue

            # 按得分升序排序，选取前n组
            top_n_groups = sorted(all_valid_groups, key=lambda x: x["score"])[:n]
            print(f"📊 {root} - 合法组合总数: {len(all_valid_groups)}")

            # 删除旧文件
            out_json = os.path.join(root, 'selected_best.json')
            if os.path.exists(out_json):
                os.remove(out_json)

            # 保存为新文件
            with open(out_json, 'w') as f:
                json.dump({"top_groups": top_n_groups}, f, indent=2)

            print(f"✅ {root} - 最优前{n}组已保存: {out_json}")
            for idx, g in enumerate(top_n_groups):
                print(f"  [{idx+1}] score={g['score']:.2f}, avg_angle={g['avg_angle']:.2f}, time_span={g['time_span']:.1f}天")

if __name__ == "__main__":
    dataset_root = r"H:\MVS-Dataset\Test2"
    metadata_root = r"H:\MVS-Dataset\Track3-Metadata"
    process_all_best_group(dataset_root, metadata_root, k=5, n=10)
