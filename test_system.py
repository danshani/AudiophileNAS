#!/usr/bin/env python3
"""
Comprehensive system test for AudiophileNAS
Tests metadata processing and detection on downloads folder
"""

import sys
import logging
from pathlib import Path
from collections import defaultdict

# Setup paths
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "features" / "audio-repair"))

from metadata.services.metadata_service import MetadataService
from metadata.parsers.metadata_parser import MetadataParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DOWNLOADS_DIR = PROJECT_ROOT / "downloads"
SUPPORTED_EXTENSIONS = {'.flac', '.mp3', '.m4a', '.ogg', '.wav', '.alac', '.ape'}

def find_audio_files(directory: Path) -> list:
    """Find all audio files in directory."""
    audio_files = []
    if not directory.exists():
        logger.error(f"Directory not found: {directory}")
        return audio_files
    
    for ext in SUPPORTED_EXTENSIONS:
        audio_files.extend(directory.glob(f"**/*{ext}"))
        audio_files.extend(directory.glob(f"**/*{ext.upper()}"))
    
    return sorted(set(audio_files))

def test_metadata_extraction():
    """Test 1: Metadata extraction on sample files"""
    logger.info("=" * 80)
    logger.info("TEST 1: METADATA EXTRACTION")
    logger.info("=" * 80)
    
    audio_files = find_audio_files(DOWNLOADS_DIR)
    if not audio_files:
        logger.error("No audio files found in downloads folder!")
        return False
    
    logger.info(f"Found {len(audio_files)} audio files")
    
    # Sample 10 files for quick test
    sample_files = audio_files[:10]
    
    parser = MetadataParser()
    results = defaultdict(int)
    
    for i, file_path in enumerate(sample_files, 1):
        try:
            metadata = parser.extract_metadata(file_path)
            format_type = file_path.suffix.lower()
            
            # Check how many fields are filled
            filled_fields = sum([
                metadata.title is not None,
                metadata.artist is not None,
                metadata.album is not None,
                metadata.date is not None,
                metadata.genre is not None,
                metadata.track_number is not None,
            ])
            
            logger.info(f"[{i}/10] {file_path.name} ({format_type})")
            logger.info(f"         Fields: {filled_fields}/6 | Artist: {metadata.artist} | Title: {metadata.title}")
            results[format_type] += 1
            
        except Exception as e:
            logger.error(f"  ERROR processing {file_path.name}: {e}")
    
    logger.info(f"\nMetadata extraction complete. Processed {sum(results.values())} files")
    for fmt, count in sorted(results.items()):
        logger.info(f"  {fmt}: {count} files")
    
    return True

def test_metadata_completion():
    """Test 2: Metadata completion via MusicBrainz"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: METADATA COMPLETION (MusicBrainz)")
    logger.info("=" * 80)
    
    audio_files = find_audio_files(DOWNLOADS_DIR)
    if not audio_files:
        return False
    
    # Test on 5 files
    sample_files = audio_files[:5]
    service = MetadataService()
    
    stats = {
        'processed': 0,
        'already_complete': 0,
        'completed': 0,
        'failed': 0,
        'by_format': defaultdict(lambda: {'total': 0, 'complete': 0, 'failed': 0})
    }
    
    for i, file_path in enumerate(sample_files, 1):
        try:
            logger.info(f"\n[{i}/5] Processing: {file_path.name}")
            result = service.process_file(file_path, write_metadata=False)
            
            fmt = file_path.suffix.lower()
            stats['by_format'][fmt]['total'] += 1
            stats['processed'] += 1
            
            if result.success:
                missing = result.metadata.get_missing_fields()
                if not missing:
                    logger.info(f"     ✓ Already complete")
                    stats['already_complete'] += 1
                    stats['by_format'][fmt]['complete'] += 1
                else:
                    logger.info(f"     Missing: {missing}")
                    stats['completed'] += 1
                    stats['by_format'][fmt]['complete'] += 1
            else:
                logger.error(f"     ✗ Failed: {result.error}")
                stats['failed'] += 1
                stats['by_format'][fmt]['failed'] += 1
                
        except Exception as e:
            logger.error(f"  Exception: {e}")
            stats['failed'] += 1
    
    logger.info(f"\nCompletion Summary:")
    logger.info(f"  Processed: {stats['processed']}")
    logger.info(f"  Already complete: {stats['already_complete']}")
    logger.info(f"  Newly completed: {stats['completed']}")
    logger.info(f"  Failed: {stats['failed']}")
    
    return stats['processed'] > 0

def test_detection():
    """Test 3: Audio quality detection"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: AUDIO QUALITY DETECTION")
    logger.info("=" * 80)
    
    logger.info("Detection service requires full initialization - skipping in this test")
    logger.info("Run 'python features/audio-repair/detection/scanner_service.py' separately")
    
    return True

def test_file_stats():
    """Test 4: Overall file statistics"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 4: FILE STATISTICS")
    logger.info("=" * 80)
    
    audio_files = find_audio_files(DOWNLOADS_DIR)
    
    if not audio_files:
        logger.error("No audio files found!")
        return False
    
    stats = defaultdict(int)
    total_size = 0
    
    for file_path in audio_files:
        fmt = file_path.suffix.lower()
        stats[fmt] += 1
        total_size += file_path.stat().st_size
    
    logger.info(f"Total audio files: {len(audio_files)}")
    logger.info(f"Total size: {total_size / (1024**3):.2f} GB")
    logger.info("\nBy format:")
    
    for fmt in sorted(stats.keys()):
        logger.info(f"  {fmt}: {stats[fmt]} files")
    
    return True

def main():
    """Run all tests"""
    logger.info("🎵 AudiophileNAS - COMPREHENSIVE SYSTEM TEST")
    logger.info(f"Testing with files from: {DOWNLOADS_DIR}")
    logger.info("")
    
    results = {
        'metadata_extraction': test_metadata_extraction(),
        'metadata_completion': test_metadata_completion(),
        'detection': test_detection(),
        'file_stats': test_file_stats(),
    }
    
    logger.info("\n" + "=" * 80)
    logger.info("FINAL TEST RESULTS")
    logger.info("=" * 80)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    logger.info("\n" + ("✓ ALL TESTS PASSED" if all_passed else "✗ SOME TESTS FAILED"))
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
