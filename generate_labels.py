
import os
import csv

OUTPUT_DIR = "dataset"
REAL_DIR = os.path.join(OUTPUT_DIR, "real")
FAKE_DIR = os.path.join(OUTPUT_DIR, "fake")
LABELS_FILE = os.path.join(OUTPUT_DIR, "labels.csv")

def main():
    print("Generating labels.csv...")
    with open(LABELS_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "label", "class_id"])
        
        # Real
        if os.path.exists(REAL_DIR):
            for f in os.listdir(REAL_DIR):
                if f.endswith('.jpg') or f.endswith('.png'):
                    writer.writerow([os.path.join("real", f), "REAL", 0])
        
        # Fake
        if os.path.exists(FAKE_DIR):
            for f in os.listdir(FAKE_DIR):
                if f.endswith('.jpg') or f.endswith('.png'):
                    writer.writerow([os.path.join("fake", f), "FAKE", 1])
                    
    print(f"Labels saved to {LABELS_FILE}")

if __name__ == "__main__":
    main()
