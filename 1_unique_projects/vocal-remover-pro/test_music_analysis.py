import os
import sys

# Add src to path
sys.path.append(os.path.abspath("c:/Users/mehme/PY_MAIN/vocal_remover"))

from src.utils.music_analysis import detect_key_bpm

def test():
    print("Testing music_analysis import...")
    import librosa
    import numpy as np
    
    # Let's generate a dummy wav file to test
    dummy_wav = "dummy.wav"
    sr = 22050
    # A 30s sine wave at 440Hz (A4)
    t = np.linspace(0, 30, int(sr * 30), endpoint=False)
    y = 0.5 * np.sin(2 * np.pi * 440 * t)
    
    import soundfile as sf
    sf.write(dummy_wav, y, sr)
    
    key, bpm = detect_key_bpm(dummy_wav)
    print(f"Key: {key}, BPM: {bpm}")
    
    os.remove(dummy_wav)

if __name__ == "__main__":
    test()
