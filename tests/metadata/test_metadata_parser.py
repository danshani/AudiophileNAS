import sys
import types
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
METADATA_ROOT = PROJECT_ROOT / "features" / "audio-repair"
if str(METADATA_ROOT) not in sys.path:
    sys.path.insert(0, str(METADATA_ROOT))

from metadata.parsers import metadata_parser as mp


def test_extract_metadata_uses_mutagen(monkeypatch, tmp_path):
    tmp_file = tmp_path / "song.flac"
    tmp_file.write_bytes(b"fake flac")

    class DummyInfo:
        length = 123.4
        bitrate = 256000
        sample_rate = 44100
        channels = 2
        bits_per_sample = 16

    class DummyAudio:
        def __init__(self):
            self.info = DummyInfo()
            self._tags = {
                "TITLE": ["Test Title"],
                "ARTIST": ["Test Artist"],
                "ALBUM": ["Test Album"],
                "TRACKNUMBER": ["5"],
            }

        def __contains__(self, key):
            return key in self._tags

        def __getitem__(self, key):
            return self._tags[key]

    dummy_audio = DummyAudio()

    mp.MUTAGEN_AVAILABLE = True
    mp.mutagen = types.SimpleNamespace(File=lambda path: dummy_audio)

    parser = mp.MetadataParser()
    monkeypatch.setattr(parser, "_detect_format", lambda audio: "flac")

    metadata = parser.extract_metadata(tmp_file)

    assert metadata.title == "Test Title"
    assert metadata.artist == "Test Artist"
    assert metadata.album == "Test Album"
    assert metadata.track_number == "5"
    assert metadata.file_info.file_format == "flac"
    assert metadata.file_info.duration == pytest.approx(123.4)
    assert metadata.file_info.sample_rate == 44100
