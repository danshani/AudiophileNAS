#!/usr/bin/env python3
"""
Example usage of the metadata completion functionality.
"""

import os
import sys
import logging

# Add the parent directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from metadata import MetadataCompleter, MetadataExtractor, MetadataWriter

def setup_logging():
    """Setup basic logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def example_extract_metadata():
    """Example: Extract metadata from an audio file."""
    print("=== Example: Extract Metadata ===")
    
    extractor = MetadataExtractor()
    
    # Replace with actual audio file path
    audio_file = "path/to/your/audio/file.flac"
    
    if os.path.exists(audio_file):
        metadata = extractor.extract_metadata(audio_file)
        print(f"Extracted metadata: {metadata}")
        
        missing_fields = extractor.get_missing_metadata_fields(metadata)
        print(f"Missing fields: {missing_fields}")
    else:
        print(f"Audio file not found: {audio_file}")

def example_complete_metadata():
    """Example: Complete metadata using MusicBrainz."""
    print("\n=== Example: Complete Metadata ===")
    
    completer = MetadataCompleter()
    
    # Replace with actual audio file path
    audio_file = "path/to/your/audio/file.flac"
    
    if os.path.exists(audio_file):
        try:
            completed_metadata = completer.complete_metadata(audio_file)
            print(f"Completed metadata: {completed_metadata}")
        except Exception as e:
            print(f"Error completing metadata: {e}")
    else:
        print(f"Audio file not found: {audio_file}")

def example_write_metadata():
    """Example: Write metadata to an audio file."""
    print("\n=== Example: Write Metadata ===")
    
    writer = MetadataWriter()
    
    # Example metadata to write
    example_metadata = {
        'title': 'Example Song',
        'artist': 'Example Artist',
        'album': 'Example Album',
        'date': '2023',
        'genre': 'Rock',
        'track_number': '1'
    }
    
    # Replace with actual audio file path
    audio_file = "path/to/your/audio/file.flac"
    
    if os.path.exists(audio_file):
        try:
            success = writer.write_metadata(audio_file, example_metadata, backup=True)
            if success:
                print(f"Metadata written successfully to: {audio_file}")
            else:
                print(f"Failed to write metadata to: {audio_file}")
        except Exception as e:
            print(f"Error writing metadata: {e}")
    else:
        print(f"Audio file not found: {audio_file}")

def example_batch_processing():
    """Example: Process multiple files at once."""
    print("\n=== Example: Batch Processing ===")
    
    completer = MetadataCompleter()
    writer = MetadataWriter()
    
    # Replace with actual audio file paths
    audio_files = [
        "path/to/file1.flac",
        "path/to/file2.mp3",
        "path/to/file3.m4a"
    ]
    
    # Filter existing files
    existing_files = [f for f in audio_files if os.path.exists(f)]
    
    if existing_files:
        try:
            # Complete metadata for all files
            results = completer.batch_complete_metadata(existing_files)
            
            # Write metadata back to files
            write_results = writer.batch_write_metadata(results, backup=True)
            
            # Print summary
            print("Batch processing results:")
            for file_path in existing_files:
                completed = file_path in results and 'error' not in results[file_path]
                written = write_results.get(file_path, False)
                print(f"  {os.path.basename(file_path)}: Completed={completed}, Written={written}")
                
        except Exception as e:
            print(f"Error in batch processing: {e}")
    else:
        print("No existing audio files found for batch processing")

def main():
    """Run all examples."""
    setup_logging()
    
    print("Metadata Completion Examples")
    print("=" * 50)
    
    # Note: These examples require actual audio files to work
    print("Note: Replace file paths with actual audio files to run these examples")
    
    example_extract_metadata()
    example_complete_metadata()
    example_write_metadata()
    example_batch_processing()
    
    print("\n=== Configuration Information ===")
    from metadata.config import get_config
    config = get_config()
    print(f"MusicBrainz API URL: {config['musicbrainz']['base_url']}")
    print(f"Rate limit: {config['musicbrainz']['rate_limit']} requests/second")
    print(f"Required metadata fields: {config['metadata']['required_fields']}")
    
    print("\n=== CLI Usage Example ===")
    print("To use the command-line interface:")
    print("python metadata_cli.py /path/to/audio/files --write --verbose")
    print("python metadata_cli.py file1.flac file2.mp3 --output results.json")
    print("python metadata_cli.py /music/directory --dry-run")

if __name__ == '__main__':
    main()