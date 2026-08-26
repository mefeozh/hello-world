"""
VocalRemover Pro - Library Explorer Tab
Browses the structured library folder with stem audio players and 1-click re-extraction.
"""
import os
import shutil
import tempfile
import streamlit as st

from src.config import MDX_DIR, VR_DIR, MDX_KIM_VOCAL_2, VR_DEECHO, VR_DENOISE
from src.core.separator import run_stage
from src.utils.normalizer import sanitize_filename, artist_library_paths

STEM_FOLDERS = [
    ("1_Downloaded",    "🔊 Original Download"),
    ("2_Raw_Vocal",     "🎤 Stage 1 — Raw Vocal (Wet)"),
    ("3_DeReverbed",    "🎙️ Stage 2 — Dry Vocal"),
    ("4_Final_Acapella","🧹 Stage 3 — Clean Acapella"),
]


def render_library_tab(settings: dict):
    library_dir = settings["library_dir"]

    st.markdown("### 📁 Local Library")

    if not os.path.isdir(library_dir):
        st.info("Library is empty. Process some tracks to populate it.")
        return

    artists = sorted(
        d for d in os.listdir(library_dir)
        if os.path.isdir(os.path.join(library_dir, d))
    )
    if not artists:
        st.info("No artist folders found yet.")
        return

    selected_artist = st.selectbox("Select artist:", artists)
    if not selected_artist:
        return

    artist_path = os.path.join(library_dir, selected_artist)

    # Collect all unique base track names across sub-folders
    all_tracks = set()
    for folder, _ in STEM_FOLDERS:
        folder_path = os.path.join(artist_path, folder)
        if os.path.isdir(folder_path):
            for f in os.listdir(folder_path):
                if f.endswith(".wav"):
                    # Normalize base filename
                    base = f.replace("_Vocals_Raw.wav", ".wav").replace("_Vocals_Dry.wav", ".wav").replace(" (Acapella).wav", ".wav")
                    all_tracks.add(base)

    if not all_tracks:
        st.info(f"No audio files found for **{selected_artist}** yet.")
        return

    st.markdown(f"#### 🎵 {selected_artist} — {len(all_tracks)} track(s)")

    for track_file in sorted(all_tracks):
        base_name = os.path.splitext(track_file)[0]
        
        # Check stem availability
        dl_file    = os.path.join(artist_path, "1_Downloaded", f"{base_name}.wav")
        raw_file   = os.path.join(artist_path, "2_Raw_Vocal", f"{base_name}_Vocals_Raw.wav")
        dry_file   = os.path.join(artist_path, "3_DeReverbed", f"{base_name}_Vocals_Dry.wav")
        clean_file = os.path.join(artist_path, "4_Final_Acapella", f"{base_name} (Acapella).wav")

        has_acapella = os.path.isfile(clean_file) and os.path.getsize(clean_file) > 0
        has_download = os.path.isfile(dl_file) and os.path.getsize(dl_file) > 0

        title_display = f"🎵 {base_name} {'✅' if has_acapella else '⏳ (Download Only - Ready to Extract)'}"

        with st.expander(title_display, expanded=not has_acapella):
            cols = st.columns(len(STEM_FOLDERS))
            
            stems = [
                ("1_Downloaded",    dl_file),
                ("2_Raw_Vocal",     raw_file),
                ("3_DeReverbed",    dry_file),
                ("4_Final_Acapella",clean_file),
            ]

            for col, (folder, stem_path) in zip(cols, stems):
                with col:
                    st.caption(dict(STEM_FOLDERS)[folder])
                    if os.path.isfile(stem_path) and os.path.getsize(stem_path) > 0:
                        st.audio(stem_path)
                        with open(stem_path, "rb") as f:
                            st.download_button(
                                "⬇️ Download",
                                data=f,
                                file_name=os.path.basename(stem_path),
                                mime="audio/wav",
                                key=f"dl_{selected_artist}_{folder}_{base_name}",
                            )
                    else:
                        st.markdown("*Missing*")

            # If download exists but acapella is missing, show Extract Vocals Now button!
            if has_download and not has_acapella:
                st.markdown("---")
                if st.button(f"⚡ Extract Vocals Now for '{base_name}'", key=f"ext_lib_{selected_artist}_{base_name}", type="primary", use_container_width=True):
                    _extract_cached_track(selected_artist, base_name, dl_file, settings)


def _extract_cached_track(artist_name: str, base_name: str, source_wav: str, settings: dict):
    """Run 3-stage vocal extraction for a track that is already downloaded in library."""
    st.markdown(f"### 🎛️ Extracting Vocals: {artist_name} - {base_name}")
    
    progress_bar = st.progress(0)
    status_text  = st.empty()

    library_dir = settings["library_dir"]
    do_s1 = settings["do_stage1"]
    do_s2 = settings["do_stage2"]
    do_s3 = settings["do_stage3"]
    fast  = settings["fast_mode"]

    lib = artist_library_paths(library_dir, artist_name)
    tmp_dir = tempfile.mkdtemp(prefix="uvr_reext_")

    def _progress(pct: int, msg: str):
        progress_bar.progress(min(max(pct, 0), 100))
        status_text.markdown(f"**Progress ({pct}%):** {msg}")

    try:
        last = source_wav
        _progress(20, "⬇️ Using downloaded WAV from library.")

        # Stage 1
        if do_s1:
            dest1 = os.path.join(lib["raw_vocal"], f"{base_name}_Vocals_Raw.wav")
            stem1 = run_stage(MDX_DIR, MDX_KIM_VOCAL_2, last, tmp_dir, "Stage 1 — Raw Vocal", _progress, 20, 50, fast)
            shutil.copyfile(stem1, dest1)
            last = dest1

        # Stage 2
        if do_s2 and last:
            dest2 = os.path.join(lib["dereverbed"], f"{base_name}_Vocals_Dry.wav")
            stem2 = run_stage(VR_DIR, VR_DEECHO, last, tmp_dir, "Stage 2 — De-Reverb", _progress, 50, 75, fast)
            shutil.copyfile(stem2, dest2)
            last = dest2

        # Stage 3
        if do_s3 and last:
            dest3 = os.path.join(lib["final_acapella"], f"{base_name} (Acapella).wav")
            stem3 = run_stage(VR_DIR, VR_DENOISE, last, tmp_dir, "Stage 3 — De-Noise", _progress, 75, 100, fast)
            shutil.move(stem3, dest3)

        _progress(100, "🎉 Acapella Extraction Complete!")
        st.balloons()
        st.rerun()

    except Exception as exc:
        status_text.error(f"❌ Extraction Error: {exc}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
