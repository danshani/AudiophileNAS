import os
import numpy as np
import librosa
import soundfile as sf
import random
import shutil

# --- הגדרות ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_FOLDER = os.path.join(BASE_DIR, "source_music")
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
SAMPLE_RATE = 22050
DURATION = 3.0 

print("--- [DEBUG] התחלת סקריפט יצירת דאטה ---")

# ניקוי תיקיות
if os.path.exists(DATASET_DIR):
    shutil.rmtree(DATASET_DIR)
os.makedirs(os.path.join(DATASET_DIR, "clean"))
os.makedirs(os.path.join(DATASET_DIR, "noisy"))

def add_aggressive_noise(audio):
    """הוספת רעש אגרסיבית עם לוגים"""
    noise_type = random.choice(['white', 'hum', 'clipping', 'dropout', 'mixed'])
    
    if noise_type == 'white':
        noise_level = random.uniform(0.05, 0.2) # רעש חזק
        noise = np.random.normal(0, noise_level, audio.shape)
        return audio + noise, "White Noise"
        
    elif noise_type == 'hum':
        t = np.linspace(0, len(audio)/SAMPLE_RATE, len(audio))
        hum = random.uniform(0.1, 0.4) * np.sin(2 * np.pi * 50 * t) # המהום חזק
        return audio + hum, "50Hz Hum"
        
    elif noise_type == 'clipping':
        factor = random.uniform(5.0, 15.0) 
        return np.clip(audio * factor, -0.6, 0.6), "Hard Clipping"

    elif noise_type == 'dropout':
        modified = audio.copy()
        for _ in range(random.randint(3, 8)): # הרבה חורים
            start = random.randint(0, len(audio) - 2000)
            length = random.randint(1000, 5000)
            modified[start : start + length] = 0
        return modified, "Dropouts"
    
    elif noise_type == 'mixed':
        noise = np.random.normal(0, 0.1, audio.shape)
        return np.clip((audio + noise) * 5.0, -0.8, 0.8), "Mixed Destruction"
    
    return audio, "None"

files = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith(('mp3', 'flac', 'wav', 'm4a'))]
print(f"--- [DEBUG] נמצאו {len(files)} קבצי מקור ---")

count = 0
skipped_silent = 0

for file_name in files:
    try:
        y, sr = librosa.load(os.path.join(SOURCE_FOLDER, file_name), sr=SAMPLE_RATE, mono=True)
        chunk_len = int(DURATION * SAMPLE_RATE)
        
        if len(y) < chunk_len: 
            print(f"[DEBUG] קובץ קצר מדי: {file_name}")
            continue

        # לוקחים עד 30 צ'אנקים מכל שיר
        for i in range(0, min(len(y) - chunk_len, chunk_len * 30), chunk_len):
            chunk = y[i : i + chunk_len]
            
            # בדיקת שקט (חשוב!)
            amplitude = np.mean(np.abs(chunk))
            if amplitude < 0.02: 
                skipped_silent += 1
                continue 

            base_name = f"{count}_{file_name[:-4]}"
            
            # יצירת הרועש
            noisy_chunk, noise_type = add_aggressive_noise(chunk.copy())
            
            # --- DEBUG: בדיקה שהרעש באמת שינה משהו ---
            diff = np.mean(np.abs(chunk - noisy_chunk))
            if diff < 0.001 and noise_type != "None":
                 print(f"[WARNING] הרעש לא תפס! {file_name} -> {noise_type} (Diff: {diff:.5f})")

            # שמירה
            sf.write(os.path.join(DATASET_DIR, "clean", f"c_{base_name}.wav"), chunk, SAMPLE_RATE)
            sf.write(os.path.join(DATASET_DIR, "noisy", f"n_{base_name}.wav"), noisy_chunk, SAMPLE_RATE)
            
            # הדפסת מדגם כל 100 קבצים
            if count % 100 == 0:
                print(f"[INFO] Sample {count}: Added {noise_type} to {file_name} (Amp: {amplitude:.3f})")
            
            count += 1
            
    except Exception as e:
        print(f"[ERROR] נכשל בקובץ {file_name}: {e}")

print(f"--- [DEBUG] סיום. נוצרו {count} זוגות. דולגו {skipped_silent} קטעי שקט. ---")