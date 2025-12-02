import os
import numpy as np
import librosa
import tensorflow as tf
from tensorflow.keras import layers, models, regularizers, callbacks, optimizers
from sklearn.model_selection import train_test_split

# --- הגדרות ---
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))

# נתיבים לשני מאגרי המידע
LOCAL_DIR = os.path.join(WORKSPACE_DIR, "dataset")              # הדאטה האישי שלך (WAV)
HF_DIR = os.path.join(WORKSPACE_DIR, "dataset_hf_processed")    # הדאטה מהאינטרנט (NPY)

# נתיב שמירה סופי
FINAL_MODEL_DIR = os.path.abspath(os.path.join(WORKSPACE_DIR, "..", "features", "audio-repair", "models"))

# פרמטרים לאימון
IMG_SIZE = (128, 128)
BATCH_SIZE = 32
EPOCHS = 40 

print(f"--- [ULTIMATE TRAINER] Loading Hybrid Dataset (Local + Web) ---")

# --- פונקציית טעינה היברידית (מטפלת בשני הסוגים) ---
def load_sample(file_path):
    try:
        # סוג 1: קובץ מעובד מוכן (NPY מהאינטרנט)
        if file_path.endswith('.npy'):
            return np.load(file_path)
            
        # סוג 2: קובץ אודיו גולמי (WAV מהמחשב שלך)
        elif file_path.endswith('.wav'):
            # טעינה ועיבוד בזמן אמת
            y, sr = librosa.load(file_path, sr=22050, duration=3.0)
            target_len = int(22050 * 3.0)
            if len(y) < target_len: y = np.pad(y, (0, target_len - len(y)))
            else: y = y[:target_len]
            
            mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=IMG_SIZE[0])
            mel_db = librosa.power_to_db(mel, ref=np.max)
            
            # נרמול (חובה!)
            min_val, max_val = mel_db.min(), mel_db.max()
            if max_val - min_val == 0: return None
            mel_norm = (mel_db - min_val) / (max_val - min_val)
            
            # התאמת גודל
            if mel_norm.shape[1] > IMG_SIZE[1]: mel_norm = mel_norm[:, :IMG_SIZE[1]]
            else: mel_norm = np.pad(mel_norm, ((0,0), (0, IMG_SIZE[1] - mel_norm.shape[1])))
            return mel_norm
            
    except: return None

# --- שלב 1: איסוף כל הקבצים ---
data, labels = [], []

# רשימות לקבצים
files_clean = []
files_noisy = []

# א. הוספת קבצים מקומיים (אם קיימים)
if os.path.exists(LOCAL_DIR):
    local_c = [os.path.join(LOCAL_DIR, "clean", f) for f in os.listdir(os.path.join(LOCAL_DIR, "clean"))]
    local_n = [os.path.join(LOCAL_DIR, "noisy", f) for f in os.listdir(os.path.join(LOCAL_DIR, "noisy"))]
    files_clean.extend(local_c)
    files_noisy.extend(local_n)
    print(f"[INFO] Source 1 (Local): Found {len(local_c)} clean samples")

# ב. הוספת קבצים מהאינטרנט (אם קיימים)
if os.path.exists(HF_DIR):
    hf_c = [os.path.join(HF_DIR, "clean", f) for f in os.listdir(os.path.join(HF_DIR, "clean"))]
    hf_n = [os.path.join(HF_DIR, "noisy", f) for f in os.listdir(os.path.join(HF_DIR, "noisy"))]
    files_clean.extend(hf_c)
    files_noisy.extend(hf_n)
    print(f"[INFO] Source 2 (Web):   Found {len(hf_c)} clean samples")

# איזון הכמויות
limit = min(len(files_clean), len(files_noisy))
print(f"[INFO] Total balanced pairs to load: {limit}")

# --- שלב 2: טעינה לזיכרון ---
print("Loading data... (This might take a minute)")
for i in range(limit):
    if i % 1000 == 0 and i > 0: print(f"   Loaded {i} pairs...")
    
    # טעינת הזוג (נקי/רועש)
    c_spec = load_sample(files_clean[i])
    n_spec = load_sample(files_noisy[i])
    
    if c_spec is not None and n_spec is not None:
        data.extend([c_spec, n_spec])
        labels.extend([0, 1])

X = np.array(data)[..., np.newaxis]
y = np.array(labels)
print(f"[INFO] RAM Loading Complete. Final Shape: {X.shape}")

# חלוקה
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42, stratify=y)

# --- שלב 3: המודל (ULTRA ARCHITECTURE) ---
model = models.Sequential([
    layers.Input(shape=(128, 128, 1)),
    
    # Block 1
    layers.Conv2D(32, 3, padding='same', kernel_regularizer=regularizers.l2(0.0001)),
    layers.BatchNormalization(), layers.Activation('relu'), layers.MaxPooling2D(2),
    
    # Block 2
    layers.Conv2D(64, 3, padding='same', kernel_regularizer=regularizers.l2(0.0001)),
    layers.BatchNormalization(), layers.Activation('relu'), layers.MaxPooling2D(2),
    
    # Block 3
    layers.Conv2D(128, 3, padding='same', kernel_regularizer=regularizers.l2(0.0001)),
    layers.BatchNormalization(), layers.Activation('relu'), layers.MaxPooling2D(2),
    
    # Block 4 (Deep Feature Extraction)
    layers.Conv2D(256, 3, padding='same', kernel_regularizer=regularizers.l2(0.0001)),
    layers.BatchNormalization(), layers.Activation('relu'), layers.MaxPooling2D(2),
    
    # Summary
    layers.GlobalAveragePooling2D(),
    
    # Classifier
    layers.Dense(256, activation='relu'),
    layers.Dropout(0.5),
    layers.Dense(1, activation='sigmoid')
])

model.compile(optimizer=optimizers.Adam(1e-3), loss='binary_crossentropy', metrics=['accuracy'])

# --- שלב 4: אימון ---
if not os.path.exists(FINAL_MODEL_DIR): os.makedirs(FINAL_MODEL_DIR)
checkpoint_path = os.path.join(FINAL_MODEL_DIR, 'audio_quality_ultimate.keras')

callbacks_list = [
    callbacks.ModelCheckpoint(checkpoint_path, monitor='val_accuracy', save_best_only=True, verbose=1),
    callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, verbose=1),
    callbacks.EarlyStopping(monitor='val_loss', patience=8, restore_best_weights=True)
]

print("\n--- Starting Training ---")
history = model.fit(X_train, y_train, epochs=EPOCHS, batch_size=BATCH_SIZE, validation_data=(X_test, y_test), callbacks=callbacks_list)

# --- שלב 5: המרה ושמירה ---
print("\n--- Converting to TFLite ---")
best_model = models.load_model(checkpoint_path)
converter = tf.lite.TFLiteConverter.from_keras_model(best_model)
tflite_model = converter.convert()

tflite_path = os.path.join(FINAL_MODEL_DIR, 'audio_quality.tflite')
with open(tflite_path, 'wb') as f:
    f.write(tflite_model)

# מחיקת הקובץ הכבד הזמני
if os.path.exists(checkpoint_path): os.remove(checkpoint_path)

print(f"--- SUCCESS! Ultimate Model saved to: {tflite_path} ---")
print(f"Final Accuracy: {max(history.history['val_accuracy'])*100:.2f}%")