import os
import musicbrainzngs
import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
import re

# Configure MusicBrainz
musicbrainzngs.set_useragent("AudiophileNAS_Fixer", "0.1", "http://example.com")

def get_title_from_filename(filename):
    # Remove extension
    name = os.path.splitext(filename)[0]
    # Remove leading numbers (e.g., "01 dasty ho" -> "dasty ho")
    name = re.sub(r'^\d+\s*[-_.]?\s*', '', name)
    return name.strip()

def update_tags(filepath, artist, title):
    try:
        if filepath.lower().endswith('.mp3'):
            try:
                audio = MP3(filepath, ID3=EasyID3)
            except mutagen.id3.ID3NoHeaderError:
                audio = MP3(filepath)
                audio.add_tags()
            
            audio['artist'] = artist
            audio['title'] = title
            audio.save()
            
        elif filepath.lower().endswith('.flac'):
            audio = FLAC(filepath)
            audio['artist'] = artist
            audio['title'] = title
            audio.save()
            
        print(f"✅ Updated tags: {artist} - {title}")
        return True
    except Exception as e:
        print(f"❌ Error updating tags: {e}")
        return False

def interactive_fix(folder_path):
    print(f"🔍 Scanning {folder_path} for files with missing metadata...\n")
    
    files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.mp3', '.flac', '.wav', '.m4a'))]
    
    if not files:
        print("No audio files found in this folder.")
        return

    for filename in files:
        filepath = os.path.join(folder_path, filename)
        
        # Check if tags are missing (simplified check)
        try:
            if filename.lower().endswith('.mp3'):
                audio = MP3(filepath, ID3=EasyID3)
                if 'artist' in audio and 'title' in audio:
                    continue # Skip if tags exist
            elif filename.lower().endswith('.flac'):
                audio = FLAC(filepath)
                if 'artist' in audio and 'title' in audio:
                    continue
        except:
            pass # If error reading tags, assume they are missing and process it

        print(f"\n---------------------------------------------------")
        print(f"📂 File: {filename}")
        
        # 1. Guess Title
        search_query = get_title_from_filename(filename)
        print(f"🔎 Searching MusicBrainz for track: '{search_query}'")
        
        try:
            # 2. Search MusicBrainz
            result = musicbrainzngs.search_recordings(recording=search_query, limit=10)
            recordings = result.get('recording-list', [])
            
            if not recordings:
                print("⚠️ No results found.")
                continue

            # 3. Show Options
            print("\nFound these artists:")
            unique_artists = []
            seen = set()
            
            for rec in recordings:
                artist_name = rec['artist-credit-phrase']
                track_title = rec['title']
                key = (artist_name, track_title)
                
                if key not in seen:
                    unique_artists.append((artist_name, track_title))
                    seen.add(key)
            
            for i, (artist, title) in enumerate(unique_artists[:10], 1):
                print(f"   {i}. {artist}  (Track: {title})")
            
            print("   0. Skip this file")
            print("   M. Manual Entry (Type artist name yourself)")

            # 4. User Choice
            while True:
                choice = input("\nSelect an artist (0-10 or M): ").strip().upper()
                
                if choice == '0':
                    print("Skipping...")
                    break
                
                if choice == 'M':
                    manual_artist = input("Enter Artist Name: ")
                    manual_title = input("Enter Track Title (or press Enter to keep search query): ")
                    if not manual_title:
                        manual_title = search_query
                    update_tags(filepath, manual_artist, manual_title)
                    break

                if choice.isdigit() and 1 <= int(choice) <= len(unique_artists):
                    selected_artist, selected_title = unique_artists[int(choice)-1]
                    update_tags(filepath, selected_artist, selected_title)
                    break
                    
        except Exception as e:
            print(f"Error searching/processing: {e}")

if __name__ == "__main__":
    # You can change this path to wherever your problem files are
    target_folder = "downloads" 
    interactive_fix(target_folder)
