"""
Audio File Repair Module - Attempts to repair corrupted audio files
"""

import os
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
import config

class AudioRepairer:
    def __init__(self):
        self.repair_log = []
    
    def repair_file(self, file_path, backup=True):
        """Attempt to repair a single audio file"""
        file_path = Path(file_path)
        
        print(f"\nRepairing: {file_path.name}")
        
        # Create backup if requested
        if backup and config.BACKUP_BEFORE_REPAIR:
            backup_path = self.create_backup(file_path)
            if not backup_path:
                return False
        
        # Try repair methods
        success = self.repair_with_ffmpeg(file_path)
        
        if success:
            print(f"SUCCESS: {file_path.name} repaired")
            self.repair_log.append({
                'file': str(file_path),
                'status': 'success',
                'timestamp': datetime.now().isoformat()
            })
            return True
        else:
            print(f"FAILED: Could not repair {file_path.name}")
            self.repair_log.append({
                'file': str(file_path),
                'status': 'failed',
                'timestamp': datetime.now().isoformat()
            })
            return False
    
    def create_backup(self, file_path):
        """Create backup of original file"""
        try:
            backup_dir = file_path.parent / 'backups'
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = backup_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"
            
            shutil.copy2(file_path, backup_path)
            print(f"Backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            print(f"ERROR: Could not create backup - {e}")
            return None
    
    def repair_with_ffmpeg(self, file_path):
        """Attempt repair using FFmpeg re-encoding"""
        try:
            temp_output = file_path.parent / f"{file_path.stem}_repaired{file_path.suffix}"
            
            # FFmpeg command to re-encode with error correction
            cmd = [
                'ffmpeg',
                '-err_detect', 'ignore_err',
                '-i', str(file_path),
                '-c:a', 'copy',
                '-y',
                str(temp_output)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=config.FFMPEG_TIMEOUT
            )
            
            if result.returncode == 0 and temp_output.exists():
                # Replace original with repaired file
                file_path.unlink()
                temp_output.rename(file_path)
                return True
            else:
                # Cleanup failed attempt
                if temp_output.exists():
                    temp_output.unlink()
                return False
                
        except Exception as e:
            print(f"ERROR during repair: {e}")
            return False
    
    def repair_batch(self, corrupted_files):
        """Repair multiple files from scan results"""
        print(f"\nStarting batch repair of {len(corrupted_files)} files...")
        
        success_count = 0
        failed_count = 0
        
        for file_info in corrupted_files:
            file_path = file_info['file']
            if self.repair_file(file_path):
                success_count += 1
            else:
                failed_count += 1
        
        print("\n" + "="*50)
        print("REPAIR SUMMARY")
        print("="*50)
        print(f"Total files: {len(corrupted_files)}")
        print(f"Successfully repaired: {success_count}")
        print(f"Failed: {failed_count}")
        
        return self.repair_log


def main():
    """Test repair on a specific file"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 repair.py <file_path>")
        sys.exit(1)
    
    repairer = AudioRepairer()
    success = repairer.repair_file(sys.argv[1], backup=True)
    
    if success:
        print("\nFile repaired successfully!")
    else:
        print("\nRepair failed.")


if __name__ == '__main__':
    main()
