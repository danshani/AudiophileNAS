import os
import shutil
import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.easymp4 import EasyMP4

# Define paths
SOURCE_DIR = "downloads"
READY_DIR = "downloads/ready_to_file"
NEEDS_WORK_DIR = "downloads/needs_tagging"

# Create directories if they don't exist
os.makedirs(READY_DIR, exist_ok=True)
os.makedirs(NEEDS_WORK_DIR, exist_ok=True)

def is_metadata_complete(filepath):
    try:
        # Load file with mutagen
        audio = mutagen.File(filepath, easy=True)
        
        if not audio:
            return False
            
        # Check for essential tags: Artist and Title
        # (You can add 'album' here if you want to be stricter)
        artist = audio.get('artist', [''])[0]
        title = audio.get('title', [''])[0]
        
        # Return True only if both are present and not empty
        return bool(artist and title)
        
    except Exception as e:
        print(f"Error checking {filepath}: {e}")
        return False

def sort_files():
    print(f"Scanning {SOURCE_DIR}...")
    count_ready = 0
    count_needs_work = 0
    
    for filename in os.listdir(SOURCE_DIR):
        filepath = os.path.join(SOURCE_DIR, filename)
        
        # Skip directories (like the ones we just created)
        if os.path.isdir(filepath):
            continue
            
        if is_metadata_complete(filepath):
            shutil.move(filepath, os.path.join(READY_DIR, filename))
            count_ready += 1
            print(f"[READY] {filename}")
        else:
            shutil.move(filepath, os.path.join(NEEDS_WORK_DIR, filename))
            count_needs_work += 1
            print(f"[NEEDS WORK] {filename}")

    print("-" * 30)
    print(f"Sorting Complete!")
    print(f"Ready to file (Good Metadata): {count_ready}")
    print(f"Needs tagging (Missing Info): {count_needs_work}")

if __name__ == "__main__":
    sort_files()
