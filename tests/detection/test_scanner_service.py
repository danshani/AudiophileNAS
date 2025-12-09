import importlib.util
import sys
import types
from pathlib import Path

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCANNER_PATH = PROJECT_ROOT / "features" / "audio-repair" / "detection" / "scanner_service.py"


def load_scanner(monkeypatch):
    class FakeInterpreter:
        def __init__(self, model_path=None):
            self.model_path = model_path
            self.stored = None

        def allocate_tensors(self):
            return None

        def get_input_details(self):
            return [{"index": 0}]

        def get_output_details(self):
            return [{"index": 0}]

        def set_tensor(self, index, value):
            self.stored = value

        def invoke(self):
            return None

        def get_tensor(self, index):
            return np.array([[0.25]], dtype=np.float32)

    fake_tflite_mod = types.SimpleNamespace(Interpreter=FakeInterpreter)
    monkeypatch.setitem(sys.modules, "tflite_runtime.interpreter", fake_tflite_mod)
    monkeypatch.setitem(sys.modules, "tensorflow.lite", fake_tflite_mod)

    spec = importlib.util.spec_from_file_location("scanner_under_test", SCANNER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_audio_predictor_predict(monkeypatch, tmp_path):
    scanner = load_scanner(monkeypatch)

    monkeypatch.setattr(scanner.librosa, "load", lambda path, sr, duration: (np.zeros(int(sr * duration)), sr))

    predictor = scanner.AudioPredictor(tmp_path / "model.tflite")
    score = predictor.predict(tmp_path / "sample.wav")

    assert 0 <= score <= 1


def test_new_file_handler_clean_file(monkeypatch, tmp_path):
    scanner = load_scanner(monkeypatch)

    class FakeDB:
        def __init__(self):
            self.scanned = set()
            self.added = []
            self.updated = []

        def is_scanned(self, filepath):
            return filepath in self.scanned

        def add_result(self, filepath, is_clean, score):
            self.added.append((filepath, is_clean, score))
            self.scanned.add(filepath)

        def update_status(self, filepath, col, status):
            self.updated.append((filepath, col, status))

    class CleanPredictor:
        def predict(self, filepath):
            return 0.1

    monkeypatch.setattr(scanner, "run_metadata_repair", lambda fp: True)

    fake_db = FakeDB()
    handler = scanner.NewFileHandler(fake_db, CleanPredictor(), repair_service=None)

    audio_file = tmp_path / "clean.flac"
    audio_file.write_bytes(b"audio")

    handler.process_file(str(audio_file))

    assert fake_db.added[0][1] is True  # marked clean
    assert any(col == "metadata_status" and status == "COMPLETED" for _, col, status in fake_db.updated)


def test_new_file_handler_dirty_file_with_quarantine(monkeypatch, tmp_path):
    scanner = load_scanner(monkeypatch)

    monkeypatch.setattr(scanner, "QUARANTINE_DIR", str(tmp_path / "quarantine"))
    monkeypatch.setattr(scanner.shutil, "move", lambda src, dest: dest)

    class FakeDB:
        def __init__(self):
            self.added = []
            self.updated = []

        def is_scanned(self, filepath):
            return False

        def add_result(self, filepath, is_clean, score):
            self.added.append((filepath, is_clean, score))

        def update_status(self, filepath, col, status):
            self.updated.append((filepath, col, status))

    class DirtyPredictor:
        def predict(self, filepath):
            return 0.9

    class FakeRepairService:
        def __init__(self, output_path):
            self.output_path = output_path
            self.calls = []

        def repair_file(self, filepath):
            self.calls.append(filepath)
            repaired = Path(self.output_path) / Path(filepath).name
            repaired.write_text("fixed")
            return str(repaired)

    repair_service = FakeRepairService(tmp_path / "downloads")
    monkeypatch.setattr(scanner, "run_metadata_repair", lambda fp: False)

    fake_db = FakeDB()
    handler = scanner.NewFileHandler(fake_db, DirtyPredictor(), repair_service=repair_service)

    dirty_file = tmp_path / "noisy.wav"
    dirty_file.write_bytes(b"audio")

    handler.process_file(str(dirty_file))

    assert fake_db.added[0][1] is False  # marked dirty
    assert any(col == "repair_status" and status == "NEEDED" for _, col, status in fake_db.updated)
    assert repair_service.calls  # repair attempted
    assert any(status == "FIXED" for _, col, status in fake_db.updated if col == "repair_status")
