"""
AudiophileNAS - Main entry point

A comprehensive audio metadata processing system.
"""

import sys
from pathlib import Path

def main():
    """Main entry point for AudiophileNAS."""
    
    print("🎵 AudiophileNAS - Audio Metadata Processing System")
    print("=" * 50)
    
    # Check if metadata system is available
    metadata_path = Path("features/audio-repair/metadata")
    if not metadata_path.exists():
        print("❌ Metadata system not found!")
        print(f"Expected path: {metadata_path.absolute()}")
        return 1
    
    print("✅ Metadata system found")
    print(f"📁 Location: {metadata_path.absolute()}")
    print()
    
    print("Available commands:")
    print("1. Process metadata:")
    print("   cd features/audio-repair/metadata")
    print("   python -m cli.commands ../test_audio --verbose")
    print()
    print("2. Python usage:")
    print("   from features.audio_repair.metadata import MetadataService")
    print("   service = MetadataService()")
    print()
    print("3. Documentation:")
    print("   - System README: features/audio-repair/metadata/README.md")
    print("   - Usage examples: docs/examples/metadata_usage_examples.py")
    print()
    
    # Test import
    try:
        sys.path.insert(0, str(Path("features").absolute()))
        from audio_repair.metadata import MetadataService
        print("✅ System import successful - Ready to use!")
    except ImportError as e:
        print(f"⚠️  Import warning: {e}")
        print("Make sure to install dependencies: pip install -r requirements.txt")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())