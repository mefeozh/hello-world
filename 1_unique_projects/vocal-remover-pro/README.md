# 🎵 VocalRemover Pro — Neural Audio Stem Separation Pipeline

**Author:** Mehmet Efe Özhan  
**Architecture:** MDX-Net (Kim Vocal 2) + UVR De-Echo / De-Noise | ONNXRuntime-DirectML

---

## 📌 System Features

A high-fidelity 3-stage neural audio stem separation pipeline optimized for low-latency AMD/Intel/NVIDIA inference via **Microsoft DirectML**:

1. **Stage 1 (Stem Separation):** MDX-Net (*Kim Vocal 2*) extracts isolated vocal and instrumental stems.
2. **Stage 2 (De-Reverb):** VR Architecture (*UVR-DeEcho-DeReverb*) eliminates acoustic room reverberation.
3. **Stage 3 (De-Noise):** UVR Architecture (*UVR-DeNoise*) strips high-frequency artifacts and hiss.

---

## 💻 Execution

- **Interactive Web UI:**
  ```bash
  streamlit run app.py
  ```
- **CLI Batch Mode:**
  ```bash
  python vocal_remover.py input_song.mp3 --output_dir ./stems/
  ```
