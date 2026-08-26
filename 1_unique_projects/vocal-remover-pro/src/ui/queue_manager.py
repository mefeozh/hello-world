"""
VocalRemover Pro - Queue Manager Tab
Displays queued tracks, lets the user remove items, and runs the batch pipeline.
Includes disk-backed state persistence across browser reloads.
"""
import os
import json
import shutil
import tempfile
import streamlit as st

from src.config import MDX_DIR, VR_DIR, MDX_KIM_VOCAL_2, VR_DEECHO, VR_DENOISE
from src.utils.normalizer import sanitize_filename, artist_library_paths
from src.core.downloader import download_audio
from src.core.separator import run_stage

QUEUE_FILE_NAME = ".queue_state.json"

# Status badge colours via inline HTML
_BADGE = {
    "Pending":    ('<span style="background:#2d2d3f;color:#ffa500;padding:2px 10px;'
                   'border-radius:10px;font-size:0.78rem;font-weight:600">⏳ Pending</span>'),
    "Processing": ('<span style="background:#1e2a38;color:#00b0ff;padding:2px 10px;'
                   'border-radius:10px;font-size:0.78rem;font-weight:600">⚙️ Processing</span>'),
    "Done":       ('<span style="background:#1e3a2b;color:#00ff9d;padding:2px 10px;'
                   'border-radius:10px;font-size:0.78rem;font-weight:600">✅ Done</span>'),
    "Error":      ('<span style="background:#3a1e1e;color:#ff5555;padding:2px 10px;'
                   'border-radius:10px;font-size:0.78rem;font-weight:600">❌ Error</span>'),
}


def _badge(status: str) -> str:
    for key in _BADGE:
        if key.lower() in status.lower():
            return _BADGE[key]
    return f'<span style="color:#aaa">{status}</span>'


def _get_queue_file_path(library_dir: str) -> str:
    os.makedirs(library_dir, exist_ok=True)
    return os.path.join(library_dir, QUEUE_FILE_NAME)


def load_persisted_queue(library_dir: str) -> list[dict]:
    """Load queue from disk if it exists."""
    filepath = _get_queue_file_path(library_dir)
    if os.path.isfile(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    # Reset any leftover 'Processing' status to 'Pending' on fresh page reload
                    for item in data:
                        if item.get("status") == "Processing":
                            item["status"] = "Pending"
                    return data
        except Exception:
            pass
    return []


def save_persisted_queue(library_dir: str, queue: list[dict]):
    """Save queue to disk."""
    filepath = _get_queue_file_path(library_dir)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(queue, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def render_queue_tab(settings: dict):
    library_dir = settings["library_dir"]
    st.markdown("### 📋 Queue Manager")

    if "queue" not in st.session_state or st.session_state.queue is None:
        st.session_state.queue = load_persisted_queue(library_dir)

    queue = st.session_state.queue

    if not queue:
        st.info("Your queue is empty. Go to **Search** to find and add tracks.")
        return

    # ── Queue table ────────────────────────────────────────────────────────
    st.markdown(f"**{len(queue)} track(s) in queue:**")
    header = st.columns([0.5, 2, 3, 2, 0.7])
    for col, label in zip(header, ["#", "Artist", "Title", "Status", ""]):
        col.markdown(f"**{label}**")
    st.divider()

    to_remove = []
    for idx, item in enumerate(queue):
        c1, c2, c3, c4, c5 = st.columns([0.5, 2, 3, 2, 0.7])
        c1.text(item["id"])
        c2.text(item["artist"])
        c3.text(item["title"])
        c4.markdown(_badge(item["status"]), unsafe_allow_html=True)
        if c5.button("✕", key=f"rm_{item['id']}"):
            to_remove.append(idx)

    for idx in reversed(to_remove):
        st.session_state.queue.pop(idx)
    if to_remove:
        save_persisted_queue(library_dir, st.session_state.queue)
        st.rerun()

    st.divider()

    col_clear, col_start = st.columns(2)
    with col_clear:
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.queue = []
            save_persisted_queue(library_dir, [])
            st.rerun()
    with col_start:
        start = st.button("▶️ Start Batch", type="primary", use_container_width=True)

    if not start:
        return

    # ── Batch execution ────────────────────────────────────────────────────
    progress_bar  = st.progress(0)
    status_text   = st.empty()
    results_area  = st.container()

    do_s1 = settings["do_stage1"]
    do_s2 = settings["do_stage2"]
    do_s3 = settings["do_stage3"]
    fast  = settings["fast_mode"]

    pending = [i for i, q in enumerate(queue) if q["status"] == "Pending"]
    total   = len(pending)

    for job_num, idx in enumerate(pending, 1):
        item = queue[idx]
        item["status"] = "Processing"
        save_persisted_queue(library_dir, queue)

        lib = artist_library_paths(library_dir, item["artist"])
        safe_title = sanitize_filename(item["title"])
        tmp_dir    = tempfile.mkdtemp(prefix="uvr_")

        def _progress(pct: int, msg: str):
            overall = int(((job_num - 1) / total + pct / (100 * total)) * 100)
            progress_bar.progress(min(overall, 100))
            status_text.markdown(
                f"**[{job_num}/{total}]** {item['artist']} — {item['title']}\n\n{msg}"
            )

        try:
            # ── Download Studio Master Audio ──────────────────────────────
            import glob
            dl_dest_base = os.path.join(lib["downloaded"], f"{safe_title}")
            cached_files = glob.glob(f"{dl_dest_base}*.wav")
            
            if cached_files and os.path.getsize(cached_files[0]) > 0:
                source = cached_files[0]
                _progress(20, "⬇️ Already downloaded — using cached studio file.")
                
                from src.utils.music_analysis import detect_key_bpm
                base_name = os.path.splitext(os.path.basename(source))[0]
                if "BPM" in base_name:
                    safe_title = base_name
                else:
                    key_str, bpm_int = detect_key_bpm(source)
                    safe_title = f"{safe_title}_{bpm_int}BPM_{key_str}"
                    new_dl_dest = os.path.join(lib["downloaded"], f"{safe_title}.wav")
                    os.rename(source, new_dl_dest)
                    source = new_dl_dest
            else:
                dl_tmp, yt_title = download_audio(
                    item["full_title"],
                    tmp_dir,
                    artist_name=item["artist"],
                    expected_duration=item.get("duration"),
                    progress_callback=_progress,
                )
                from src.utils.music_analysis import detect_key_bpm
                key_str, bpm_int = detect_key_bpm(dl_tmp)
                safe_title = f"{safe_title}_{bpm_int}BPM_{key_str}"
                dl_dest = os.path.join(lib["downloaded"], f"{safe_title}.wav")
                shutil.copyfile(dl_tmp, dl_dest)
                source = dl_dest

            last = source
            raw_path = dry_path = clean_path = None

            # ── Stage 1: Raw Vocal ────────────────────────────────────────
            if do_s1:
                dest1 = os.path.join(lib["raw_vocal"], f"{safe_title}_Vocals_Raw.wav")
                if os.path.isfile(dest1) and os.path.getsize(dest1) > 0:
                    last = dest1
                    _progress(50, "🎤 Stage 1 cached.")
                else:
                    stem1 = run_stage(MDX_DIR, MDX_KIM_VOCAL_2, source, tmp_dir,
                                      "Stage 1 — Raw Vocal", _progress, 20, 50, fast)
                    shutil.copyfile(stem1, dest1)
                    last = dest1
                raw_path = last

            # ── Stage 2: De-Reverb ────────────────────────────────────────
            if do_s2 and last:
                dest2 = os.path.join(lib["dereverbed"], f"{safe_title}_Vocals_Dry.wav")
                if os.path.isfile(dest2) and os.path.getsize(dest2) > 0:
                    last = dest2
                    _progress(75, "🎙️ Stage 2 cached.")
                else:
                    stem2 = run_stage(VR_DIR, VR_DEECHO, last, tmp_dir,
                                      "Stage 2 — De-Reverb", _progress, 50, 75, fast)
                    shutil.copyfile(stem2, dest2)
                    last = dest2
                dry_path = last

            # ── Stage 3: De-Noise ─────────────────────────────────────────
            if do_s3 and last:
                dest3 = os.path.join(lib["final_acapella"], f"{safe_title} (Acapella).wav")
                if os.path.isfile(dest3) and os.path.getsize(dest3) > 0:
                    last = dest3
                    _progress(100, "🧹 Stage 3 cached.")
                else:
                    stem3 = run_stage(VR_DIR, VR_DENOISE, last, tmp_dir,
                                      "Stage 3 — De-Noise", _progress, 75, 100, fast)
                    shutil.move(stem3, dest3)
                    last = dest3
                clean_path = last

            item["status"] = "Done"
            save_persisted_queue(library_dir, queue)
            _progress(100, "✅ Complete!")

            # ── Stem Comparison ───────────────────────────────────────────
            with results_area:
                st.markdown(f"#### 🎵 {item['artist']} — {item['title']}")
                cols = st.columns(4)
                stems = [
                    ("🔊 Studio Original", source),
                    ("🎤 Raw Vocal",       raw_path),
                    ("🎙️ Dry Vocal",      dry_path),
                    ("🧹 Clean Acapella", clean_path),
                ]
                for col, (label, path) in zip(cols, stems):
                    with col:
                        st.caption(label)
                        if path and os.path.isfile(path):
                            st.audio(path)
                        else:
                            st.markdown("*Skipped*")
                st.divider()

        except Exception as exc:
            item["status"] = f"Error: {exc}"
            save_persisted_queue(library_dir, queue)
            status_text.error(f"❌ Error on **{item['title']}**: {exc}")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    progress_bar.progress(100)
    st.balloons()
