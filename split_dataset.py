import os
import shutil
import random
import pandas as pd
import json
import argparse
from math import floor

def get_image_paths(directory):
    valid_exts = {'.png', '.jpg', '.jpeg'}
    image_paths = []
    for root, _, files in os.walk(directory):
        for file in files:
            if os.path.splitext(file)[1].lower() in valid_exts:
                image_paths.append(os.path.join(root, file))
    return image_paths

def split_dataset(source_dir, output_dir, seed=42, split_ratio=(0.7, 0.15, 0.15)):
    random.seed(seed)
    
    # Define classes and paths
    classes = {'real': 0, 'fake': 1}
    source_real = os.path.join(source_dir, 'real')
    source_fake = os.path.join(source_dir, 'fake')
    
    # Check inputs
    if not os.path.exists(source_real) or not os.path.exists(source_fake):
        print(f"Error: Source directories not found in {source_dir}")
        return

    # Create output structure
    subsets = ['train', 'val', 'test']
    for subset in subsets:
        for cls_name in classes:
            os.makedirs(os.path.join(output_dir, subset, cls_name), exist_ok=True)

    # Tracking data
    csv_data = [] # filename, label, split
    stats = {
        'total': 0,
        'classes': {
            'real': {'total': 0, 'train': 0, 'val': 0, 'test': 0},
            'fake': {'total': 0, 'train': 0, 'val': 0, 'test': 0}
        }
    }

    # Process each class
    for cls_name, label_code in classes.items():
        src_path = source_real if cls_name == 'real' else source_fake
        images = get_image_paths(src_path)
        random.shuffle(images)
        
        total_imgs = len(images)
        stats['classes'][cls_name]['total'] = total_imgs
        stats['total'] += total_imgs
        
        # Calculate split indices
        n_train = floor(total_imgs * split_ratio[0])
        n_val = floor(total_imgs * split_ratio[1])
        # Remainders go to test to ensure total matches
        
        train_imgs = images[:n_train]
        val_imgs = images[n_train:n_train+n_val]
        test_imgs = images[n_train+n_val:]
        
        split_mapping = {
            'train': train_imgs,
            'val': val_imgs,
            'test': test_imgs
        }
        
        print(f"Processing {cls_name}: {len(train_imgs)} Train, {len(val_imgs)} Val, {len(test_imgs)} Test")

        # Copy and Rename
        for subset, img_list in split_mapping.items():
            stats['classes'][cls_name][subset] = len(img_list)
            for idx, src_file in enumerate(img_list):
                ext = os.path.splitext(src_file)[1]
                # Format: real_train_0001.jpg
                new_filename = f"{cls_name}_{subset}_{idx+1:04d}{ext}"
                dest_path = os.path.join(output_dir, subset, cls_name, new_filename)
                
                shutil.copy2(src_file, dest_path)
                
                # Add to CSV record
                csv_data.append({
                    'filename': new_filename,
                    'label': label_code,
                    'split': subset,
                    'original_filename': os.path.basename(src_file) # Optional useful info
                })

    # Save CSV
    df = pd.DataFrame(csv_data)
    csv_path = os.path.join(output_dir, 'split.csv')
    df.to_csv(csv_path, index=False)
    print(f"Saved split tracking to {csv_path}")

    # Save JSON Summary
    json_path = os.path.join(output_dir, 'split_summary.json')
    with open(json_path, 'w') as f:
        json.dump(stats, f, indent=4)
    print(f"Saved summary to {json_path}")
    print("Done!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split dataset into Train/Val/Test")
    parser.add_argument("--source", default="dataset", help="Source dataset directory containing 'real' and 'fake'")
    parser.add_argument("--output", default="dataset_split", help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    
    split_dataset(args.source, args.output, args.seed)
