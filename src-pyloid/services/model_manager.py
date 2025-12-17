"""
Model Manager service for downloading and managing Whisper models.

Provides:
- is_model_cached(): Check if model exists in cache
- get_model_info(): Get model metadata
- download_model(): Download with progress and cancellation support
- load_model(): Load already-downloaded model
- ensure_model_ready(): Download if needed + load

Uses faster_whisper's download_model() which uses huggingface_hub internally.
Cache location: ~/.cache/huggingface/hub/
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional
import threading
import time
import os

from services.logger import get_logger

log = get_logger("model")


# Model sizes in bytes (approximate download sizes)
# These are estimates based on the quantized int8 CT2 models from faster-whisper
MODEL_SIZES = {
    "tiny": 75_000_000,      # ~75 MB
    "base": 175_000_000,     # ~175 MB
    "small": 500_000_000,    # ~500 MB
    "medium": 1_530_000_000, # ~1.53 GB
    "large-v3": 3_090_000_000,  # ~3.09 GB
    "turbo": 1_600_000_000,  # ~1.6 GB (large-v3-turbo)
}

# Model name to HuggingFace repo ID mapping
# Most models follow the pattern Systran/faster-whisper-{name}
# but some (like turbo) are hosted elsewhere
MODEL_REPOS = {
    "tiny": "Systran/faster-whisper-tiny",
    "base": "Systran/faster-whisper-base",
    "small": "Systran/faster-whisper-small",
    "medium": "Systran/faster-whisper-medium",
    "large-v3": "Systran/faster-whisper-large-v3",
    "turbo": "deepdml/faster-whisper-large-v3-turbo-ct2",
}


@dataclass
class CancelToken:
    """Token for cancelling long-running operations."""
    _cancelled: bool = False

    def cancel(self) -> None:
        """Request cancellation of the operation."""
        self._cancelled = True

    def is_cancelled(self) -> bool:
        """Check if cancellation has been requested."""
        return self._cancelled


@dataclass
class ModelInfo:
    """Information about a Whisper model."""
    name: str
    size_bytes: int
    cached: bool


@dataclass
class DownloadProgress:
    """Progress information for model downloads."""
    model_name: str
    percent: float
    downloaded_bytes: int
    total_bytes: int
    speed_bps: float
    eta_seconds: float


class ProgressTracker:
    """
    A tqdm-compatible class that tracks download progress.

    Used as tqdm_class parameter for faster_whisper.download_model().
    """

    def __init__(
        self,
        model_name: str,
        on_progress: Callable[[DownloadProgress], None],
        cancel_token: CancelToken,
        total: int = 0,
        **kwargs
    ):
        self.model_name = model_name
        self.on_progress = on_progress
        self.cancel_token = cancel_token
        self.total = total
        self.n = 0
        self._start_time = time.time()
        self._last_update_time = self._start_time

    def update(self, n: int = 1):
        """Update progress by n bytes."""
        if self.cancel_token.is_cancelled():
            raise DownloadCancelledError("Download cancelled by user")

        self.n += n
        now = time.time()

        # Throttle updates to avoid overwhelming the UI
        if now - self._last_update_time < 0.1:  # Max 10 updates per second
            return

        self._last_update_time = now

        # Calculate progress
        elapsed = now - self._start_time
        speed = self.n / elapsed if elapsed > 0 else 0
        remaining = self.total - self.n
        eta = remaining / speed if speed > 0 else 0
        percent = (self.n / self.total * 100) if self.total > 0 else 0

        progress = DownloadProgress(
            model_name=self.model_name,
            percent=percent,
            downloaded_bytes=self.n,
            total_bytes=self.total,
            speed_bps=speed,
            eta_seconds=eta
        )

        try:
            self.on_progress(progress)
        except Exception as e:
            log.warning("Progress callback error", error=str(e))

    def close(self):
        """Close the progress tracker."""
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class DownloadCancelledError(Exception):
    """Raised when a download is cancelled."""
    pass


class ModelManager:
    """
    Manages Whisper model downloading and caching.

    Uses faster_whisper's download_model() which stores models in
    the huggingface cache directory (~/.cache/huggingface/hub/).
    """

    def __init__(self):
        self._download_lock = threading.Lock()

    def get_cache_path(self) -> Path:
        """Get the huggingface cache directory path."""
        # huggingface_hub uses this environment variable or default
        cache_dir = os.environ.get("HF_HOME")
        if cache_dir:
            return Path(cache_dir) / "hub"

        # Default cache location
        return Path.home() / ".cache" / "huggingface" / "hub"

    def _get_repo_id(self, model_name: str) -> str:
        """Get the HuggingFace repo ID for a model name."""
        return MODEL_REPOS.get(model_name, f"Systran/faster-whisper-{model_name}")

    def _get_cache_dir_name(self, model_name: str) -> str:
        """Get the cache directory name for a model (converts repo_id to dir name)."""
        repo_id = self._get_repo_id(model_name)
        # HuggingFace converts repo_id like "owner/repo" to "models--owner--repo"
        return f"models--{repo_id.replace('/', '--')}"

    def is_model_cached(self, model_name: str) -> bool:
        """
        Check if a model is already downloaded and cached.

        Args:
            model_name: Name of the model (tiny, base, small, medium, large-v3, turbo)

        Returns:
            True if the model is cached, False otherwise.
        """
        try:
            cache_path = self.get_cache_path()
            model_dir_name = self._get_cache_dir_name(model_name)
            model_path = cache_path / model_dir_name

            if not model_path.exists():
                return False

            # Check for snapshots directory which contains the actual model files
            snapshots_dir = model_path / "snapshots"
            if not snapshots_dir.exists():
                return False

            # Check if there's at least one snapshot with model files
            for snapshot in snapshots_dir.iterdir():
                if snapshot.is_dir():
                    # Check for model.bin file which is required
                    model_bin = snapshot / "model.bin"
                    if model_bin.exists():
                        return True

            return False

        except Exception as e:
            log.warning("Error checking model cache", model=model_name, error=str(e))
            return False

    def get_model_info(self, model_name: str) -> ModelInfo:
        """
        Get information about a model.

        Args:
            model_name: Name of the model

        Returns:
            ModelInfo with name, size, and cache status
        """
        size_bytes = MODEL_SIZES.get(model_name, 0)
        cached = self.is_model_cached(model_name)

        return ModelInfo(
            name=model_name,
            size_bytes=size_bytes,
            cached=cached
        )

    def download_model(
        self,
        model_name: str,
        on_progress: Callable[[DownloadProgress], None],
        cancel_token: CancelToken
    ) -> bool:
        """
        Download a model with progress reporting and cancellation support.

        Args:
            model_name: Name of the model to download
            on_progress: Callback for progress updates
            cancel_token: Token to cancel the download

        Returns:
            True if download completed successfully, False if cancelled or failed
        """
        if cancel_token.is_cancelled():
            log.info("Download cancelled before start", model=model_name)
            return False

        with self._download_lock:
            return self._do_download(model_name, on_progress, cancel_token)

    def _do_download(
        self,
        model_name: str,
        on_progress: Callable[[DownloadProgress], None],
        cancel_token: CancelToken
    ) -> bool:
        """
        Internal download implementation.

        Uses huggingface_hub.snapshot_download() with a progress callback.
        Runs download in a daemon thread so cancellation can abandon it.

        Args:
            model_name: Name of the model to download
            on_progress: Callback for progress updates
            cancel_token: Token to cancel the download

        Returns:
            True if successful, False if cancelled or failed
        """
        from huggingface_hub import snapshot_download
        from tqdm import tqdm as tqdm_base

        log.info("Starting model download", model=model_name)

        # Get the correct repo ID for this model
        repo_id = self._get_repo_id(model_name)

        # Track total bytes downloaded across all files
        total_size = MODEL_SIZES.get(model_name, 0)
        downloaded_bytes = [0]  # Use list to allow mutation in nested class
        start_time = [time.time()]
        last_update_time = [start_time[0]]

        # Result holder for the download thread
        result = {"success": False, "error": None}

        def send_progress():
            """Send progress update to callback."""
            now = time.time()
            # Throttle updates to max 10 per second
            if now - last_update_time[0] < 0.1:
                return
            last_update_time[0] = now

            elapsed = now - start_time[0]
            speed = downloaded_bytes[0] / elapsed if elapsed > 0 else 0
            remaining = total_size - downloaded_bytes[0]
            eta = remaining / speed if speed > 0 else 0
            percent = (downloaded_bytes[0] / total_size * 100) if total_size > 0 else 0

            try:
                on_progress(DownloadProgress(
                    model_name=model_name,
                    percent=min(percent, 99.9),  # Cap at 99.9 until truly complete
                    downloaded_bytes=downloaded_bytes[0],
                    total_bytes=total_size,
                    speed_bps=speed,
                    eta_seconds=eta
                ))
            except Exception as e:
                log.warning("Progress callback error", error=str(e))

        # Custom tqdm class that tracks download progress
        class DownloadProgressBar(tqdm_base):
            def __init__(self, *args, **kwargs):
                # Filter out any unexpected kwargs that tqdm doesn't accept
                kwargs.pop('name', None)
                super().__init__(*args, **kwargs)

            def update(self, n=1):
                super().update(n)
                # Only count byte updates (not file count updates)
                if n > 100:  # Likely a byte update, not file count
                    downloaded_bytes[0] += n
                    send_progress()

        def download_thread():
            """Run the download in a separate thread."""
            try:
                snapshot_download(
                    repo_id,
                    tqdm_class=DownloadProgressBar,
                )
                result["success"] = True
            except Exception as e:
                result["error"] = str(e)

        # Start download in daemon thread
        thread = threading.Thread(target=download_thread, daemon=True)
        thread.start()

        # Wait for completion while checking for cancellation
        while thread.is_alive():
            if cancel_token.is_cancelled():
                log.info("Model download cancelled by user", model=model_name)
                # Thread is daemon, so it will be abandoned when we return
                return False
            thread.join(timeout=0.1)  # Check every 100ms

        # Check result
        if result["success"]:
            log.info("Model download completed", model=model_name)

            # Send final 100% progress
            on_progress(DownloadProgress(
                model_name=model_name,
                percent=100.0,
                downloaded_bytes=total_size,
                total_bytes=total_size,
                speed_bps=0,
                eta_seconds=0
            ))
            return True
        else:
            log.error("Model download failed", model=model_name, error=result["error"])
            return False

    def load_model(self, model_name: str):
        """
        Load an already-downloaded model.

        Args:
            model_name: Name of the model to load

        Returns:
            WhisperModel instance

        Raises:
            RuntimeError: If model is not cached
        """
        if not self.is_model_cached(model_name):
            raise RuntimeError(f"Model '{model_name}' is not cached. Download it first.")

        from faster_whisper import WhisperModel

        # Use repo_id for non-standard models (like turbo from deepdml)
        model_id = self._get_repo_id(model_name)

        log.info("Loading model", model=model_name, repo_id=model_id)
        model = WhisperModel(
            model_id,
            device="cpu",
            compute_type="int8"
        )
        log.info("Model loaded successfully", model=model_name)

        return model

    def ensure_model_ready(
        self,
        model_name: str,
        on_progress: Optional[Callable[[DownloadProgress], None]] = None,
        cancel_token: Optional[CancelToken] = None
    ):
        """
        Ensure a model is downloaded and load it.

        Downloads the model if not cached, then loads it.

        Args:
            model_name: Name of the model
            on_progress: Optional callback for download progress
            cancel_token: Optional token to cancel the download

        Returns:
            WhisperModel instance

        Raises:
            RuntimeError: If download fails or is cancelled
        """
        if not self.is_model_cached(model_name):
            log.info("Model not cached, downloading", model=model_name)

            # Set up defaults if not provided
            if on_progress is None:
                on_progress = lambda p: None
            if cancel_token is None:
                cancel_token = CancelToken()

            success = self.download_model(model_name, on_progress, cancel_token)

            if not success:
                raise RuntimeError(f"Failed to download model '{model_name}'")

        return self.load_model(model_name)


# Singleton instance
_model_manager: Optional[ModelManager] = None


def get_model_manager() -> ModelManager:
    """Get the singleton ModelManager instance."""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager
