#!/usr/bin/env python3
"""
Audio Repair CLI - Complete scan and repair workflow
"""

import sys
import argparse
from scanner import AudioScanner
from repair import AudioRepairer

def main():
    parser = argparse.ArgumentParser(description='Audio File Repair System')
    parser.add_argument('directory', help='Directory to scan')
    parser.add_argument('--repair', action='store_true', help='Auto-repair corrupted files')
    parser.add_argument('--no-backup', action='store_true', help='Skip backup before repair')
    
    args = parser.parse_args()
    
    # Step 1: Scan
    print("="*60)
    print("AUDIO REPAIR SYSTEM - SCAN & REPAIR")
    print("="*60)
    
    scanner = AudioScanner(args.directory)
    results = scanner.scan()
    scanner.generate_report()
    
    # Step 2: Repair if requested
    if args.repair and results['corrupted']:
        print("\n" + "="*60)
        print("STARTING REPAIR PROCESS")
        print("="*60)
        
        repairer = AudioRepairer()
        repair_log = repairer.repair_batch(results['corrupted'])
        
        print("\nRepair complete!")
    elif results['corrupted']:
        print(f"\nFound {len(results['corrupted'])} corrupted files.")
        print("Run with --repair flag to attempt automatic repair.")
    else:
        print("\nAll files are healthy!")

if __name__ == '__main__':
    main()
