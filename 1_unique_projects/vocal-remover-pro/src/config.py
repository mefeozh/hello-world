"""
VocalRemover Pro - Environment-Aware Configuration
All paths and settings are read from environment variables with sensible defaults.
"""
import os
from pathlib import Path

# ─── UVR Installation & Cross-Platform Default ───────────────────────────────
if os.name == "nt":
    user_prof = os.environ.get("USERPROFILE", "C:\\")
    UVR_DEFAULT = os.path.join(user_prof, "AppData", "Local", "Programs", "Ultimate Vocal Remover")
else:
    UVR_DEFAULT = "/app/models"

UVR_DIR = os.getenv("UVR_DIR", UVR_DEFAULT)

# Add UVR bundled ffmpeg to PATH so yt-dlp and audio-separator can find it
if os.path.isdir(UVR_DIR):
    os.environ["PATH"] = UVR_DIR + os.pathsep + os.environ.get("PATH", "")

# ─── Model Directories ────────────────────────────────────────────────────────
# In Docker: set MODEL_DIR=/app/models and mount your UVR models there
MODEL_DIR = os.getenv("MODEL_DIR", os.path.join(UVR_DIR, "models"))
MDX_DIR   = os.path.join(MODEL_DIR, "MDX_Net_Models")
VR_DIR    = os.path.join(MODEL_DIR, "VR_Models")

# ─── Library / Output ─────────────────────────────────────────────────────────
# Root directory where all processed audio is stored
# In Docker: mount host ./library → /app/library and set LIBRARY_DIR=/app/library
_here       = Path(__file__).resolve().parent.parent  # vocal_remover/
LIBRARY_DIR = os.getenv("LIBRARY_DIR", str(_here / "library"))

# ─── API Endpoints ────────────────────────────────────────────────────────────
ITUNES_SEARCH_URL = "https://itunes.apple.com/search"
ITUNES_LOOKUP_URL = "https://itunes.apple.com/lookup"
DEEZER_SEARCH_URL = "https://api.deezer.com/search/artist"
DEEZER_TOP_URL    = "https://api.deezer.com/artist/{artist_id}/top"

COMMON_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ─── UVR Model File Names ─────────────────────────────────────────────────────
MDX_KIM_VOCAL_2 = "Kim_Vocal_2.onnx"
VR_DEECHO       = "UVR-DeEcho-DeReverb.pth"
VR_DENOISE      = "UVR-DeNoise.pth"
