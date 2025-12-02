#!/usr/bin/env python3
"""
CLI tool for metadata completion using MusicBrainz API.
"""

import argparse
import sys
import os
import json
import logging
from typing import List
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.metadata_service import MetadataService
from writers.mutagen_writer import MutagenWriter
from parsers.metadata_parser import MetadataParser

def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def find_audio_files(directory: str, extensions: List[str] = None) -> List[str]:
    """Find audio files in a directory."""
    if extensions is None:
        extensions = ['.flac', '.mp3', '.m4a', '.ogg', '.wav']
    
    audio_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if any(file.lower().endswith(ext) for ext in extensions):
                audio_files.append(os.path.join(root, file))
    
    return audio_files

def main():
    parser = argparse.ArgumentParser(
        description='Complete metadata for audio files using MusicBrainz API'
    )
    parser.add_argument(
        'paths',
        nargs='+',
        help='Audio files or directories to process'
    )
    parser.add_argument(
        '--write',
        action='store_true',
        help='Write completed metadata back to files'
    )
    parser.add_argument(
        '--backup',
        action='store_true',
        default=True,
        help='Create backup files before writing (default: True)'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Do not create backup files'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output JSON file for metadata results'
    )
    parser.add_argument(
        '--extensions',
        nargs='+',
        default=['.flac', '.mp3', '.m4a', '.ogg', '.wav'],
        help='Audio file extensions to process (default: .flac .mp3 .m4a .ogg .wav)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit the number of files to process for testing'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Handle backup settings
    create_backup = args.backup and not args.no_backup
    
    # Collect audio files
    audio_files = []
    for path in args.paths:
        if os.path.isfile(path):
            if any(path.lower().endswith(ext) for ext in args.extensions):
                audio_files.append(path)
            else:
                logger.warning(f"Skipping non-audio file: {path}")
        elif os.path.isdir(path):
            found_files = find_audio_files(path, args.extensions)
            audio_files.extend(found_files)
            logger.info(f"Found {len(found_files)} audio files in {path}")
        else:
            logger.error(f"Path not found: {path}")
    
    if not audio_files:
        logger.error("No audio files found to process")
        sys.exit(1)
    
    # Apply limit if specified
    if args.limit and args.limit < len(audio_files):
        audio_files = audio_files[:args.limit]
        logger.info(f"Limited to {args.limit} files for testing")
    
    logger.info(f"Processing {len(audio_files)} audio files")
    
    try:
        # Initialize components
        metadata_service = MetadataService()
        metadata_parser = MetadataParser()
        writer = MutagenWriter() if args.write else None
        
        results = {}
        
        for i, file_path in enumerate(audio_files, 1):
            logger.info(f"Processing {i}/{len(audio_files)}: {os.path.basename(file_path)}")
            
            if args.dry_run:
                # For dry run, just extract current metadata and show missing fields
                current_metadata = metadata_parser.extract_metadata(file_path)
                missing_fields = []  # TODO: implement missing field detection
                
                results[file_path] = {
                    'current_metadata': current_metadata,
                    'missing_fields': missing_fields,
                    'status': 'dry_run'
                }
                
                if missing_fields:
                    print(f"\n{file_path}:")
                    print(f"  Missing fields: {', '.join(missing_fields)}")
                    print(f"  Current metadata: {current_metadata}")
                else:
                    print(f"\n{file_path}: Metadata already complete")
                
            else:
                # Complete metadata
                try:
                    completed_metadata = metadata_service.process_file(file_path)
                    results[file_path] = completed_metadata
                    
                    # Write metadata if requested
                    if args.write and writer:
                        # Convert to format expected by writer
                        success = writer.write_metadata(file_path, completed_metadata, create_backup)
                        results[file_path]['write_success'] = success
                        
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    results[file_path] = {'error': str(e)}
        
        # Save results to JSON if requested
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"Results saved to: {args.output}")
        
        # Print summary
        if not args.dry_run:
            completed_count = 0
            written_count = 0
            
            for file_path, metadata in results.items():
                if 'error' not in metadata:
                    completed_count += 1
                if metadata.get('write_success'):
                    written_count += 1
            
            print(f"\nSummary:")
            print(f"  Files processed: {len(audio_files)}")
            print(f"  Metadata completed: {completed_count}")
            if args.write:
                print(f"  Files written: {written_count}")
        
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()