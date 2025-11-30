"""
Advanced Audio Analysis Module
Detects clipping, loudness issues, frequency problems
"""

import librosa
import numpy as np
import soundfile as sf
from pathlib import Path
import json

class AudioAnalyzer:
    def __init__(self):
        self.analysis_results = []
    
    def analyze_file(self, file_path):
        """Comprehensive audio analysis"""
        file_path = Path(file_path)
        print(f"\n🔬 Analyzing: {file_path.name}")
        
        try:
            # Load audio
            y, sr = librosa.load(str(file_path), sr=None, mono=False)
            
            # Convert to mono for analysis if stereo
            if y.ndim > 1:
                y_mono = librosa.to_mono(y)
            else:
                y_mono = y
            
            analysis = {
                'file': str(file_path),
                'sample_rate': sr,
                'duration': len(y_mono) / sr,
                'channels': 2 if y.ndim > 1 else 1,
                'issues': []
            }
            
            # 1. Clipping Detection
            clipping_info = self.detect_clipping(y_mono)
            if clipping_info['has_clipping']:
                analysis['issues'].append('clipping')
            analysis['clipping'] = clipping_info
            
            # 2. Loudness Analysis
            loudness_info = self.analyze_loudness(y_mono)
            if loudness_info['needs_normalization']:
                analysis['issues'].append('loudness')
            analysis['loudness'] = loudness_info
            
            # 3. Silence/Dropout Detection
            silence_info = self.detect_silence(y_mono, sr)
            if silence_info['has_long_silence']:
                analysis['issues'].append('silence')
            analysis['silence'] = silence_info
            
            # 4. Frequency Analysis
            freq_info = self.analyze_frequency(y_mono, sr)
            if freq_info['has_issues']:
                analysis['issues'].append('frequency')
            analysis['frequency'] = freq_info
            
            # 5. Dynamic Range
            dr_info = self.analyze_dynamic_range(y_mono)
            if dr_info['needs_expansion']:
                analysis['issues'].append('dynamic_range')
            analysis['dynamic_range'] = dr_info
            
            # Overall health score
            analysis['health_score'] = self.calculate_health_score(analysis)
            analysis['status'] = 'healthy' if len(analysis['issues']) == 0 else 'needs_attention'
            
            self.analysis_results.append(analysis)
            self.print_analysis(analysis)
            
            return analysis
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            return {'file': str(file_path), 'error': str(e), 'status': 'error'}
    
    def detect_clipping(self, y, threshold=0.99):
        """Detect audio clipping"""
        clipped_samples = np.sum(np.abs(y) >= threshold)
        total_samples = len(y)
        clipping_ratio = clipped_samples / total_samples
        
        has_clipping = clipping_ratio > 0.001  # 0.1% threshold
        
        return {
            'has_clipping': bool(has_clipping),
            'clipping_ratio': float(clipping_ratio),
            'clipped_samples': int(clipped_samples),
            'severity': 'high' if clipping_ratio > 0.01 else 'medium' if clipping_ratio > 0.001 else 'low'
        }
    
    def analyze_loudness(self, y):
        """Analyze loudness (RMS and peak)"""
        rms = np.sqrt(np.mean(y**2))
        peak = np.max(np.abs(y))
        
        # Convert to dB
        rms_db = 20 * np.log10(rms) if rms > 0 else -np.inf
        peak_db = 20 * np.log10(peak) if peak > 0 else -np.inf
        
        # Ideal range: -18 to -14 dB RMS for music
        needs_normalization = rms_db < -24 or rms_db > -12
        
        return {
            'rms_db': float(rms_db),
            'peak_db': float(peak_db),
            'crest_factor': float(peak / rms) if rms > 0 else 0,
            'needs_normalization': bool(needs_normalization),
            'recommendation': 'normalize' if needs_normalization else 'ok'
        }
    
    def detect_silence(self, y, sr, threshold_db=-40, min_duration=0.5):
        """Detect long silent sections"""
        # Convert to dB
        db = librosa.amplitude_to_db(np.abs(y), ref=np.max)
        
        # Find silent intervals
        silent_intervals = librosa.effects.split(y, top_db=-threshold_db)
        
        # Calculate silence duration
        if len(silent_intervals) > 0:
            audio_duration = len(y) / sr
            audio_samples = sum([end - start for start, end in silent_intervals])
            silence_duration = audio_duration - (audio_samples / sr)
        else:
            silence_duration = 0
        
        has_long_silence = silence_duration > min_duration
        
        return {
            'has_long_silence': bool(has_long_silence),
            'total_silence_duration': float(silence_duration),
            'silent_intervals_count': int(len(silent_intervals)),
            'recommendation': 'check_dropouts' if has_long_silence else 'ok'
        }
    
    def analyze_frequency(self, y, sr):
        """Analyze frequency spectrum"""
        # Compute FFT
        fft = np.fft.fft(y)
        magnitude = np.abs(fft[:len(fft)//2])
        freqs = np.fft.fftfreq(len(fft), 1/sr)[:len(fft)//2]
        
        # Check frequency bands
        low_freq = np.mean(magnitude[(freqs >= 20) & (freqs < 250)])
        mid_freq = np.mean(magnitude[(freqs >= 250) & (freqs < 4000)])
        high_freq = np.mean(magnitude[(freqs >= 4000) & (freqs < 20000)])
        
        # Detect imbalance
        total_energy = low_freq + mid_freq + high_freq
        if total_energy > 0:
            low_ratio = low_freq / total_energy
            high_ratio = high_freq / total_energy
        else:
            low_ratio = high_ratio = 0
        
        has_issues = low_ratio < 0.1 or high_ratio < 0.05  # Missing frequencies
        
        return {
            'has_issues': bool(has_issues),
            'low_freq_energy': float(low_ratio),
            'high_freq_energy': float(high_ratio),
            'recommendation': 'eq_correction' if has_issues else 'ok'
        }
    
    def analyze_dynamic_range(self, y):
        """Analyze dynamic range"""
        # Calculate DR using EBU R128 approximation
        rms_values = []
        window_size = 1024
        for i in range(0, len(y) - window_size, window_size):
            window = y[i:i+window_size]
            rms_values.append(np.sqrt(np.mean(window**2)))
        
        if len(rms_values) > 0:
            rms_values = np.array(rms_values)
            rms_values = rms_values[rms_values > 0]
            
            if len(rms_values) > 0:
                rms_db = 20 * np.log10(rms_values)
                dr = np.percentile(rms_db, 95) - np.percentile(rms_db, 5)
            else:
                dr = 0
        else:
            dr = 0
        
        # Good DR is > 10 dB for music
        needs_expansion = dr < 6
        
        return {
            'dynamic_range_db': float(dr),
            'needs_expansion': bool(needs_expansion),
            'quality': 'poor' if dr < 6 else 'fair' if dr < 10 else 'good' if dr < 14 else 'excellent'
        }
    
    def calculate_health_score(self, analysis):
        """Calculate overall health score (0-100)"""
        score = 100
        
        # Deduct points for issues
        if analysis['clipping']['has_clipping']:
            severity = analysis['clipping']['severity']
            score -= 30 if severity == 'high' else 20 if severity == 'medium' else 10
        
        if analysis['loudness']['needs_normalization']:
            score -= 15
        
        if analysis['silence']['has_long_silence']:
            score -= 10
        
        if analysis['frequency']['has_issues']:
            score -= 15
        
        if analysis['dynamic_range']['needs_expansion']:
            score -= 20
        
        return max(0, score)
    
    def print_analysis(self, analysis):
        """Print analysis results"""
        print(f"  📊 Health Score: {analysis['health_score']}/100")
        print(f"  ⏱️  Duration: {analysis['duration']:.2f}s")
        print(f"  📻 Sample Rate: {analysis['sample_rate']} Hz")
        print(f"  🔊 Channels: {analysis['channels']}")
        
        if analysis['issues']:
            print(f"  ⚠️  Issues: {', '.join(analysis['issues'])}")
        else:
            print(f"  ✅ No issues detected!")
    
    def save_report(self, output_file='audio_analysis_report.json'):
        """Save comprehensive analysis report"""
        
        def convert_to_native(obj):
            """Convert numpy types to Python native types"""
            if isinstance(obj, dict):
                return {k: convert_to_native(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_native(item) for item in obj]
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return obj
        
        report = {
            'total_files': len(self.analysis_results),
            'results': convert_to_native(self.analysis_results)
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Analysis report saved: {output_file}")


def main():
    """Test analyzer"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 audio_analyzer.py <file_or_directory>")
        sys.exit(1)
    
    path = Path(sys.argv[1])
    analyzer = AudioAnalyzer()
    
    if path.is_file():
        analyzer.analyze_file(path)
    elif path.is_dir():
        audio_files = list(path.rglob('*.mp3')) + list(path.rglob('*.flac')) + list(path.rglob('*.wav'))
        for audio_file in audio_files:
            analyzer.analyze_file(audio_file)
    
    analyzer.save_report()


if __name__ == '__main__':
    main()
