# Dataset Splitting Utility

This utility splits your raw dataset (`dataset/real` and `dataset/fake`) into Train, Validation, and Test sets.

## Overview
- **Source**: `dataset/`
- **Output**: `dataset_split/`
- **Ratio**: 70% Train, 15% Validation, 15% Test
- **Renaming**: Files are renamed as `class_split_xxxx.jpg` (e.g., `real_train_0001.jpg`).
- **Tracking**: Generates `split.csv` and `split_summary.json`.

## Usage
Run the following command:

```bash
python split_dataset.py
```

### Options
- `--source`: Source directory (default: `dataset`)
- `--output`: Output directory (default: `dataset_split`)
- `--seed`: Random seed for reproducibility (default: `42`)

## Output Structure
```
dataset_split/
├── train/
│   ├── real/
│   └── fake/
├── val/
│   ├── real/
│   └── fake/
├── test/
│   ├── real/
│   └── fake/
├── split.csv           # List of all files with their split assignment
└── split_summary.json  # Count of images in each split
```
