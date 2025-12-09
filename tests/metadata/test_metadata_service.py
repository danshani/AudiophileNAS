import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
METADATA_ROOT = PROJECT_ROOT / "features" / "audio-repair"
if str(METADATA_ROOT) not in sys.path:
    sys.path.insert(0, str(METADATA_ROOT))

from metadata.core.models import AudioMetadata, MetadataSearchResult, ProcessingResult
from metadata.services.metadata_service import MetadataService


class StubFileService:
    def __init__(self):
        self.write_calls = 0

    def extract_metadata(self, file_path: Path) -> AudioMetadata:
        return AudioMetadata(
            title=None,
            artist=None,
            album=None,
            track_number=None,
            genre=None,
            date=None,
            source="embedded",
        )

    def parse_filename(self, file_path: Path) -> AudioMetadata:
        return AudioMetadata(
            title="Filename Title",
            artist="Filename Artist",
            album=None,
            track_number="02",
            source="filename",
        )

    def write_metadata(self, file_path: Path, metadata: AudioMetadata) -> ProcessingResult:
        self.write_calls += 1
        return ProcessingResult(success=True, metadata=metadata)


class StubMusicBrainzService:
    def search_metadata(self, metadata: AudioMetadata):
        candidate = AudioMetadata(
            title="MB Title",
            artist="MB Artist",
            album="MB Album",
            genre="Rock",
            date="2020",
            track_number="01",
            source="musicbrainz",
        )
        return [MetadataSearchResult(metadata=candidate, confidence_score=0.92, source="musicbrainz")]


def test_process_file_completes_metadata_and_writes():
    file_service = StubFileService()
    music_service = StubMusicBrainzService()
    service = MetadataService(file_service=file_service, musicbrainz_service=music_service)

    result = service.process_file(Path("dummy.flac"), write_metadata=True)

    assert result.success is True
    assert result.metadata.title == "MB Title"
    assert result.metadata.artist == "MB Artist"
    assert result.metadata.album == "MB Album"
    assert result.metadata.genre == "Rock"
    assert result.metadata.track_number == "01"
    assert result.metadata.source.endswith("musicbrainz")
    assert file_service.write_calls == 1
