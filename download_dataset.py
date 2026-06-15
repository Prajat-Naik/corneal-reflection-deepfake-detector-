import os
import time
import urllib.request
import shutil

REAL_DIR = 'dataset/real'
FAKE_DIR = 'dataset/fake'

def clear_directory(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)
    print(f"Cleared {path}")

def download_images(url, dest_dir, count, prefix, delay=1.0):
    print(f"Downloading {count} images to {dest_dir}...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    success = 0
    for i in range(count):
        try:
            req = urllib.request.Request(url, headers=headers)
            filename = os.path.join(dest_dir, f"{prefix}_{i:03d}.jpg")
            with urllib.request.urlopen(req, timeout=10) as response:
                with open(filename, 'wb') as out_file:
                    out_file.write(response.read())
            print(f"[OK] Saved {filename}")
            success += 1
            time.sleep(delay) # Be polite
        except Exception as e:
            print(f"[ERR] Failed {i}: {e}")
    
    print(f"Finished. Downloaded {success}/{count} images.")

def main():
    print("=== Acquiring High-Res Dataset ===")
    
    # 1. Clear old data
    clear_directory(REAL_DIR)
    clear_directory(FAKE_DIR)
    
    # 2. Download Fakes (stylegan2)
    # thispersondoesnotexist returns a new image on every request
    print("\n--- Downloading FAKE images (StyleGAN2) ---")
    download_images("https://thispersondoesnotexist.com", FAKE_DIR, 20, "fake", delay=1.5)
    
    # 3. Download Reals
    # loremflickr provides random images from Flickr based on keywords
    print("\n--- Downloading REAL images (loremflickr) ---")
    # Redirects to random flickr photo tagged 'face' or 'portrait'
    download_images("https://loremflickr.com/1024/1024/portrait", REAL_DIR, 20, "real_flickr", delay=1.5)

if __name__ == "__main__":
    main()
