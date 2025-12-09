import sys
import types
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
METADATA_ROOT = PROJECT_ROOT / "features" / "audio-repair"
if str(METADATA_ROOT) not in sys.path:
    sys.path.insert(0, str(METADATA_ROOT))

from metadata.core.models import AudioMetadata
from metadata.writers import mutagen_writer as mw


def test_write_metadata_sets_tags(monkeypatch, tmp_path):
    tmp_file = tmp_path / "track.mp3"
    tmp_file.write_bytes(b"fake mp3")

    class DummyAudio(dict):
        def __init__(self):
            super().__init__()
            self.saved = False

        def save(self):
            self.saved = True

    dummy_audio = DummyAudio()

    mw.MUTAGEN_AVAILABLE = True
    mw.mutagen = types.SimpleNamespace(File=lambda path: dummy_audio)

    writer = mw.MutagenWriter()
    monkeypatch.setattr(writer, "_detect_format", lambda audio: "mp3")

    metadata = AudioMetadata(
        title="Song",
        artist="Artist",
        album="Album",
        track_number="7",
        musicbrainz_recording_id="rec-1",
    )

    result = writer.write_metadata(tmp_file, metadata, create_backup=False)

    assert result.success is True
    assert dummy_audio["TIT2"] == ["Song"]
    assert dummy_audio["TPE1"] == ["Artist"]
    assert dummy_audio["TALB"] == ["Album"]
    assert dummy_audio["TRCK"] == ["7"]
    assert dummy_audio["MUSICBRAINZ_TRACKID"] == ["rec-1"]
    assert dummy_audio.saved is True
