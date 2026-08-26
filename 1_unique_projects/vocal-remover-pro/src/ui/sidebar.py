"""
VocalRemover Pro - Streamlit Sidebar
Renders pipeline settings and system status.
"""
import os
import streamlit as st

from src.config import MDX_DIR, VR_DIR, MDX_KIM_VOCAL_2, VR_DEECHO, VR_DENOISE, UVR_DIR, LIBRARY_DIR
from src.utils.directml_check import describe_engine


def _model_ok(directory: str, filename: str) -> bool:
    return os.path.isfile(os.path.join(directory, filename))


def render_sidebar() -> dict:
    """Render the settings sidebar and return the current settings dict."""
    with st.sidebar:
        st.markdown(
            "<h2 style='margin-bottom:0'>🎛️ Pipeline</h2>"
            "<p style='color:#888;font-size:0.85rem;margin-top:2px'>VocalRemover Pro</p>",
            unsafe_allow_html=True,
        )
        st.divider()

        # ── Processing Stages ──────────────────────────────────────────────
        st.markdown("#### 🎙️ Processing Stages")
        st.caption("Uncheck stages you don't need to skip them and save time.")
        do_stage1 = st.checkbox(
            "Stage 1 — Raw Vocal (Kim Vocal 2)",
            value=True,
            help="MDX-Net extraction. Keeps producer reverb/effects intact.",
        )
        do_stage2 = st.checkbox(
            "Stage 2 — De-Reverb (DeEcho-DeReverb)",
            value=True,
            help="Removes room acoustics and reverb tails.",
        )
        do_stage3 = st.checkbox(
            "Stage 3 — De-Noise (DeNoise)",
            value=True,
            help="Removes residual background noise and hum.",
        )

        st.divider()

        # ── Speed ─────────────────────────────────────────────────────────
        st.markdown("#### ⚡ Speed")
        fast_mode = st.checkbox(
            "Fast Separation Mode",
            value=True,
            help="Increases hop length for Stage 1 (ONNX). ~2-3× faster, slight quality trade-off.",
        )

        st.divider()

        # ── Library ───────────────────────────────────────────────────────
        st.markdown("#### 📁 Library")
        library_dir_input = st.text_input("Output folder", value=LIBRARY_DIR)
        
        # Ensure library_dir is an absolute path
        if not os.path.isabs(library_dir_input):
            library_dir = os.path.abspath(os.path.join(LIBRARY_DIR, "..", library_dir_input))
        else:
            library_dir = library_dir_input

        st.divider()

        # ── System Status ─────────────────────────────────────────────────
        st.markdown("#### ⚙️ System Status")
        engine_desc = describe_engine()
        if "DirectML" in engine_desc or "CUDA" in engine_desc:
            st.success(f"GPU: {engine_desc}")
        else:
            st.info(f"Engine: {engine_desc}")

        missing = []
        if not _model_ok(MDX_DIR, MDX_KIM_VOCAL_2):
            missing.append(MDX_KIM_VOCAL_2)
        if not _model_ok(VR_DIR, VR_DEECHO):
            missing.append(VR_DEECHO)
        if not _model_ok(VR_DIR, VR_DENOISE):
            missing.append(VR_DENOISE)

        if missing:
            st.error("Missing UVR models:\n" + "\n".join(f"• {m}" for m in missing))
        else:
            st.success("All UVR models found ✓")

        ffmpeg_ok = os.path.isfile(os.path.join(UVR_DIR, "ffmpeg.exe"))
        if ffmpeg_ok:
            st.success("FFmpeg found ✓")
        else:
            st.warning("ffmpeg.exe not found in UVR dir")

    return {
        "do_stage1":   do_stage1,
        "do_stage2":   do_stage2,
        "do_stage3":   do_stage3,
        "fast_mode":   fast_mode,
        "library_dir": library_dir,
    }
