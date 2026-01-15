import numpy as np
from typing import Optional
from faster_whisper import WhisperModel
import threading
from services.logger import get_logger
from services.model_manager import MODEL_REPOS
from services.gpu import resolve_device, get_compute_type

log = get_logger("model")


def _get_repo_id(model_name: str) -> str:
    """Get the HuggingFace repo ID for a model name."""
    return MODEL_REPOS.get(model_name, f"Systran/faster-whisper-{model_name}")


class TranscriptionService:
    def __init__(self):
        self._model: Optional[WhisperModel] = None
        self._current_model_name: str = None
        self._current_device: str = None
        self._current_compute_type: str = None
        self._loading = False
        self._lock = threading.Lock()
        self._idle_timer: Optional[threading.Timer] = None

    def load_model(self, model_name: str = "tiny", device_preference: str = "auto"):
        """Load or switch Whisper model.

        Args:
            model_name: Name of the Whisper model
            device_preference: "auto", "cpu", or "cuda"
        """
        # Cancel idle timer since we're actively using the model
        self._cancel_idle_timer()

        # Resolve device and compute type
        device = resolve_device(device_preference)
        compute_type = get_compute_type(device)

        with self._lock:
            # Check if we need to reload
            if (self._current_model_name == model_name
                and self._current_device == device
                and self._model is not None):
                return  # Already loaded with same config

            self._loading = True
            try:
                repo_id = _get_repo_id(model_name)
                log.info(
                    "Loading model",
                    model=model_name,
                    device=device,
                    compute_type=compute_type
                )
                self._model = WhisperModel(
                    repo_id,
                    device=device,
                    compute_type=compute_type,
                )
                self._current_model_name = model_name
                self._current_device = device
                self._current_compute_type = compute_type
                log.info("Model loaded successfully", device=device, compute_type=compute_type)
            except Exception as e:
                log.error("Failed to load model", error=str(e), device=device)
                # If CUDA failed, try falling back to CPU
                if device == "cuda":
                    log.warning("CUDA load failed, falling back to CPU")
                    self._model = WhisperModel(
                        repo_id,
                        device="cpu",
                        compute_type="int8",
                    )
                    self._current_model_name = model_name
                    self._current_device = "cpu"
                    self._current_compute_type = "int8"
                    log.info("Model loaded on CPU fallback")
                else:
                    raise
            finally:
                self._loading = False

    def ensure_model_loaded(self, model_name: str = "tiny", device_preference: str = "auto"):
        """Ensure model is loaded, loading it if necessary.

        This enables lazy loading - the model is only loaded when first needed.
        If the model is already loaded with the requested configuration, this is a no-op.

        Args:
            model_name: Name of the Whisper model
            device_preference: "auto", "cpu", or "cuda"
        """
        # load_model() already checks if model is loaded with same config
        # and skips reloading if so (see lines 38-42)
        self.load_model(model_name, device_preference)

    def is_loading(self) -> bool:
        return self._loading

    def get_current_model(self) -> Optional[str]:
        return self._current_model_name

    def get_current_device(self) -> str:
        """Get the device currently being used."""
        return self._current_device or "cpu"

    def get_current_compute_type(self) -> str:
        """Get the compute type currently being used."""
        return self._current_compute_type or "int8"

    def transcribe(
        self,
        audio: np.ndarray,
        language: str = "auto",
    ) -> str:
        """Transcribe audio to text."""
        if self._model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        if len(audio) == 0:
            return ""

        # Ensure audio is float32 and normalized
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)

        # Normalize if needed
        max_val = np.abs(audio).max()
        if max_val > 1.0:
            audio = audio / max_val

        # Transcribe
        language_arg = None if language == "auto" else language

        log.debug("Audio stats", length=len(audio), max_amplitude=float(np.abs(audio).max()), mean_amplitude=float(np.abs(audio).mean()))

        segments, info = self._model.transcribe(
            audio,
            language=language_arg,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=500,  # Less aggressive silence detection
                speech_pad_ms=400,  # More padding around speech
            ),
        )

        # Combine all segments
        segments_list = list(segments)
        log.debug("Transcription segments", segment_count=len(segments_list))
        text_parts = [segment.text for segment in segments_list]
        text = " ".join(text_parts).strip()

        return text

    def unload_model(self):
        """Unload model to free memory."""
        self._cancel_idle_timer()
        with self._lock:
            self._model = None
            self._current_model_name = None
            self._current_device = None
            self._current_compute_type = None

    def start_idle_timer(self, timeout_seconds: int):
        """Start idle timer that will auto-unload model after timeout.

        Args:
            timeout_seconds: Number of seconds of inactivity before unloading model
        """
        self._cancel_idle_timer()
        if timeout_seconds > 0:
            self._idle_timer = threading.Timer(timeout_seconds, self._on_idle_timeout)
            self._idle_timer.daemon = True
            self._idle_timer.start()
            log.debug("Idle timer started", timeout=timeout_seconds)

    def _cancel_idle_timer(self):
        """Cancel any running idle timer."""
        if self._idle_timer is not None:
            self._idle_timer.cancel()
            self._idle_timer = None

    def _on_idle_timeout(self):
        """Called when idle timer expires."""
        log.info("Model idle timeout reached, unloading model")
        self.unload_model()
