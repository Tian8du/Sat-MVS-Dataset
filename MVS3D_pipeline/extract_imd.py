# ---------------------------------------------------------------
# Script for Extracting IMD Files from the Original MVS3D Dataset
# and Centralizing Them for Satellite Image Metadata Parsing.
#
# Purpose:
#   - Extract .imd metadata files from the original MVS3D dataset
#   - Prepare for retrieving imaging time, intersection angle, etc.
#
# Author: Chen Liu, Wuhan University
# Contact: sweetdegree@gmail.com
# ---------------------------------------------------------------

import os
import tarfile
import shutil

# Set the root directory where your data is located
root_dir = r"H:\IARPA_MVS_DATASET\WV3\PAN"

# Step 1: Extract all .tar files in the root_dir and its subdirectories
for dirpath, dirnames, filenames in os.walk(root_dir):
    for fname in filenames:
        if fname.lower().endswith('.tar'):
            tar_path = os.path.join(dirpath, fname)
            # Extract to a folder with the same name as the .tar file (without extension)
            extract_dir = os.path.splitext(tar_path)[0]
            if not os.path.exists(extract_dir):
                os.makedirs(extract_dir)
            print(f"Extracting: {tar_path} -> {extract_dir}")
            with tarfile.open(tar_path) as tar:
                tar.extractall(path=extract_dir)

# Step 2: Search for all IMD files after extraction
imd_list = []

for dirpath, dirnames, filenames in os.walk(root_dir):
    for fname in filenames:
        if fname.lower().endswith('.imd'):
            imd_list.append(os.path.join(dirpath, fname))

print(f"Found {len(imd_list)} IMD files in total.")
for path in imd_list:
    print(path)

# Step 3: Copy all IMD files to a single output folder, renaming to avoid duplicate names
root_dir = r"H:\IARPA_MVS_DATASET\WV3\PAN"
out_dir = r"H:\IMD_ALL"
os.makedirs(out_dir, exist_ok=True)

for dirpath, dirnames, filenames in os.walk(root_dir):
    for fname in filenames:
        if fname.lower().endswith('.imd'):
            in_path = os.path.join(dirpath, fname)
            # Rename using the parent folder name to avoid duplication
            new_name = f"{os.path.basename(dirpath)}_{fname}"
            out_path = os.path.join(out_dir, new_name)
            shutil.copy2(in_path, out_path)
            print(f"Copied {in_path} -> {out_path}")
