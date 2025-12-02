"""
Example usage of the refactored metadata processing system.

This demonstrates the new clean architecture with proper separation of concerns.
"""

from pathlib import Path
from metadata import MetadataService, FileService, MusicBrainzService
from metadata.core.models import AudioMetadata


def main():
    """Example of using the new metadata processing architecture."""
    
    # Initialize services
    metadata_service = MetadataService()
    
    # Process a single file
    audio_file = Path("../test_audio/01 Shiwa 2000_-_Jazz Zoo.flac")
    
    if audio_file.exists():
        print(f"Processing: {audio_file.name}")
        
        # Process without writing
        result = metadata_service.process_file(audio_file, write_metadata=False)
        
        if result.success:
            print(f"✅ Processing successful!")
            print(f"Title: {result.metadata.title}")
            print(f"Artist: {result.metadata.artist}")
            print(f"Album: {result.metadata.album}")
            print(f"Genre: {result.metadata.genre}")
            print(f"Confidence: {result.metadata.confidence:.2f}")
            print(f"Source: {result.metadata.source}")
            print(f"Processing time: {result.processing_time:.2f}s")
            
            if result.warnings:
                print("Warnings:")
                for warning in result.warnings:
                    print(f"  - {warning}")
        else:
            print(f"❌ Processing failed: {result.error}")
    
    # Batch processing example
    print("\n" + "="*50)
    print("Batch Processing Example")
    print("="*50)
    
    test_dir = Path("../test_audio")
    if test_dir.exists():
        # Find audio files
        file_service = FileService()
        audio_files = file_service.find_audio_files(test_dir)
        
        print(f"Found {len(audio_files)} audio files")
        
        # Process first 3 files
        sample_files = audio_files[:3]
        results = metadata_service.process_batch(sample_files, write_metadata=False)
        
        for file_path, result in results.items():
            filename = Path(file_path).name
            if result.success:
                print(f"✅ {filename}: {result.metadata.title} - {result.metadata.artist}")
            else:
                print(f"❌ {filename}: {result.error}")


def example_with_custom_services():
    """Example of using the system with custom service configurations."""
    
    # Custom MusicBrainz configuration
    mb_config = {
        'base_url': 'https://musicbrainz.org/ws/2/',
        'user_agent': 'MyCustomApp/1.0',
        'rate_limit': 0.5,  # Slower rate
        'timeout': 15,
        'search_threshold': 0.9,  # Higher threshold
        'max_search_results': 5
    }
    
    # Initialize with custom services
    musicbrainz_service = MusicBrainzService(mb_config)
    file_service = FileService()
    metadata_service = MetadataService(file_service, musicbrainz_service)
    
    print("Using custom configured services...")
    # Use the service as normal
    

def example_direct_service_usage():
    """Example of using services directly for more control."""
    
    file_service = FileService()
    musicbrainz_service = MusicBrainzService()
    
    audio_file = Path("../test_audio/01 Shiwa 2000_-_Jazz Zoo.flac")
    
    if audio_file.exists():
        # Step 1: Extract metadata
        metadata = file_service.extract_metadata(audio_file)
        print(f"Extracted metadata: {metadata.title} - {metadata.artist}")
        
        # Step 2: Search for additional info
        if not metadata.genre:
            search_results = musicbrainz_service.search_metadata(metadata)
            if search_results:
                best_match = search_results[0]
                print(f"Found match: {best_match.metadata.title} (score: {best_match.confidence_score})")
                
                # Step 3: Merge metadata
                completed_metadata = metadata.merge(best_match.metadata)
                print(f"Completed metadata: Genre = {completed_metadata.genre}")
                
                # Step 4: Write back (optional)
                # write_result = file_service.write_metadata(audio_file, completed_metadata)


if __name__ == "__main__":
    main()
    print("\n" + "="*50)
    example_direct_service_usage()