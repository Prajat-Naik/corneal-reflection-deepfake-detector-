
import os
import cv2
import time
import requests
import shutil
import csv
import numpy as np
from mediapipe_utils import IrisTracker

# Configuration
REAL_TARGET = 200
FAKE_TARGET = 200
MIN_RES = 512
SHARPNESS_TH = 30.0  # Very relaxed
OUTPUT_DIR = "dataset"
REAL_DIR = os.path.join(OUTPUT_DIR, "real")
FAKE_DIR = os.path.join(OUTPUT_DIR, "fake")
DEBUG_DIR = os.path.join(OUTPUT_DIR, "debug")
LABELS_FILE = os.path.join(OUTPUT_DIR, "labels.csv")

# Initialize Tracker - RECREATE WITH LOWER CONFIDENCE
# We need to hack the IrisTracker instance or recreate the file logic.
# The IrisTracker class in mediapipe_utils.py uses hardcoded confidence 0.5.
# Let's try to pass an argument if possible. No, it's hardcoded.
# We will subclass or just instance it and hope 0.5 is fine (usually is).
tracker = IrisTracker()

def setup_dirs():
    for d in [REAL_DIR, FAKE_DIR, DEBUG_DIR]:
        os.makedirs(d, exist_ok=True)

# Wikimedia API
WIKI_API_URL = "https://commons.wikimedia.org/w/api.php"
# Generator for Wikimedia URLs
def wikimedia_url_generator():
    search_terms = [
        "portrait photograph", "human face photo", "person portrait", "studio portrait",
        "actor portrait", "business portrait", "scientist portrait", "model portrait",
        "man face", "woman face", "old man portrait", "old woman portrait",
        "smiling person", "serious person face", "asian person portrait", "african person portrait",
        "european person portrait", "indian person portrait", "latino person portrait",
        "middle eastern person portrait", "young man portrait", "young woman portrait",
        "child portrait", "boy portrait", "girl portrait", "teenager portrait",
        "worker portrait", "doctor portrait", "teacher portrait", "artist portrait",
        "musician portrait", "athlete portrait", "politician portrait", "writer portrait",
        "soldier portrait", "police portrait", "nurse portrait", "engineer portrait",
        "lawyer portrait", "chef portrait", "farmer portrait", "driver portrait",
        "student portrait", "professor portrait", "grandparent portrait", "baby portrait",
        "family portrait", "couple portrait", "friends portrait", "group portrait",
        "person looking at camera", "person glasses", "person beard", "person hat",
        "person smile", "person sad", "person angry", "person surprised"
    ]
    import random
    random.shuffle(search_terms) 
    
    for term in search_terms:
        # Use search generator
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": term,
            "gsrnamespace": 6, # Files only
            "gsrlimit": 50,
            "prop": "imageinfo",
            "iiprop": "url",
            "iiurlwidth": 1024 
        }
        
        continue_token = None
        while True:
            p = params.copy()
            if continue_token:
                p.update(continue_token)
            
            try:
                # print(f"DEBUG: Requesting {p['gsrsearch']} with {p}")
                r = requests.get(WIKI_API_URL, params=p, headers={'User-Agent': 'DeepfakeDetectionBot/1.0'})
                data = r.json()
                
                # print(f"DEBUG: Keys: {data.keys()}")
                if "query" in data and "pages" in data["query"]:
                    pages = data["query"]["pages"]
                    print(f"DEBUG: Found {len(pages)} pages")
                    for k, v in pages.items():
                        if "imageinfo" in v:
                            # Verify it's a jpg/png
                            url = v["imageinfo"][0]["thumburl"] if "thumburl" in v["imageinfo"][0] else v["imageinfo"][0]["url"]
                            if url.lower().endswith(('.jpg', '.jpeg', '.png')):
                                yield url
                else:
                     print(f"DEBUG: No pages or query in data: {data.keys()}")
                
                if "continue" in data:
                    continue_token = data["continue"]
                    # print(f"DEBUG: Continue token: {continue_token}")
                else:
                    print(f"DEBUG: No continue token for {term}")
                    break # Next search term
            except Exception as e:
                print(f"Wiki Error: {e}")
                break

# Global generator instance
wiki_gen = wikimedia_url_generator()

def get_image_url(is_fake):
    global wiki_gen
    if is_fake:
        # StyleGAN2 fakes
        return "https://thispersondoesnotexist.com"
    else:
        # Wikimedia Commons
        try:
            return next(wiki_gen)
        except StopIteration:
            print("Wikimedia generator exhausted. Restarting...")
            from random import choice
            # Fallback to specific high quality sources if needed, or restart
            # Let's just restart for now, or use a backup
            wiki_gen = wikimedia_url_generator()
            return next(wiki_gen)
        except Exception:
            # Fallback to random picsum buffer if wiki fails
            return f"https://picsum.photos/1024/1024?random={time.time()}"

def download_image(url):
    try:
        # Simple download
        resp = requests.get(url, timeout=10, headers={'User-Agent': 'DeepfakeDetectionBot/1.0'})
        if resp.status_code == 200:
            arr = np.asarray(bytearray(resp.content), dtype=np.uint8)
            img = cv2.imdecode(arr, -1)
            # Check valid image
            if img is None: return None
            return img
    except Exception as e:
        print(f"Download error: {e}")
    return None

def check_sharpness(img):
    if len(img.shape) == 2:
        gray = img
    else:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    return variance


def check_eye_reflection(eye_img, eye_mask):
    try:
        # If grayscale, convert to BGR first or just use intensity?
        # HSV conversion requires 3 channels.
        if len(eye_img.shape) == 2:
             eye_img = cv2.cvtColor(eye_img, cv2.COLOR_GRAY2BGR)
             
        hsv = cv2.cvtColor(eye_img, cv2.COLOR_BGR2HSV)
        v = hsv[..., 2]
        
        # If mask is boolean, use it directly. If uint8 (0/255), >0.
        if eye_mask.dtype == bool:
            mask_bool = eye_mask
        else:
            mask_bool = eye_mask > 0
            
        if np.sum(mask_bool) == 0: return False
        
        vals = v[mask_bool]
        p_max = np.max(vals) if len(vals) > 0 else 0
        # print(f"DEBUG: Max V: {p_max}")
        return p_max > 120 # Reasonable threshold
    except Exception as e:
        print(f"DEBUG: check_eye_reflection error: {e}")
        return False

def process_image(img, img_id, label_dir, is_fake):
    # 1. Resolution Check
    h, w = img.shape[:2]
    if h < MIN_RES or w < MIN_RES:
        print(f"Skipping: Low Res {w}x{h}")
        return False

    # 2. Sharpness Check
    sharpness = check_sharpness(img)
    if sharpness < SHARPNESS_TH:
         pass 

    # 3. Face/Eye Detection
    temp_path = os.path.join(DEBUG_DIR, "temp.jpg")
    cv2.imwrite(temp_path, img)
    
    success, data = tracker.process_image(temp_path)
    if not success:
        # Save failed image to debug
        cv2.imwrite(os.path.join(DEBUG_DIR, f"fail_face_{img_id}.jpg"), img)
        print(f"Skipping: Face/Eye Detection Failed ({data})")
        return False

    # Check eye masks
    l_sum = np.sum(data['left_mask'])
    r_sum = np.sum(data['right_mask'])
    if l_sum == 0 or r_sum == 0:
         print(f"Skipping: Empty Eye Masks (L:{l_sum} R:{r_sum})")
         return False

    # 4. Check Reflections
    # Use CROPS
    l_img = data['left_img']
    l_mask = data['left_mask']
    r_img = data['right_img']
    r_mask = data['right_mask']
    
    if not check_eye_reflection(l_img, l_mask) or not check_eye_reflection(r_img, r_mask):
        print(f"Skipping: No Corneal Reflections")
        return False

    # Save Valid
    prefix = "fake" if is_fake else "real"
    filename = f"{prefix}_{img_id:03d}.jpg"
    save_path = os.path.join(label_dir, filename)
    cv2.imwrite(save_path, img)
    
    print(f"[SAVED] {filename} (Sharpness: {sharpness:.1f})")
    return True

def build_class(target_count, is_fake):
    dest_dir = FAKE_DIR if is_fake else REAL_DIR
    # Check existing count
    existing = len([f for f in os.listdir(dest_dir) if f.endswith('.jpg')])
    current_count = existing
    
    print(f"--- Building {'FAKE' if is_fake else 'REAL'} Dataset (Target: {target_count}, Current: {current_count}) ---")
    
    while current_count < target_count:
        url = get_image_url(is_fake)
        img = download_image(url)
        if img is None:
            time.sleep(1)
            continue
            
        if process_image(img, current_count, dest_dir, is_fake):
            current_count += 1
        
        time.sleep(0.5)

def main():
    setup_dirs()
    # Build Fakes First (to test MediaPipe) - commented out if done?
    # build_class(FAKE_TARGET, is_fake=True)
    
    # Build Reals
    build_class(REAL_TARGET, is_fake=False)
    
    # Generate CSV
    print("Generating labels.csv...")
    with open(LABELS_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "label", "class_id"])
        
        for f in os.listdir(REAL_DIR):
            if f.endswith('.jpg'):
                 writer.writerow([os.path.join("real", f), "REAL", 0])
                 
        for f in os.listdir(FAKE_DIR):
            if f.endswith('.jpg'):
                 writer.writerow([os.path.join("fake", f), "FAKE", 1])
                 
    print("Dataset Build Complete!")

if __name__ == "__main__":
    main()
