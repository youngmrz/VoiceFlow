import numpy as np
import sounddevice as sd
from typing import Optional, Callable
import threading
import queue
from services.logger import debug, info, warning


class AudioService:
    SAMPLE_RATE = 16000  # Whisper expects 16kHz
    CHANNELS = 1  # Mono
    DTYPE = np.float32

    def __init__(self):
        self._recording = False
        self._audio_queue = queue.Queue()
        self._audio_data = []
        self._stream: Optional[sd.InputStream] = None
        self._amplitude_callback: Optional[Callable[[float], None]] = None
        self._device_id: Optional[int] = None  # None = default device

    def set_device(self, device_id: Optional[int]):
        """Set the input device to use. None for default."""
        self._device_id = device_id
        info(f"Audio device set to: {device_id}")

    def set_amplitude_callback(self, callback: Callable[[float], None]):
        """Set callback to receive amplitude values for visualization."""
        self._amplitude_callback = callback

    def _audio_callback(self, indata, frames, time, status):
        if status:
            warning(f"Audio status: {status}")

        # Copy audio data
        audio_chunk = indata.copy().flatten()
        self._audio_queue.put(audio_chunk)

        # Calculate amplitude for visualization
        if self._amplitude_callback:
            amplitude = float(np.abs(audio_chunk).mean())
            self._amplitude_callback(amplitude)

    def start_recording(self):
        if self._recording:
            return

        self._recording = True
        self._audio_data = []

        # Clear queue
        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
            except queue.Empty:
                break

        info(f"Starting recording with device: {self._device_id}")
        self._stream = sd.InputStream(
            samplerate=self.SAMPLE_RATE,
            channels=self.CHANNELS,
            dtype=self.DTYPE,
            callback=self._audio_callback,
            blocksize=1024,
            device=self._device_id,
        )
        self._stream.start()
        debug("Recording started")

    def stop_recording(self) -> np.ndarray:
        if not self._recording:
            return np.array([], dtype=self.DTYPE)

        self._recording = False

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        # Collect all audio from queue
        while not self._audio_queue.empty():
            try:
                chunk = self._audio_queue.get_nowait()
                self._audio_data.append(chunk)
            except queue.Empty:
                break

        if not self._audio_data:
            return np.array([], dtype=self.DTYPE)

        # Concatenate all chunks
        audio = np.concatenate(self._audio_data)
        self._audio_data = []

        return audio

    def is_recording(self) -> bool:
        return self._recording

    @staticmethod
    def get_input_devices() -> list:
        """Get list of available input devices."""
        devices = sd.query_devices()
        input_devices = []
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                input_devices.append({
                    'id': i,
                    'name': device['name'],
                    'channels': device['max_input_channels'],
                })
        return input_devices
