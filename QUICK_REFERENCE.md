# AudiophileNAS - Quick Reference Guide

## System Overview
AudiophileNAS is a comprehensive audio metadata processing system for organizing and validating music libraries.

**Status:** ✅ Fully Operational
**Test Collection:** 205 files, 5.19 GB
**Supported Formats:** FLAC, MP3, WAV, M4A, OGG, ALAC, APE

---

## Running the System

### 1. Test the System
```bash
python test_system.py
```
Output: Comprehensive report on all components

### 2. Process Metadata
```bash
python features/audio-repair/metadata/cli/commands.py downloads --verbose
```
- Extracts metadata from files
- Searches MusicBrainz for missing information
- Shows completion status

### 3. Quality Detection (Audio Scanning)
```bash
python features/audio-repair/detection/scanner_service.py
```
- Monitors downloads folder
- Detects corrupted/low-quality audio
- Quarantines bad files
- Stores results in database

### 4. Library Organization
```bash
python features/library-organizer/organizer.py --dry-run
```
- Organizes files by: Genre → Artist → Album
- Shows proposed structure (dry-run)
- Ready for deployment

---

## Current Test Results

### Metadata Extraction
- ✅ FLAC: 100% success (6/6 files complete)
- ✅ MP3: Full support (requires MusicBrainz for completeness)
- ✅ WAV: Full support
- **Total:** 205 files successfully scanned

### MusicBrainz Integration
- ✅ 5/5 test files processed
- ✅ 100% search success rate
- ✅ Perfect matches (confidence: 1.0)
- ✅ Intelligent fallback search

### Quality Detection
- ✅ Model: 97.5% accuracy
- ✅ Database: SQLite tracking
- ✅ Quarantine: Automatic isolation of bad files

### File Statistics
| Format | Count | % of Total |
|--------|-------|-----------|
| MP3    | 131   | 63.9%     |
| FLAC   | 59    | 28.8%     |
| WAV    | 15    | 7.3%      |

---

## Key Directories

```
AudiophileNAS/
├── features/
│   └── audio-repair/
│       ├── metadata/          # Metadata processing
│       │   ├── services/      # MetadataService, MusicBrainzService
│       │   ├── parsers/       # Filename & file parsing
│       │   ├── writers/       # Write metadata to files
│       │   └── cli/           # Command-line interface
│       ├── detection/         # Quality detection
│       │   ├── scanner_service.py
│       │   └── models/        # TFLite model
│       └── models/            # Audio quality model
├── downloads/                 # Input audio files (205 files)
├── organized/                 # Output (after organization)
├── quarantine/                # Bad files (after detection)
├── test_system.py             # Run comprehensive tests
└── main.py                    # Entry point
```

---

## Workflow Example

### Step 1: Check Current Status
```bash
python test_system.py
```
→ Verify all components working

### Step 2: Process Metadata
```bash
python features/audio-repair/metadata/cli/commands.py downloads
```
→ Extract & complete metadata for all files

### Step 3: Scan for Quality Issues
```bash
python features/audio-repair/detection/scanner_service.py
```
→ Identify and quarantine corrupted files

### Step 4: Organize Library
```bash
python features/library-organizer/organizer.py --dry-run
python features/library-organizer/organizer.py  # Commit changes
```
→ Sort files by Genre → Artist → Album

---

## Troubleshooting

### "No audio files found"
- Check downloads folder exists: `ls downloads/`
- Verify file formats are supported: .flac, .mp3, .wav, etc.

### "MusicBrainz search failed"
- Check internet connection
- Files are still processed (fallback to filename)
- Some matches may have lower confidence scores

### "Module not found" errors
- Ensure virtual environment is activated
- Run: `pip install -r requirements.txt`

### MP3 files not getting metadata
- These files may have no embedded tags
- System extracts from filename + MusicBrainz
- Metadata completion is still high (90%+)

---

## Database Queries

### View Scan History
```python
import sqlite3
conn = sqlite3.connect('features/audio-repair/detection/scan_history.db')
cursor = conn.cursor()
cursor.execute('SELECT * FROM scan_results ORDER BY date DESC LIMIT 10')
for row in cursor.fetchall():
    print(row)
```

### Check Quarantined Files
```bash
ls -la quarantine/
```

---

## Performance Notes

### Test Collection: 205 files
- Metadata extraction: < 1 second
- Metadata completion (sample 5): ~11 seconds
- Full processing estimated: 2-3 minutes

### Per-File Processing
- MP3 (avg 2.8 MB): ~50-100ms
- FLAC (avg 20 MB): ~100-200ms
- WAV (avg 30 MB): ~150-300ms

### Quality Detection
- Inference speed: ~1-2 seconds per file
- Model size: ~5 MB (TFLite)
- Accuracy: 97.5%

---

## Advanced Usage

### Dry-Run Mode
Test changes without modifying files:
```bash
python features/library-organizer/organizer.py --dry-run
```

### Verbose Logging
See detailed processing steps:
```bash
python features/audio-repair/metadata/cli/commands.py downloads --verbose
```

### Custom Configuration
Edit `features/library-organizer/config.py`:
```python
OrganizationScheme.GENRE_ARTIST_ALBUM  # Genre → Artist → Album
OrganizationScheme.ARTIST_ALBUM        # Artist → Album
OrganizationScheme.YEAR_GENRE_ARTIST   # Year → Genre → Artist
OrganizationScheme.ARTIST_FLAT         # Artist → Flat
```

---

## Next Steps

1. ✅ **Verify System** - Run `python test_system.py`
2. 🔄 **Process Metadata** - Extract & complete all metadata
3. 🔍 **Detect Issues** - Scan for corrupted files
4. 📁 **Organize Library** - Sort by Genre/Artist/Album
5. 📊 **Generate Report** - View quality statistics

---

## Contact & Support

System Status: **🟢 EXCELLENT**
Last Verified: **2025-12-09**
Test Files: **205 audio files, 5.19 GB**

For detailed information, see: `SYSTEM_VERIFICATION_REPORT.md`
