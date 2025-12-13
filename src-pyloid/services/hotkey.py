import keyboard
from typing import Callable, Optional
import threading
from services.logger import debug, info


class HotkeyService:
    def __init__(self):
        self._on_activate: Optional[Callable[[], None]] = None
        self._on_deactivate: Optional[Callable[[], None]] = None
        self._hotkey_active = False
        self._running = False
        self._max_recording_timer: Optional[threading.Timer] = None

        # Hotkey combination: Ctrl + Win
        self._hotkey = 'ctrl+win'

    def set_callbacks(
        self,
        on_activate: Callable[[], None],
        on_deactivate: Callable[[], None],
    ):
        """Set callbacks for hotkey press and release."""
        self._on_activate = on_activate
        self._on_deactivate = on_deactivate

    def _on_hotkey_press(self):
        """Called when hotkey is pressed."""
        if not self._hotkey_active:
            self._hotkey_active = True
            info("Hotkey activated! Calling on_activate...")
            if self._on_activate:
                self._on_activate()
            self._start_max_timer()

    def _on_hotkey_release(self):
        """Called when hotkey is released."""
        if self._hotkey_active:
            self._deactivate()

    def _start_max_timer(self):
        """Start a timer to auto-stop recording after 60 seconds."""
        self._cancel_max_timer()
        self._max_recording_timer = threading.Timer(60.0, self._deactivate)
        self._max_recording_timer.daemon = True
        self._max_recording_timer.start()

    def _cancel_max_timer(self):
        """Cancel the max recording timer."""
        if self._max_recording_timer:
            self._max_recording_timer.cancel()
            self._max_recording_timer = None

    def _deactivate(self):
        """Deactivate the hotkey and call callback."""
        if not self._hotkey_active:
            return
        self._hotkey_active = False
        self._cancel_max_timer()
        info("Hotkey deactivated! Calling on_deactivate...")
        if self._on_deactivate:
            self._on_deactivate()

    def force_deactivate(self):
        """Manually force deactivation (e.g., from stop button)."""
        debug("Force deactivate called")
        self._deactivate()

    def start(self):
        """Start listening for hotkeys."""
        if self._running:
            return

        self._running = True

        # Register hotkey with keyboard library
        # Use on_press_key for activation and monitor for release
        info(f"Registering hotkey: {self._hotkey}")

        # keyboard library handles Win key properly on Windows
        keyboard.add_hotkey(self._hotkey, self._on_hotkey_press, suppress=False)

        # Monitor key release to detect when user lets go
        keyboard.on_release_key('ctrl', self._check_release)
        keyboard.on_release_key('win', self._check_release)
        keyboard.on_release_key('windows', self._check_release)
        keyboard.on_release_key('left windows', self._check_release)
        keyboard.on_release_key('right windows', self._check_release)

    def _check_release(self, event):
        """Check if hotkey should be deactivated on key release."""
        if self._hotkey_active:
            # Check if either Ctrl or Win is no longer pressed
            ctrl_pressed = keyboard.is_pressed('ctrl')
            win_pressed = keyboard.is_pressed('win') or keyboard.is_pressed('windows')

            debug(f"Key released: {event.name}, ctrl={ctrl_pressed}, win={win_pressed}")

            if not ctrl_pressed or not win_pressed:
                self._on_hotkey_release()

    def stop(self):
        """Stop listening for hotkeys."""
        self._running = False
        keyboard.unhook_all()
        self._cancel_max_timer()
        self._hotkey_active = False

    def is_running(self) -> bool:
        return self._running
