# Sat-MVS-Dataset

A lightweight and flexible tool for generating samples from **US3D** and **MVS3D** datasets for satellite multi-view stereo (MVS) research.

## Changelog

#### 2025-07-18
- Released **MVS3D V2** dataset with improved data organization and standardized splits for unsupervised MVS.
    - **Training set:** Uses random selection within each region/block to enhance diversity and generalization.
    - **Test set:** Selects the best-scored 5-view group for each region to ensure fair and robust benchmarking.
    - **Download:** [Baidu Netdisk](https://pan.baidu.com/s/1bpO7IJB6-RMqYS78Z9GVEQ?pwd=muxr) (Extraction Code: `muxr`)
- This version supports robust, region-level unsupervised MVS training and evaluation in satellite imagery scenarios.

#### 2025-07-17
- Added **MVS3D V1 (US3D-MVS-V1)** dataset, available for multi-view unsupervised learning tasks.
- **Download:** [Baidu Netdisk](https://pan.baidu.com/s/12k7ZKAu9iuh9_JevbROCKg?pwd=x9ic) (Extraction Code: `x9ic`)

#### 2025-07-16
- Updated **SP-MVS** dataset links and instructions.
- Provided access to the original dataset used in SP-MVS paper.

**Download:** [Baidu Netdisk](https://pan.baidu.com/s/111IrueZ1UyQcpX7oEq5QyQ?pwd=pieb) (Extraction Code: `pieb`)

#### 2025-07-11
- Added support for **US3D-MVS-V1** dataset in Sat-MVS-Dataset.
- Users can now generate samples from US3D-MVS-V1 for MVS experiments seamlessly.

**Download:** [Baidu Netdisk](https://pan.baidu.com/s/1mlOl7mWtDJ9LJ6D6Kc73Ng?pwd=yc9t) (Extraction Code: `yc9t`)

---

## Citation
If you use Sat-MVS-Dataset in your research, please cite:

```bibtex
@misc{satmvstool2025,
  title = {Sat-MVS-Dataset: A Tool for Generating Samples from US3D and MVS3D},
  author = {Chen Liu},
  year = {2025},
  howpublished = {GitHub},
  url = {https://github.com/yourname/Sat-MVS-Dataset}
}
```

---

## Contact

If you have any questions or encounter issues:
- Open an issue on [GitHub Issues](https://github.com/yourname/Sat-MVS-Dataset/issues)
- Or contact: sweet8degree@gmail.com

---

Happy MVS research with Sat-MVS-Dataset! 🚀
