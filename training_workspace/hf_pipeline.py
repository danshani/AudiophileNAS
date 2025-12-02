import os
import numpy as np
import librosa
import random
from datasets import load_dataset

# --- הגדרות היעד ---
# אנחנו רוצים הרבה דאטה. נחתוך כל קובץ לכמה שיותר חתיכות.
TOTAL_MUSIC_TARGET = 8000  # יעד מוזיקה
TOTAL_SPEECH_TARGET = 2000 # יעד דיבור
# סה"כ = 10,000 דוגמאות חדשות

IMG_SIZE = (128, 128)
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(WORKSPACE_DIR, "dataset_hf_processed")

for d in [os.path.join(DATASET_DIR, "clean"), os.path.join(DATASET_DIR, "noisy")]:
    os.makedirs(d, exist_ok=True)

# --- פונקציות עיבוד משודרגות ---
def create_spectrogram(y, sr):
    try:
        mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=IMG_SIZE[0])
        mel_db = librosa.power_to_db(mel, ref=np.max)
        
        # נרמול 0-1
        min_val, max_val = mel_db.min(), mel_db.max()
        if max_val - min_val == 0: return None
        mel_norm = (mel_db - min_val) / (max_val - min_val)
        
        # התאמת גודל
        if mel_norm.shape[1] > IMG_SIZE[1]: mel_norm = mel_norm[:, :IMG_SIZE[1]]
        else: mel_norm = np.pad(mel_norm, ((0,0), (0, IMG_SIZE[1] - mel_norm.shape[1])))
        return mel_norm
    except: return None

def add_aggressive_noise(audio, sr):
    noise_type = random.choice(['white', 'hum', 'clipping', 'dropout', 'mixed'])
    if noise_type == 'white': return audio + np.random.normal(0, 0.1, audio.shape)
    elif noise_type == 'hum':
        t = np.linspace(0, len(audio)/sr, len(audio))
        return audio + (0.3 * np.sin(2 * np.pi * 50 * t))
    elif noise_type == 'clipping': return np.clip(audio * 10.0, -0.6, 0.6)
    elif noise_type == 'dropout':
        mod = audio.copy()
        start = random.randint(0, len(audio)-2000)
        mod[start:start+2000] = 0 
        return mod
    elif noise_type == 'mixed': 
        return np.clip((audio + np.random.normal(0, 0.05, audio.shape)) * 4.0, -0.8, 0.8)
    return audio

def process_file_chunks(audio_array, sr, filename_prefix, global_counter, limit):
    """
    פונקציה חכמה שחותכת קובץ אחד להרבה חתיכות של 3 שניות
    """
    if audio_array.dtype != np.float32:
        audio_array = audio_array.astype(np.float32)
        
    chunk_samples = int(sr * 3.0) # 3 שניות
    total_samples = len(audio_array)
    
    # חותכים בחפיפה קלה או ברצף. נלך על רצף.
    created_here = 0
    
    # רצים על הקובץ בקפיצות של 3 שניות
    for i in range(0, total_samples - chunk_samples, chunk_samples):
        if global_counter >= limit: break
        
        chunk = audio_array[i : i + chunk_samples]
        
        # 1. יצירת ספקטרוגרמה נקייה
        spec_clean = create_spectrogram(chunk, sr)
        if spec_clean is not None:
            name = f"{filename_prefix}_{global_counter}"
            
            # שמירה
            np.save(os.path.join(DATASET_DIR, "clean", name), spec_clean)
            
            # 2. יצירת ספקטרוגרמה רועשת
            noisy_chunk = add_aggressive_noise(chunk.copy(), sr)
            spec_noisy = create_spectrogram(noisy_chunk, sr)
            if spec_noisy is not None:
                np.save(os.path.join(DATASET_DIR, "noisy", name), spec_noisy)
                
                global_counter += 1
                created_here += 1
                
    return global_counter

# --- Main Pipeline ---
print(f"--- Starting MASSIVE Data Pipeline ---")
print(f"Target: {TOTAL_MUSIC_TARGET} Music + {TOTAL_SPEECH_TARGET} Speech = {TOTAL_MUSIC_TARGET + TOTAL_SPEECH_TARGET} Samples")

# 1. Music (GTZAN) - Slicing aggressively
print("\n>>> Processing Music (GTZAN)...")
ds_music = load_dataset("sanchit-gandhi/gtzan", split="train", streaming=True)

music_count = 0
for i, item in enumerate(ds_music):
    if music_count >= TOTAL_MUSIC_TARGET: break
    
    try:
        music_count = process_file_chunks(
            np.array(item['audio']['array']), 
            item['audio']['sampling_rate'], 
            "music_gtzan", 
            music_count, 
            TOTAL_MUSIC_TARGET
        )
        print(f"\rMusic Samples: {music_count}/{TOTAL_MUSIC_TARGET}", end="")
    except: continue

# 2. Speech (LibriSpeech)
print("\n\n>>> Processing Speech (LibriSpeech)...")
ds_speech = load_dataset("librispeech_asr", "clean", split="train.100", streaming=True)

speech_count = 0
for i, item in enumerate(ds_speech):
    if speech_count >= TOTAL_SPEECH_TARGET: break
    
    try:
        speech_count = process_file_chunks(
            np.array(item['audio']['array']), 
            item['audio']['sampling_rate'], 
            "speech_libri", 
            speech_count, 
            TOTAL_SPEECH_TARGET
        )
        print(f"\rSpeech Samples: {speech_count}/{TOTAL_SPEECH_TARGET}", end="")
    except: continue

print(f"\n\n--- DONE! You now have {music_count + speech_count} NEW samples on disk. ---")