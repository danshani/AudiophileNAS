import os
import shutil
import numpy as np
import soundfile as sf
import librosa
import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3

# --- הגדרות ---
# הסקריפט יחפש קובץ בשם test_source.flac באותה תיקייה שבה הוא רץ
SOURCE_FILE = "test_source.flac"
DOWNLOADS_DIR = "downloads"

# וודא שתיקיית ההורדות קיימת
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

def create_clean_no_meta(src, dest):
    print(f"Creating 1: Clean Audio + DELETED Metadata -> {dest}")
    # טעינה ושמירה מחדש (מנקה מטא-דאטה טכנית)
    y, sr = librosa.load(src, sr=44100)
    sf.write(dest, y, sr)
    
    # מחיקת תגיות נוספת ליתר ביטחון
    try:
        tags = ID3(dest)
        tags.delete()
        tags.save()
    except:
        pass
    print("   -> Tags removed (Simulating bad download).")

def create_noisy_file(src, dest):
    print(f"Creating 2: BAD Audio (Heavy Noise) -> {dest}")
    # טוענים רק 30 שניות כדי שיהיה מהיר
    y, sr = librosa.load(src, sr=22050, duration=30) 
    
    # הוספת רעש לבן חזק
    noise = np.random.normal(0, 0.4, y.shape)
    y_noisy = y + noise
    
    sf.write(dest, y_noisy, sr)
    print("   -> Noise added (Should be flagged DIRTY).")

def create_clipped_file(src, dest):
    print(f"Creating 3: BAD Audio (Distortion) -> {dest}")
    y, sr = librosa.load(src, sr=22050, duration=30)
    
    # הגברה מוגזמת (Clipping)
    y_clipped = np.clip(y * 20.0, -0.99, 0.99) 
    
    sf.write(dest, y_clipped, sr)
    print("   -> Distortion added (Should be flagged DIRTY).")

if __name__ == "__main__":
    if not os.path.exists(SOURCE_FILE):
        print(f"Error: Could not find source file: {SOURCE_FILE}")
        print("Please make sure 'test_source.flac' exists in this folder.")
        exit(1)

    print(f"--- Starting Chaos Test using: {SOURCE_FILE} ---")
    
    # 1. קובץ נקי (אמור לעבור תיקון)
    create_clean_no_meta(SOURCE_FILE, os.path.join(DOWNLOADS_DIR, "test_CLEAN_repaired.mp3"))
    
    # 2. קובץ רועש (אמור לעבור לבידוד)
    create_noisy_file(SOURCE_FILE, os.path.join(DOWNLOADS_DIR, "test_NOISY.wav"))
    
    # 3. קובץ שרוף (אמור לעבור לבידוד)
    create_clipped_file(SOURCE_FILE, os.path.join(DOWNLOADS_DIR, "test_CLIPPED.wav"))
    
    print("\n--- Test Files Created! ---")
    print("Check your Scanner logs now.")