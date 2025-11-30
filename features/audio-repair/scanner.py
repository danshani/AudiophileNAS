"""
Audio File Scanner - Detects corrupted audio files
"""

import os
import subprocess
import json
from pathlib import Path
from datetime import datetime
import config

class AudioScanner:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.results = {
            'total_files': 0,
            'scanned': 0,
            'corrupted': [],
            'healthy': [],
            'errors': []
        }
    
    def scan(self):
        print(f"Scanning: {self.directory}")
        
        for file_path in self.directory.rglob('*'):
            if file_path.suffix.lower() in config.SUPPORTED_FORMATS:
                self.results['total_files'] += 1
                self.check_file(file_path)
        
        return self.results
    
    def check_file(self, file_path):
        try:
            cmd = [
                'ffmpeg',
                '-v', 'error',
                '-i', str(file_path),
                '-f', 'null',
                '-'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=config.FFMPEG_TIMEOUT
            )
            
            self.results['scanned'] += 1
            
            if result.returncode != 0 or result.stderr:
                self.results['corrupted'].append({
                    'file': str(file_path),
                    'error': result.stderr.strip(),
                    'size_mb': file_path.stat().st_size / (1024*1024)
                })
                print(f"CORRUPTED: {file_path.name}")
            else:
                self.results['healthy'].append(str(file_path))
                print(f"OK: {file_path.name}")
                
        except subprocess.TimeoutExpired:
            self.results['errors'].append({
                'file': str(file_path),
                'error': 'Timeout during scan'
            })
            print(f"TIMEOUT: {file_path.name}")
            
        except Exception as e:
            self.results['errors'].append({
                'file': str(file_path),
                'error': str(e)
            })
            print(f"ERROR: {file_path.name} - {e}")
    
    def generate_report(self, output_file='scan_report.json'):
        report = {
            'scan_date': datetime.now().isoformat(),
            'directory': str(self.directory),
            'summary': {
                'total_files': self.results['total_files'],
                'scanned': self.results['scanned'],
                'corrupted_count': len(self.results['corrupted']),
                'healthy_count': len(self.results['healthy']),
                'errors_count': len(self.results['errors'])
            },
            'corrupted_files': self.results['corrupted'],
            'errors': self.results['errors']
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Report saved: {output_file}")
        return report


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 scanner.py <directory>")
        sys.exit(1)
    
    scanner = AudioScanner(sys.argv[1])
    results = scanner.scan()
    
    print("\n" + "="*50)
    print("SCAN RESULTS")
    print("="*50)
    print(f"Total files found: {results['total_files']}")
    print(f"Successfully scanned: {results['scanned']}")
    print(f"Healthy: {len(results['healthy'])}")
    print(f"Corrupted: {len(results['corrupted'])}")
    print(f"Errors: {len(results['errors'])}")
    
    scanner.generate_report()


if __name__ == '__main__':
    main()
