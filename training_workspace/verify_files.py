import os
import librosa
import numpy as np

# הגדרת נתיבים
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_FOLDER = os.path.join(BASE_DIR, "source_music")

print(f"--- בודק תקינות קבצים בתיקייה: {SOURCE_FOLDER} ---")

if not os.path.exists(SOURCE_FOLDER):
    print("Error: Source folder not found!")
    exit()

files = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith(('mp3', 'flac', 'wav', 'm4a'))]
valid_count = 0
corrupt_count = 0

for file_name in files:
    file_path = os.path.join(SOURCE_FOLDER, file_name)
    try:
        # מנסים לטעון רק שנייה אחת כדי לראות שהקובץ לא שבור
        y, sr = librosa.load(file_path, sr=22050, duration=1.0)
        
        # בדיקה שהקובץ לא מכיל רק שקט מוחלט (Digital Silence)
        if np.max(np.abs(y)) == 0:
            print(f"[WARNING] {file_name} - הקובץ ריק (שקט מוחלט)!")
            corrupt_count += 1
        else:
            print(f"[OK] {file_name}")
            valid_count += 1
            
    except Exception as e:
        print(f"[ERROR] {file_name} - קובץ פגום! מומלץ למחוק אותו.")
        print(f"        Error details: {e}")
        corrupt_count += 1

print("-" * 30)
print(f"סיכום בדיקה:")
print(f"קבצים תקינים: {valid_count}")
print(f"קבצים בעייתיים: {corrupt_count}")

if corrupt_count == 0:
    print("\n>>> הכל מעולה! אתה יכול להריץ את generate_dataset.py <<<")
else:
    print("\n>>> יש קבצים בעייתיים. אנא מחק אותם לפני יצירת הדאטה <<<")