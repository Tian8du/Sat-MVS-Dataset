# ------------------------------------------------------------------------------
# File: select_best_images.py
# Description: Select the optimal k satellite images from multi-view observations
#              based on convergence angle and time span.
#              Each folder named "image" under the dataset_root will be processed.
#
# Author: Chen Liu (Wuhan University)
# Date: 2025-7-19
# ------------------------------------------------------------------------------

import os
import re
from glob import glob
from datetime import datetime
from itertools import combinations
import json
import math

def get_unique_id(filename):
    """Extract unique ID from image or IMD filename"""
    base = os.path.basename(filename)
    match = re.search(r'(\d{12}_\d{2}_P\d{3})', base)
    if match:
        return match.group(1)
    match2 = re.search(r'(P1BS-\d{12}_\d{2}_P\d{3})', base)
    if match2:
        return match2.group(1)[5:]
    return None

def extract_imd_datetime(imd_path):
    """Extract firstLineTime from IMD file"""
    try:
        with open(imd_path, 'r') as f:
            for line in f:
                if 'firstLineTime' in line:
                    match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', line)
                    if match:
                        return datetime.strptime(match.group(1), "%Y-%m-%dT%H:%M:%S")
    except Exception as e:
        print(f"Error reading {imd_path}: {e}")
    return None

def extract_imd_angles(imd_path):
    """Extract satellite azimuth and elevation from IMD file"""
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
        print(f"❌ Error reading {imd_path}: {e}")
    return az, el

def compute_convergence_angle(az1, az2, el1, el2):
    """Compute convergence angle between two observation angles"""
    az1, az2 = math.radians(az1), math.radians(az2)
    el1, el2 = math.radians(el1), math.radians(el2)
    cos_d = math.sin(el1) * math.sin(el2) + math.cos(el1) * math.cos(el2) * math.cos(az1 - az2)
    return math.degrees(math.acos(min(max(cos_d, -1.0), 1.0)))

def save_selected_image_paths(image_infos, output_path):
    """Save selected image file names to a JSON file"""
    json_data = {
        "selected_images": [os.path.basename(info["image_path"]) for info in image_infos]
    }
    with open(output_path, "w") as f:
        json.dump(json_data, f, indent=4)
    print(f"Saved successfully: {output_path}")

def collect_images_in_one_folder(image_folder, metadata_root):
    """Read image and metadata pairs from a folder"""
    image_infos = []
    tif_files = sorted(glob(os.path.join(image_folder, '*.tif')))
    imd_dict = {}

    for imd_path in glob(os.path.join(metadata_root, "*.IMD")):
        uid = get_unique_id(imd_path)
        if uid:
            imd_dict[uid] = imd_path

    for tif_path in tif_files:
        uid = get_unique_id(tif_path)
        if not uid or uid not in imd_dict:
            print(f"⚠️ IMD not found for: {tif_path}")
            continue
        imd_path = imd_dict[uid]
        dt = extract_imd_datetime(imd_path)
        az, el = extract_imd_angles(imd_path)
        if dt is not None and az is not None and el is not None:
            image_infos.append({
                "image_path": tif_path,
                "imd_path": imd_path,
                "datetime": dt,
                "unique_id": uid,
                "az": az,
                "el": el
            })

    image_infos.sort(key=lambda x: x['datetime'])
    return image_infos

def group_score(group, target_angle=20.0, target_time_span=3.0):
    """
    Compute group score based on convergence angle and time span.

    Parameters:
        target_angle (float): ideal convergence angle (in degrees)
        target_time_span (float): ideal time span (in days)
    """
    times = [img['datetime'] for img in group]
    time_span = (max(times) - min(times)).total_seconds() / 86400.0
    angles = []
    k = len(group)
    for i in range(k):
        for j in range(i+1, k):
            ang = compute_convergence_angle(
                group[i]['az'], group[j]['az'],
                group[i]['el'], group[j]['el']
            )
            angles.append(ang)

    angle_penalty = sum(abs(a - target_angle) for a in angles)
    time_penalty = abs(time_span - target_time_span)
    score = angle_penalty + time_penalty
    return score, time_span, angles

def select_best_k_images(image_infos, k=3):
    """Select the best k images based on score"""
    if len(image_infos) <= k:
        return image_infos, 0.0, [], 0.0

    best_group = None
    best_score = float("inf")
    best_time_span = 0
    best_angles = []

    for group in combinations(image_infos, k):
        score, time_span, angles = group_score(group)
        if score < best_score:
            best_score = score
            best_group = group
            best_time_span = time_span
            best_angles = angles

    return best_group, best_score, best_angles, best_time_span

def process_image_folder(image_folder, metadata_root, k=3, output_name="selected_best.json"):
    """Process a single image folder and select best k images"""
    print(f"\n🔍 Processing: {image_folder}")
    infos = collect_images_in_one_folder(image_folder, metadata_root)

    if len(infos) < k:
        print(f"⚠️ Not enough images (required: {k}), skipping.")
        return

    selected, best_score, best_angles, best_time_span = select_best_k_images(infos, k=k)

    print(f"✅ Best {k} images selected (score = {best_score:.2f}, span = {best_time_span:.2f} days, angles = {best_angles}):")
    for item in selected:
        print(item)

    output_json = os.path.join(image_folder, output_name)
    save_selected_image_paths(selected, output_json)
    print(f"💾 JSON saved to: {output_json}")

def find_all_image_folders(dataset_root):
    """Find all subfolders named 'image' in the dataset root"""
    image_folders = []
    for root, dirs, files in os.walk(dataset_root):
        for d in dirs:
            if d.lower() == "image":
                image_folders.append(os.path.join(root, d))
    return image_folders

def process_all_image_folders(dataset_root, metadata_root, k=3):
    """Process all 'image' folders in dataset root"""
    image_folders = find_all_image_folders(dataset_root)
    print(f"\n🔎 Found {len(image_folders)} image folders")
    for image_folder in image_folders:
        try:
            process_image_folder(image_folder, metadata_root, k)
        except Exception as e:
            print(f"❌ Failed to process: {image_folder}")
            print(f"🚨 Error: {e}")

if __name__ == "__main__":
    dataset_root = r"H:\IARPA_MVS_DATASET\MVS3D"  # Root path of dataset
    metadata_root = r"H:\IARPA_MVS_DATASET\IMD_ALL"
    process_all_image_folders(dataset_root, metadata_root, k=5)
