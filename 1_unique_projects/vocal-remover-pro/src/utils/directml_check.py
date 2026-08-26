"""
VocalRemover Pro - AMD/Intel GPU (DirectML) Detection
"""
import logging

logger = logging.getLogger("directml_check")


def get_providers() -> tuple[list[str], str]:
    """Detect the best available ONNX Runtime execution providers.

    Priority: DirectML (AMD / Intel GPU on Windows) → CUDA → CPU.

    Returns:
        (provider_list, human_readable_description)
    """
    try:
        import onnxruntime as ort
        available = ort.get_available_providers()
        if "DmlExecutionProvider" in available:
            return ["DmlExecutionProvider", "CPUExecutionProvider"], "AMD/Intel GPU (DirectML ⚡)"
        if "CUDAExecutionProvider" in available:
            return ["CUDAExecutionProvider", "CPUExecutionProvider"], "NVIDIA GPU (CUDA ⚡)"
    except Exception as exc:
        logger.debug("ONNX Runtime provider check failed: %s", exc)
    return ["CPUExecutionProvider"], "CPU (no GPU acceleration)"


def describe_engine() -> str:
    _, desc = get_providers()
    return desc
