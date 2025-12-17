import pyperclip
import pyautogui
import time
from services.logger import get_logger

log = get_logger("clipboard")


class ClipboardService:
    def __init__(self):
        # Disable pyautogui fail-safe (moving mouse to corner won't abort)
        pyautogui.FAILSAFE = False
        # Small pause between pyautogui actions
        pyautogui.PAUSE = 0.05

    def copy_to_clipboard(self, text: str):
        """Copy text to clipboard."""
        pyperclip.copy(text)

    def paste_at_cursor(self, text: str):
        """Copy text to clipboard and paste at current cursor position."""
        log.debug("Paste at cursor called", text_length=len(text))

        # Save current clipboard content
        try:
            original_clipboard = pyperclip.paste()
        except Exception:
            original_clipboard = ""

        # Copy our text
        pyperclip.copy(text)
        log.debug("Text copied to clipboard")

        # Small delay to ensure clipboard is updated
        time.sleep(0.1)

        # Simulate Ctrl+V
        log.debug("Simulating Ctrl+V")
        pyautogui.hotkey('ctrl', 'v')
        log.debug("Paste command sent")

        # Small delay before restoring
        time.sleep(0.1)

        # Optionally restore original clipboard
        # Commented out as it may interfere with user expectation
        # pyperclip.copy(original_clipboard)

    def get_clipboard(self) -> str:
        """Get current clipboard content."""
        try:
            return pyperclip.paste()
        except Exception:
            return ""
