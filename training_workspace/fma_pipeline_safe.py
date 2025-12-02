import os
import requests
import librosa
import numpy as np
import random
import time

# --- הגדרות ---
# רשימת הטווחים המאוכלסים ביותר (מבוסס על FMA GitHub Data)
VALID_RANGES = [
    (106500, 107500), # אזור צפוף מאוד
    (115000, 116000),
    (130000, 132000),
    (140000, 142000),
    (148000, 150000)
]

BATCH_SIZE = 20 
IMG_SIZE = (128, 128)
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_AUDIO_DIR = os.path.join(WORKSPACE_DIR, "temp_audio")
DATASET_DIR = os.path.join(WORKSPACE_DIR, "dataset_fma_processed") 

# יצירת תיקיות
for d in [TEMP_AUDIO_DIR, os.path.join(DATASET_DIR, "clean"), os.path.join(DATASET_DIR, "noisy")]:
    os.makedirs(d, exist_ok=True)

# --- פונקציות עזר (אותן פונקציות כמו קודם) ---
def is_valid_music(y, sr):
    try:
        if len(y) / sr < 30: return False, "Short"
        flatness = np.mean(librosa.feature.spectral_flatness(y=y))
        if flatness > 0.4: return False, "Noise/Static"
        return True, "OK"
    except: return False, "Error"

def audio_to_spec(y, sr):
    try:
        target_len = int(sr * 3.0)
        start_trim = int(sr * 10.0) # מדלגים על ההתחלה
        if len(y) > start_trim + target_len: y_cut = y[start_trim : start_trim + target_len]
        else: y_cut = y[:target_len]
        if len(y_cut) < target_len: y_cut = np.pad(y_cut, (0, target_len - len(y_cut)))
        
        mel = librosa.feature.melspectrogram(y=y_cut, sr=sr, n_mels=IMG_SIZE[0])
        mel_db = librosa.power_to_db(mel, ref=np.max)
        min_val, max_val = mel_db.min(), mel_db.max()
        if max_val - min_val == 0: return None
        mel_norm = (mel_db - min_val) / (max_val - min_val)
        
        # התאמה לגודל
        if mel_norm.shape[1] > IMG_SIZE[1]: mel_norm = mel_norm[:, :IMG_SIZE[1]]
        else: mel_norm = np.pad(mel_norm, ((0,0), (0, IMG_SIZE[1] - mel_norm.shape[1])))
        return mel_norm
    except: return None

def add_aggressive_noise(audio, sr):
    noise_type = random.choice(['white', 'hum', 'clipping', 'mixed'])
    if noise_type == 'white': return audio + np.random.normal(0, 0.1, audio.shape)
    return audio 

def download_file(track_id):
    id_str = f"{track_id:06d}" 
    url = f"https://files.freemusicarchive.org/storage-new/tracks/{id_str}.mp3"
    try:
        # Timeout קצר מאוד כדי "לרוץ" מהר על קישורים מתים
        r = requests.get(url, stream=True, timeout=3) 
        if r.status_code == 200:
            filename = os.path.join(TEMP_AUDIO_DIR, f"{id_str}.mp3")
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            if os.path.getsize(filename) > 50000: return filename
            else: os.remove(filename)
    except: pass
    return None

# --- הלולאה הראשית: רצה רק על הטווחים הידועים ---
print(f"--- Smart Pipeline Started (Scanning Github verified ranges) ---")

current_batch = []
processed_count = 0

for start_range, end_range in VALID_RANGES:
    print(f"\n>>> Moving to range: {start_range} - {end_range}")
    
    for track_id in range(start_range, end_range):
        print(f"\rID {track_id} | Saved: {processed_count}...", end="")
        
        file_path = download_file(track_id)
        if file_path:
            current_batch.append(file_path)
            print(f" [V] Found!")
        
        # עיבוד כשהבאץ' מתמלא
        if len(current_batch) >= BATCH_SIZE:
            print(f"\nProcessing {len(current_batch)} files...")
            for f_path in current_batch:
                try:
                    y, sr = librosa.load(f_path, sr=22050, duration=60.0, mono=True)
                    if is_valid_music(y, sr)[0]:
                        spec = audio_to_spec(y, sr)
                        if spec is not None:
                            name = os.path.basename(f_path).replace('.mp3', '')
                            np.save(os.path.join(DATASET_DIR, "clean", name), spec)
                            
                            # רעש
                            spec_noisy = audio_to_spec(add_aggressive_noise(y, sr), sr)
                            np.save(os.path.join(DATASET_DIR, "noisy", name), spec_noisy)
                            processed_count += 1
                except: pass
                finally:
                    if os.path.exists(f_path): os.remove(f_path)
            current_batch = []

print("\n--- Pipeline Finished! ---")