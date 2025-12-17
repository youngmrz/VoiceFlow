from typing import Optional, Callable
import threading
import time
import os

from services.database import DatabaseService
from services.settings import SettingsService
from services.audio import AudioService
from services.transcription import TranscriptionService
from services.hotkey import HotkeyService
from services.clipboard import ClipboardService
from services.logger import get_logger

# Domain loggers for different concerns
model_log = get_logger("model")
audio_log = get_logger("audio")
window_log = get_logger("window")


class AppController:
    def __init__(self):
        # Initialize services
        self.db = DatabaseService()
        self.settings_service = SettingsService(self.db)
        self.audio_service = AudioService()
        self.transcription_service = TranscriptionService()
        self.hotkey_service = HotkeyService()
        self.clipboard_service = ClipboardService()

        # Model loading state
        self._model_loaded = False
        self._model_loading = False

        # Popup enabled state (disabled during onboarding)
        self._popup_enabled = True

        # Callbacks for UI
        self._on_recording_start: Optional[Callable[[], None]] = None
        self._on_recording_stop: Optional[Callable[[], None]] = None
        self._on_transcription_complete: Optional[Callable[[str], None]] = None
        self._on_amplitude: Optional[Callable[[float], None]] = None
        self._on_error: Optional[Callable[[str], None]] = None

        # Setup hotkey callbacks
        self.hotkey_service.set_callbacks(
            on_activate=self._handle_hotkey_activate,
            on_deactivate=self._handle_hotkey_deactivate,
        )

        # Setup audio amplitude callback
        self.audio_service.set_amplitude_callback(self._handle_amplitude)

    def set_ui_callbacks(
        self,
        on_recording_start: Callable[[], None] = None,
        on_recording_stop: Callable[[], None] = None,
        on_transcription_complete: Callable[[str], None] = None,
        on_amplitude: Callable[[float], None] = None,
        on_error: Callable[[str], None] = None,
    ):
        self._on_recording_start = on_recording_start
        self._on_recording_stop = on_recording_stop
        self._on_transcription_complete = on_transcription_complete
        self._on_amplitude = on_amplitude
        self._on_error = on_error

    def initialize(self):
        """Initialize the app - load model and start hotkey listener."""
        settings = self.settings_service.get_settings()

        # Set initial microphone
        mic_id = settings.microphone if settings.microphone >= 0 else None
        self.audio_service.set_device(mic_id)

        # Load whisper model in background
        def load_model():
            self._model_loading = True
            try:
                model_log.info("Loading model", model=settings.model)
                self.transcription_service.load_model(settings.model)
                self._model_loaded = True
                model_log.info("Model loaded successfully", model=settings.model)
            except Exception as e:
                model_log.error("Failed to load model", model=settings.model, error=str(e))
                if self._on_error:
                    self._on_error(f"Failed to load model: {e}")
            finally:
                self._model_loading = False

        threading.Thread(target=load_model, daemon=True).start()

        # Start hotkey listener
        self.hotkey_service.start()

        # Clean old history based on retention setting
        self.db.clear_old_history(settings.retention)

    def shutdown(self):
        """Clean shutdown."""
        self.hotkey_service.stop()
        self.transcription_service.unload_model()

    def _handle_hotkey_activate(self):
        """Called when hotkey is pressed."""
        # Don't activate during onboarding
        if not self._popup_enabled:
            audio_log.debug("Hotkey ignored - popup disabled")
            return

        if self._on_recording_start:
            self._on_recording_start()
        self.audio_service.start_recording()

    def _handle_hotkey_deactivate(self):
        """Called when hotkey is released."""
        if self._on_recording_stop:
            self._on_recording_stop()

        # Get recorded audio
        audio = self.audio_service.stop_recording()

        if len(audio) == 0:
            audio_log.warning("No audio recorded")
            return

        audio_log.info("Audio recorded", samples=len(audio))

        # Transcribe in background
        def transcribe():
            try:
                # Wait for model to be loaded (with timeout)
                wait_time = 0
                while not self._model_loaded and wait_time < 30:
                    if not self._model_loading:
                        model_log.warning("Model not loaded and not loading, skipping transcription")
                        if self._on_transcription_complete:
                            self._on_transcription_complete("")
                        return
                    model_log.info("Waiting for model to load", wait_seconds=wait_time)
                    time.sleep(1)
                    wait_time += 1

                if not self._model_loaded:
                    model_log.error("Model load timeout, skipping transcription")
                    if self._on_transcription_complete:
                        self._on_transcription_complete("")
                    return

                settings = self.settings_service.get_settings()
                model_log.info("Transcribing", language=settings.language)

                text = self.transcription_service.transcribe(
                    audio,
                    language=settings.language,
                )

                model_log.info("Transcription complete", text_length=len(text) if text else 0)

                if text:
                    # Paste at cursor
                    audio_log.debug("Pasting text at cursor")
                    self.clipboard_service.paste_at_cursor(text)

                    # Save to history
                    self.db.add_history(text)

                    if self._on_transcription_complete:
                        self._on_transcription_complete(text)
                else:
                    model_log.warning("No text transcribed (empty result)")
                    if self._on_transcription_complete:
                        self._on_transcription_complete("")

            except Exception as e:
                model_log.error("Transcription error", error=str(e))
                if self._on_error:
                    self._on_error(f"Transcription failed: {e}")
                # Still notify completion to reset UI state
                if self._on_transcription_complete:
                    self._on_transcription_complete("")

        threading.Thread(target=transcribe, daemon=True).start()

    def _handle_amplitude(self, amplitude: float):
        """Forward amplitude to UI."""
        if self._on_amplitude:
            self._on_amplitude(amplitude)

    # Settings methods for RPC
    def get_settings(self) -> dict:
        settings = self.settings_service.get_settings()
        return {
            "language": settings.language,
            "model": settings.model,
            "autoStart": settings.auto_start,
            "retention": settings.retention,
            "theme": settings.theme,
            "onboardingComplete": settings.onboarding_complete,
            "microphone": settings.microphone,
        }

    def update_settings(self, **kwargs) -> dict:
        # Convert camelCase to snake_case
        mapped = {}
        if "autoStart" in kwargs:
            mapped["auto_start"] = kwargs["autoStart"]
        if "onboardingComplete" in kwargs:
            mapped["onboarding_complete"] = kwargs["onboardingComplete"]
        for key in ["language", "model", "retention", "theme", "microphone"]:
            if key in kwargs:
                mapped[key] = kwargs[key]
        settings = self.settings_service.update_settings(**mapped)

        # Reload model if changed
        if "model" in mapped:
            def reload():
                self.transcription_service.load_model(mapped["model"])
            threading.Thread(target=reload, daemon=True).start()

        # Update microphone if changed
        if "microphone" in mapped:
            mic_id = mapped["microphone"] if mapped["microphone"] >= 0 else None
            self.audio_service.set_device(mic_id)

        return self.get_settings()

    # History methods for RPC
    def get_history(self, limit: int = 100, offset: int = 0, search: str = None) -> list:
        return self.db.get_history(limit, offset, search)

    def delete_history(self, history_id: int):
        self.db.delete_history(history_id)

    def get_stats(self) -> dict:
        return self.db.get_stats()

    # Options for UI
    def get_options(self) -> dict:
        return {
            "models": self.settings_service.get_available_models(),
            "languages": self.settings_service.get_available_languages(),
            "retentionOptions": self.settings_service.get_retention_options(),
            "themeOptions": self.settings_service.get_theme_options(),
            "microphones": self.audio_service.get_input_devices(),
        }

    def stop_recording(self):
        """Manually stop recording (called from stop button)."""
        audio_log.debug("Manual stop_recording called")
        self.hotkey_service.force_deactivate()

    def start_test_recording(self):
        """Start recording for onboarding test (no hotkey needed)."""
        audio_log.debug("Starting test recording")
        self.audio_service.start_recording()

    def stop_test_recording(self) -> dict:
        """Stop test recording, transcribe, and return result (no paste/history)."""
        audio_log.debug("Stopping test recording")
        audio = self.audio_service.stop_recording()

        if len(audio) == 0:
            audio_log.warning("No audio recorded in test")
            return {"success": False, "error": "No audio recorded", "transcript": ""}

        audio_log.info("Test audio recorded", samples=len(audio))

        # Wait for model if needed
        wait_time = 0
        while not self._model_loaded and wait_time < 10:
            if not self._model_loading:
                return {"success": False, "error": "Model not loaded", "transcript": ""}
            model_log.debug("Waiting for model", wait_seconds=wait_time)
            time.sleep(0.5)
            wait_time += 0.5

        if not self._model_loaded:
            return {"success": False, "error": "Model loading timeout", "transcript": ""}

        try:
            settings = self.settings_service.get_settings()
            text = self.transcription_service.transcribe(
                audio,
                language=settings.language,
            )
            model_log.info("Test transcription complete", text_length=len(text) if text else 0)
            return {"success": True, "transcript": text or ""}
        except Exception as e:
            model_log.error("Test transcription error", error=str(e))
            return {"success": False, "error": str(e), "transcript": ""}

    def open_data_folder(self):
        """Open the folder containing application data."""
        try:
            folder_path = str(self.db.db_path.parent)
            window_log.info("Opening data folder", path=folder_path)
            os.startfile(folder_path)
        except Exception as e:
            window_log.error("Failed to open data folder", error=str(e))

    def set_popup_enabled(self, enabled: bool):
        """Enable or disable the popup/hotkey functionality."""
        self._popup_enabled = enabled
        window_log.debug("Popup state changed", enabled=enabled)

    def reset_all_data(self):
        """Reset all data and return to fresh state."""
        window_log.info("Resetting all user data")
        self.db.reset_all_data()
        # Reset settings service cache
        self.settings_service._settings = None


# Singleton instance
_controller: Optional[AppController] = None


def get_controller() -> AppController:
    global _controller
    if _controller is None:
        _controller = AppController()
    return _controller
