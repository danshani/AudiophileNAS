"""
Audio Repair Module Configuration
"""

# Supported audio formats
SUPPORTED_FORMATS = ['.flac', '.wav', '.mp3', '.m4a', '.aac', '.ogg', '.opus', '.dsf', '.dff', '.ape', '.alac']


# Scan settings
MAX_FILE_SIZE_MB = 500
SCAN_THREADS = 4

# FFmpeg check timeout (seconds)
FFMPEG_TIMEOUT = 30

# Repair settings
AUTO_REPAIR = False
BACKUP_BEFORE_REPAIR = True

# Logging
LOG_LEVEL = 'INFO'
LOG_FILE = 'logs/audio_repair.log'
