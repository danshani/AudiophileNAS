import os
import shutil
import subprocess
import logging

class AudioDenoiser:
    """
    Handles noise reduction using FFmpeg filters.
    Requires 'ffmpeg' to be installed on the system path (a prerequisite for RPi OS).
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Critical check: Ensure FFmpeg binary is available on the system path
        if not shutil.which("ffmpeg"):
            raise EnvironmentError("FFmpeg not found! Please install it (e.g., sudo apt install ffmpeg)")

    def reduce_noise(self, input_path: str, output_path: str, noise_reduction_db: int = 12) -> bool:
        """
        Applies FFT-based noise reduction filter (afftdn) using FFmpeg.
        
        Args:
            input_path: Source file path (e.g., a file from the quarantine folder).
            output_path: Destination file path (must be .flac to preserve quality).
            noise_reduction_db: Strength of reduction in dB (safe range: 10-15dB).
            
        Returns:
            bool: True if denoising command was successful, False otherwise.
        """
        self.logger.info(f"Applying Noise Reduction ({noise_reduction_db}dB) on: {os.path.basename(input_path)}")
        
        # Build the FFmpeg command
        cmd = [
            "ffmpeg",
            "-y",                   # Overwrite output without asking
            "-v", "error",          # Only print critical errors
            "-i", input_path,       # Input file
            # afftdn filter: nr=Noise Reduction amount, nf=Noise Floor tracking, tn=Track Noise
            "-af", f"afftdn=nr={noise_reduction_db}:nf=-25:tn=1", 
            "-c:a", "flac",         # Re-encode as FLAC (Lossless) to maintain quality
            output_path             # Output file
        ]

        try:
            # Run the subprocess command
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0:
                self.logger.info("✅ Noise reduction successful.")
                return True
            else:
                # Log the specific FFmpeg error output
                self.logger.error(f"❌ FFmpeg failed:\n{result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Denoiser execution error: {e}")
            return False