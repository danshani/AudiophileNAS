import os
import shutil
import logging
from pathlib import Path
from typing import Optional
from .tools.denoiser import AudioDenoiser

class RepairService:
    """
    Orchestrates the audio repair pipeline.
    It manages the flow of a file from quarantine -> repair tools -> output.
    """
    
    def __init__(self, quarantine_dir: str, output_dir: str):
        """
        Initialize the repair service.
        
        Args:
            quarantine_dir: Directory containing bad files.
            output_dir: Directory where fixed files will be moved (usually back to 'downloads').
        """
        self.quarantine_dir = quarantine_dir
        self.output_dir = output_dir
        self.logger = logging.getLogger(__name__)
        
        # Initialize repair tools
        try:
            self.denoiser = AudioDenoiser()
        except EnvironmentError as e:
            self.logger.critical(f"Failed to initialize repair tools: {e}")
            self.denoiser = None
        
        # Create a hidden workspace directory for processing
        self.temp_work_dir = os.path.join(os.path.dirname(quarantine_dir), "repair_workspace")
        os.makedirs(self.temp_work_dir, exist_ok=True)

    def repair_file(self, file_path: str) -> Optional[str]:
        """
        Main entry point for repairing a specific file.
        
        Args:
            file_path: Full path to the damaged file.
            
        Returns:
            str: Path to the successfully repaired file in the output directory.
            None: If repair failed.
        """
        if not self.denoiser:
            self.logger.error("Repair skipped: Denoiser tool not available.")
            return None

        filename = os.path.basename(file_path)
        self.logger.info(f"🔧 Starting repair pipeline for: {filename}")
        
        # 1. Prepare Workspace Path
        # We enforce .flac extension for the output to preserve quality during processing
        base_name = os.path.splitext(filename)[0]
        work_filename = f"repaired_{base_name}.flac"
        work_file_path = os.path.join(self.temp_work_dir, work_filename)
            
        repair_success = False
        
        # --- Step 1: Noise Reduction ---
        # Apply the denoiser tool. This reads the source and writes to work_file_path.
        if self.denoiser.reduce_noise(file_path, work_file_path):
            repair_success = True
        
        # --- Future Steps (e.g., De-Clipping, Normalization) would go here ---
        
        # 2. Finalize
        if repair_success and os.path.exists(work_file_path):
            self.logger.info(f"✅ Repair cycle complete. Moving file to output.")
            
            # Define final destination
            final_dest = os.path.join(self.output_dir, work_filename)
            
            try:
                # Move the fixed file to the output directory (e.g., 'downloads')
                # This allows the Scanner Service to pick it up again for re-evaluation
                shutil.move(work_file_path, final_dest)
                return final_dest
            
            except Exception as e:
                self.logger.error(f"Failed to move repaired file to destination: {e}")
                # Clean up the stuck temp file
                if os.path.exists(work_file_path):
                    os.remove(work_file_path)
                return None
        else:
            self.logger.error(f"❌ Repair failed for {filename}")
            # Cleanup failed artifacts
            if os.path.exists(work_file_path):
                os.remove(work_file_path)
            return None