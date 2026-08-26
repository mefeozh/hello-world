"""
VocalRemover Pro - UVR Separation Engine
3-stage pipeline: Kim Vocal 2 (MDX/ONNX) → DeEcho-DeReverb (VR) → DeNoise (VR)
Guaranteed Vocal Stem Selection (Kim Vocal -> No Reverb -> No Noise).
"""
import gc
import os
import logging

from audio_separator.separator import Separator

logger = logging.getLogger("separator")


def _get_providers() -> tuple[bool, str]:
    """Detect if DirectML (AMD/Intel GPU) or CUDA is available for ONNX Runtime."""
    try:
        import onnxruntime as ort
        available = ort.get_available_providers()
        if "DmlExecutionProvider" in available:
            return True, "AMD/Intel GPU (DirectML ⚡)"
        if "CUDAExecutionProvider" in available:
            return False, "NVIDIA GPU (CUDA)"
    except Exception:
        pass
    return False, "CPU"


def run_stage(
    model_dir:         str,
    model_filename:    str,
    input_file:        str,
    output_dir:        str,
    stage_name:        str,
    progress_callback=None,
    pct_start:         int = 20,
    pct_end:           int = 50,
    fast_mode:         bool = False,
) -> str:
    """Run a single separation model stage and return the isolated vocal/dry stem file.

    Stage 1 (Kim Vocal 2)         -> Extracts isolated (Vocals) stem.
    Stage 2 (UVR-DeEcho-DeReverb) -> Extracts dry (No Reverb) stem.
    Stage 3 (UVR-DeNoise)         -> Extracts clean (No Noise) acapella stem.
    """
    os.makedirs(output_dir, exist_ok=True)
    use_dml, provider_desc = _get_providers()

    if progress_callback:
        progress_callback(pct_start, f"🎛️ {stage_name} — loading {model_filename} [{provider_desc}]…")

    logger.info("Stage: %s | Model: %s | Provider: %s", stage_name, model_filename, provider_desc)

    extra_kwargs: dict = {
        "use_directml": use_dml
    }
    
    # Configure single output stem target based on model type
    fn_lower = model_filename.lower()
    if "kim_vocal" in fn_lower:
        extra_kwargs["output_single_stem"] = "Vocals"
    elif "deecho" in fn_lower or "dereverb" in fn_lower:
        extra_kwargs["output_single_stem"] = "No Reverb"
    elif "denoise" in fn_lower:
        extra_kwargs["output_single_stem"] = "No Noise"

    if fast_mode and model_filename.endswith(".onnx"):
        extra_kwargs["mdx_params"] = {
            "hop_length":   1024,
            "segment_size": 256,
            "overlap":      0.25,
            "batch_size":   1,
        }

    try:
        sep = Separator(
            model_file_dir=model_dir,
            output_dir=output_dir,
            log_level=logging.WARNING,
            **extra_kwargs,
        )
        sep.load_model(model_filename)
    except Exception as exc:
        logger.warning(f"Failed to load model with use_directml={use_dml}, falling back to CPU: {exc}")
        if use_dml:
            extra_kwargs["use_directml"] = False
            sep = Separator(
                model_file_dir=model_dir,
                output_dir=output_dir,
                log_level=logging.WARNING,
                **extra_kwargs,
            )
            sep.load_model(model_filename)
        else:
            raise

    if progress_callback:
        mid = (pct_start + pct_end) // 2
        progress_callback(mid, f"🎛️ {stage_name} — processing audio…")

    output_files: list[str] = sep.separate(input_file)

    del sep
    try:
        gc.collect()
    except Exception:
        pass

    if not output_files:
        raise RuntimeError(f"{stage_name}: no stem files returned by audio-separator.")

    # Target stem selection algorithm
    target_stem = None
    
    for f in output_files:
        f_lower = f.lower()
        # Stage 2 dry vocal stem check
        if "no reverb" in f_lower or "no_reverb" in f_lower or "noreverb" in f_lower:
            target_stem = f
            break
        # Stage 3 clean acapella stem check
        elif "no noise" in f_lower or "no_noise" in f_lower or "nonoise" in f_lower:
            target_stem = f
            break
        # Stage 1 vocal stem check (must NOT be instrumental)
        elif "vocal" in f_lower and "instrumental" not in f_lower and "no vocal" not in f_lower:
            target_stem = f
            break

    # Fallback if specific stem keyword wasn't matched
    if not target_stem:
        for f in output_files:
            f_lower = f.lower()
            if "instrumental" not in f_lower and "reverb" not in f_lower and "noise" not in f_lower:
                target_stem = f
                break
        if not target_stem:
            target_stem = output_files[0]

    # Flexible path resolution check across current working dir and output_dir
    vocals_path = None
    for candidate in [target_stem] + output_files:
        p1 = candidate
        p2 = os.path.join(output_dir, os.path.basename(candidate))
        if os.path.isfile(p1) and os.path.getsize(p1) > 0:
            vocals_path = p1
            break
        elif os.path.isfile(p2) and os.path.getsize(p2) > 0:
            vocals_path = p2
            break

    if not vocals_path:
        raise RuntimeError(f"{stage_name}: target vocal stem file missing at {target_stem!r}")

    if progress_callback:
        progress_callback(pct_end, f"✅ {stage_name} complete.")

    return vocals_path


def get_engine_description() -> str:
    _, desc = _get_providers()
    return desc
