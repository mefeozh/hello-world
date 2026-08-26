import librosa
import numpy as np

def detect_key_bpm(audio_wav_path: str, meta: dict = None) -> tuple[str, int]:
    """
    Detects the musical key and BPM of an audio file using librosa.
    """
    try:
        # Load audio, taking the first 30 seconds to speed up processing
        y, sr = librosa.load(audio_wav_path, duration=30.0, sr=22050)
        
        # Detect BPM
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        bpm = int(round(tempo[0])) if isinstance(tempo, np.ndarray) else int(round(tempo))

        # Detect Key using Chroma
        # Using CQT chroma for better musical pitch representation
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        chroma_sum = np.sum(chroma, axis=1)
        
        # Krumhansl-Schmuckler profiles for major and minor keys
        maj_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
        min_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
        
        keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        best_corr = -1.0
        best_key = "C"
        
        for i in range(12):
            # Rotate profiles to match the root note
            maj_rot = np.roll(maj_profile, i)
            min_rot = np.roll(min_profile, i)
            
            # Calculate correlation
            corr_maj = np.corrcoef(chroma_sum, maj_rot)[0, 1]
            corr_min = np.corrcoef(chroma_sum, min_rot)[0, 1]
            
            if corr_maj > best_corr:
                best_corr = corr_maj
                best_key = f"{keys[i]}"
            
            if corr_min > best_corr:
                best_corr = corr_min
                best_key = f"{keys[i]}m"

        return best_key, bpm
    except Exception as e:
        print(f"Error detecting key and BPM for {audio_wav_path}: {e}")
        return "Unknown", 0
