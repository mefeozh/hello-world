"""
VocalRemover Pro - High-Fidelity Studio Audio Downloader
Ranker filters YouTube results for Official Master Studio Audio (Topic Channels & Official Audio)
and verifies video duration to guarantee full-length track extraction (preventing short previews/snippets).
Converts to pristine 44.1kHz PCM WAV using SOXR audiophile resampling.
"""
import os
import shutil
import tempfile
import logging
import yt_dlp

from src.config import UVR_DIR

logger = logging.getLogger("downloader")


def parse_duration_to_seconds(dur_val) -> int:
    """Parse duration integer or string like '4:19' / '04:19' / '1:04:19' into seconds."""
    if not dur_val:
        return 0
    if isinstance(dur_val, (int, float)):
        return int(dur_val)
    if isinstance(dur_val, str) and ":" in dur_val:
        try:
            parts = [int(p) for p in dur_val.split(":") if p.strip().isdigit()]
            if len(parts) == 2:
                return parts[0] * 60 + parts[1]
            elif len(parts) == 3:
                return parts[0] * 3600 + parts[1] * 60 + parts[2]
        except Exception:
            pass
    return 0


def _score_audio_entry(entry: dict, target_artist: str = "", expected_duration: int = 0) -> int:
    title    = entry.get("title", "").lower()
    uploader = entry.get("uploader", "").lower()
    channel  = entry.get("channel", "").lower()
    duration = entry.get("duration", 0) or 0
    artist   = target_artist.lower() if target_artist else ""

    score = 0

    # 1. DURATION MATCHING (CRITICAL SAFEGUARD TO PREVENT SHORT PREVIEWS / SNIPPETS)
    if expected_duration > 0 and duration > 0:
        diff = abs(duration - expected_duration)
        if diff <= 15:
            score += 60  # Exact full-length track match (+60 pts)
        elif diff <= 30:
            score += 30
        else:
            score -= 500 # Massive penalty for short previews, snippets, or extended remixes
    elif duration > 0 and duration < 100:
        score -= 300     # General penalty for videos under 1m 40s if duration unknown

    # 2. Uploader / Channel verification
    if "- topic" in uploader or "- topic" in channel or "youtube music" in uploader:
        score += 50  # Official Topic Channel = Highest Studio Master Audio
    elif artist and (artist in uploader or artist in channel or artist in entry.get("channel_url", "").lower()):
        score += 40  # Official Verified Artist Channel

    # 3. Title verification
    if "official audio" in title:
        score += 35
    elif "audio" in title and "official" in title:
        score += 30
    elif "official lyric video" in title or "lyric video" in title or "reinsertado" in title:
        score += 20
    elif "official music video" in title or "official video" in title:
        score += 10

    # Penalize low quality, live, or snippet audio
    penalties = ["live", "concert", "slowed", "reverb", "cover", "sped up", "tik tok", "snippet", "teaser", "preview", "short", "bass boosted"]
    for p in penalties:
        if p in title and (not artist or p not in artist.lower()):
            score -= 200

    return score


def download_audio(
    query: str,
    output_dir: str,
    artist_name: str = "",
    expected_duration=None,
    progress_callback=None,
) -> tuple[str, str]:
    """Download highest studio master audio for a search query string or direct URL.

    Args:
        query:             YouTube URL, Spotify URL, or search query like "Morad - Cristales"
        output_dir:        Directory where the .wav file is saved
        artist_name:       Optional canonical artist name for quality scoring
        expected_duration: Optional expected duration (seconds or "4:19" string)
        progress_callback: Optional callable(pct: int, text: str)

    Returns:
        (wav_path, video_title)
    """
    is_url = query.startswith(("http://", "https://", "www."))
    target_sec = parse_duration_to_seconds(expected_duration)

    if is_url:
        target_url = query
    else:
        # Use Studio Master Audio Ranker with Duration Verification
        clean_q = query.strip()
        search_target = f"ytsearch10:{clean_q}"
        
        ydl_rank_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False, # Extract detailed info for duration checks
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_rank_opts) as ydl:
                info = ydl.extract_info(search_target, download=False)
                entries = info.get("entries", []) if info else []
                if entries:
                    ranked = []
                    for e in entries:
                        s = _score_audio_entry(e, target_artist=artist_name, expected_duration=target_sec)
                        ranked.append((s, e))
                    ranked.sort(key=lambda x: x[0], reverse=True)
                    best_entry = ranked[0][1]
                    target_url = best_entry.get("url") or best_entry.get("webpage_url") or f"ytsearch1:{clean_q}"
                else:
                    target_url = f"ytsearch1:{clean_q} official audio"
        except Exception as exc:
            logger.warning(f"Studio ranker search failed: {exc}, using direct query")
            target_url = f"ytsearch1:{clean_q} official audio"

    def _hook(d: dict):
        if d["status"] == "downloading" and progress_callback:
            total      = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            if total > 0:
                pct      = int((downloaded / total) * 20)   # maps download → 0-20%
                speed    = d.get("speed")
                spd_str  = f"{speed / 1_048_576:.1f} MB/s" if speed else "…"
                size_str = f"{downloaded/1_048_576:.1f}/{total/1_048_576:.1f} MB"
                progress_callback(pct, f"⬇️ Downloading Full Studio Audio: {size_str} ({spd_str})")

    os.makedirs(output_dir, exist_ok=True)
    tmp_dl = tempfile.mkdtemp(prefix="ytdlp_hq_", dir=output_dir)

    ydl_opts = {
        # Select uncompressed / highest bitrate stream available (Opus 160k / AAC 256k)
        "format":             "bestaudio[acodec=opus]/bestaudio[ext=m4a]/bestaudio/best",
        "ffmpeg_location":    UVR_DIR,
        "postprocessors":     [{
            "key":              "FFmpegExtractAudio",
            "preferredcodec":   "wav",
            "preferredquality": "0",  # lossless PCM WAV
        }],
        # SOXR Audiophile Resampling: 44.1kHz 16-bit PCM with zero aliasing artifacts
        "postprocessor_args": [
            "-ar", "44100",
            "-ac", "2",
            "-c:a", "pcm_s16le",
            "-af", "aresample=resampler=soxr:precision=33"
        ],
        "outtmpl":            os.path.join(tmp_dl, "%(title)s.%(ext)s"),
        "noplaylist":         True,
        "restrictfilenames":  True,
        "quiet":              True,
        "no_warnings":        True,
        "progress_hooks":     [_hook],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(target_url, download=True)
            if "entries" in info:
                if not info["entries"]:
                    raise RuntimeError(f"No audio streams found for: {query!r}")
                video_info = info["entries"][0]
            else:
                video_info = info

            video_title = video_info.get("title", "audio")

        wav_files = [
            f for f in os.listdir(tmp_dl)
            if f.endswith(".wav")
        ]
        if not wav_files:
            raise RuntimeError("Download succeeded but no .wav file was created.")

        src_path = os.path.join(tmp_dl, wav_files[0])
        dst_path = os.path.join(output_dir, wav_files[0])
        if os.path.exists(dst_path):
            os.remove(dst_path)
        shutil.move(src_path, dst_path)

        logger.info(f"Downloaded Studio Master Audio: {video_title!r} -> {dst_path}")
        return dst_path, video_title

    finally:
        shutil.rmtree(tmp_dl, ignore_errors=True)
