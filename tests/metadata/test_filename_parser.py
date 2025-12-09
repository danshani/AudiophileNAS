import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
METADATA_ROOT = PROJECT_ROOT / "features" / "audio-repair"
if str(METADATA_ROOT) not in sys.path:
    sys.path.insert(0, str(METADATA_ROOT))

from metadata.parsers.filename_parser import FilenameParser


def test_parse_track_artist_and_title():
    parser = FilenameParser()
    metadata = parser.parse("01 Artist - Track Name.flac")

    assert metadata is not None
    assert metadata.track_number == "01"
    assert metadata.artist == "Artist"
    assert metadata.title == "Track Name"


def test_parse_with_album_and_encoding_fix():
    parser = FilenameParser()
    corrupted_name = "03 Günther - HГ¤user (Greatest Hits).mp3"
    metadata = parser.parse(corrupted_name)

    assert metadata is not None
    assert metadata.track_number == "03"
    assert metadata.artist == "Günther"
    assert metadata.title == "Häuser"
    assert metadata.album == "Greatest Hits"
