import os
import sys
import time
import shutil
import sqlite3
import logging
import subprocess
import numpy as np
import librosa
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Try importing TFLite
try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    import tensorflow.lite as tflite

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", "..", ".."))

WATCH_DIR = os.path.join(PROJECT_ROOT, "downloads")
QUARANTINE_DIR = os.path.join(PROJECT_ROOT, "quarantine")
MODEL_PATH = os.path.join(BASE_DIR, "..", "models", "audio_quality.tflite")
DB_PATH = os.path.join(BASE_DIR, "scan_history.db")

# Path to your existing Metadata CLI script
METADATA_CLI_PATH = os.path.join(PROJECT_ROOT, "features", "audio-repair", "metadata", "cli", "commands.py")

NOISE_THRESHOLD = 0.5 

# Logging setup (Force UTF-8 for Windows)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [Scanner] - %(message)s',
    handlers=[
        logging.FileHandler("scanner.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout) # Ensure stdout handles encoding correctly
    ]
)

# --- Database ---
class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                filepath TEXT UNIQUE,
                is_clean INTEGER,
                noise_score REAL,
                scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata_status TEXT
            )
        ''')
        self.conn.commit()

    def is_scanned(self, filepath):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM scans WHERE filepath = ?", (filepath,))
        return cursor.fetchone() is not None

    def add_result(self, filepath, is_clean, score, metadata_status="PENDING"):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO scans (filename, filepath, is_clean, noise_score, metadata_status) VALUES (?, ?, ?, ?, ?)",
                (os.path.basename(filepath), filepath, 1 if is_clean else 0, score, metadata_status)
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass

    def update_metadata_status(self, filepath, status):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE scans SET metadata_status = ? WHERE filepath = ?", (status, filepath))
        self.conn.commit()

# --- AI Predictor ---
class AudioPredictor:
    def __init__(self, model_path):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {model_path}")
        
        logging.info("Loading AI Model...")
        self.interpreter = tflite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

    def preprocess(self, file_path):
        try:
            duration = 3.0
            # Load only 10s to be fast
            y, sr = librosa.load(file_path, sr=22050, duration=10.0)
            target_len = int(22050 * duration)
            
            if len(y) > target_len:
                start = (len(y) - target_len) // 2
                y = y[start : start + target_len]
            elif len(y) < target_len:
                y = np.pad(y, (0, target_len - len(y)))

            mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)
            mel_db = librosa.power_to_db(mel, ref=np.max)
            min_val, max_val = mel_db.min(), mel_db.max()
            if max_val - min_val == 0: return None
            mel_norm = (mel_db - min_val) / (max_val - min_val)
            
            if mel_norm.shape[1] > 128: mel_norm = mel_norm[:, :128]
            else: mel_norm = np.pad(mel_norm, ((0,0), (0, 128 - mel_norm.shape[1])))
            
            return mel_norm[np.newaxis, ..., np.newaxis].astype(np.float32)
        except Exception as e:
            logging.error(f"Preprocessing error: {e}")
            return None

    def predict(self, file_path):
        input_data = self.preprocess(file_path)
        if input_data is None: return 1.0
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()
        return float(self.interpreter.get_tensor(self.output_details[0]['index'])[0][0])

# --- Subprocess Integration ---
def run_metadata_repair(file_path):
    """
    Runs the metadata CLI tool as a subprocess.
    Now simpler because commands.py handles its own paths.
    """
    if not os.path.exists(METADATA_CLI_PATH):
        logging.error(f"Metadata CLI not found at: {METADATA_CLI_PATH}")
        return False

    logging.info(f"[METADATA] Launching repair process for: {os.path.basename(file_path)}")
    
    # הפקודה הפשוטה ביותר
    cmd = [
        sys.executable,
        METADATA_CLI_PATH,
        file_path,
        "--write",
        "--backup"
    ]

    try:
        # פשוט מריצים. בלי cwd ובלי משחקי סביבה.
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            # חילוץ מידע רלוונטי מהלוג
            output_lines = result.stdout.strip().split('\n')
            # מחפש שורות מעניינות להצגה
            summary = [line for line in output_lines if "Metadata completed" in line or "Success" in line]
            log_msg = summary[-1] if summary else "Repair Finished"
            
            logging.info(f"[METADATA] Success! {log_msg}")
            return True
        else:
            logging.warning(f"[METADATA] Process failed.\nError: {result.stderr.strip()}")
            return False
            
    except Exception as e:
        logging.error(f"[METADATA] Execution error: {e}")
        return False

# --- Watchdog Handler ---
class NewFileHandler(FileSystemEventHandler):
    def __init__(self, db, predictor):
        self.db = db
        self.predictor = predictor

    def on_created(self, event):
        if event.is_directory: return
        filename = event.src_path
        if not filename.lower().endswith(('.mp3', '.flac', '.wav', '.m4a')): return
        time.sleep(1) # Wait for file copy
        self.process_file(filename)

    def process_file(self, filepath):
        if self.db.is_scanned(filepath):
            logging.info(f"Skipping known file: {os.path.basename(filepath)}")
            return

        logging.info(f"Analyzing: {os.path.basename(filepath)}...")
        
        # 1. AI Check
        score = self.predictor.predict(filepath)
        is_clean = score < NOISE_THRESHOLD
        
        status_icon = '[CLEAN]' if is_clean else '[DIRTY]'
        logging.info(f"   Score: {score:.4f} | Status: {status_icon}")
        
        # 2. Decision Logic
        if is_clean:
            self.db.add_result(filepath, is_clean, score, "PROCESSING")
            
            # 3. Run Metadata Repair
            success = run_metadata_repair(filepath)
            
            if success:
                self.db.update_metadata_status(filepath, "COMPLETED")
            else:
                self.db.update_metadata_status(filepath, "FAILED")
                
        else:
            # Quarantine
            self.db.add_result(filepath, is_clean, score, "QUARANTINED")
            self.move_to_quarantine(filepath)

    def move_to_quarantine(self, filepath):
        try:
            if not os.path.exists(QUARANTINE_DIR): os.makedirs(QUARANTINE_DIR)
            dest = os.path.join(QUARANTINE_DIR, os.path.basename(filepath))
            shutil.move(filepath, dest)
            logging.warning(f"   [MOVED] File quarantined: {dest}")
        except Exception as e:
            logging.error(f"Failed to quarantine: {e}")

# --- Main ---
if __name__ == "__main__":
    for d in [WATCH_DIR, QUARANTINE_DIR]: os.makedirs(d, exist_ok=True)

    db = Database()
    
    # Initialize AI
    try:
        predictor = AudioPredictor(MODEL_PATH)
    except Exception as e:
        logging.critical(f"Failed to load AI model: {e}")
        exit(1)

    logging.info(f"[STARTED] Scanner Service is running!")
    logging.info(f"   Watching: {WATCH_DIR}")
    logging.info(f"   Metadata CLI: {METADATA_CLI_PATH}")

    # Start Watchdog
    event_handler = NewFileHandler(db, predictor)
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=True)
    
    # Initial Scan
    logging.info("--- Initial Scan ---")
    for root, dirs, files in os.walk(WATCH_DIR):
        for file in files:
            if file.lower().endswith(('.mp3', '.flac', '.wav', '.m4a')):
                event_handler.process_file(os.path.join(root, file))

    observer.start()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logging.info("Scanner Stopped.")
    observer.join()