import threading
from typing import Callable, Optional
from services.logger import get_logger

log = get_logger("idle_timer")


class IdleTimerService:
    """Service to track idle time and trigger callbacks after timeout."""

    def __init__(self):
        self._timer: Optional[threading.Timer] = None
        self._timeout: int = 300  # Default 5 minutes
        self._callback: Optional[Callable[[], None]] = None
        self._running: bool = False
        self._lock = threading.Lock()

    def configure(self, timeout: int, callback: Callable[[], None]):
        """Configure the idle timer with timeout and callback.

        Args:
            timeout: Timeout in seconds before callback is triggered
            callback: Function to call when timer expires
        """
        with self._lock:
            self._timeout = timeout
            self._callback = callback
            log.info("Idle timer configured", timeout=timeout)

    def start(self):
        """Start or restart the idle timer."""
        with self._lock:
            if not self._callback:
                log.warning("Cannot start timer without callback")
                return

            # Cancel existing timer if running
            if self._timer:
                self._timer.cancel()

            # Create and start new timer
            self._timer = threading.Timer(self._timeout, self._on_timeout)
            self._timer.daemon = True
            self._timer.start()
            self._running = True
            log.debug("Idle timer started", timeout=self._timeout)

    def reset(self):
        """Reset the idle timer (restart from 0)."""
        if not self._running:
            log.debug("Timer not running, starting new timer")
            self.start()
            return

        with self._lock:
            # Cancel current timer and start fresh
            if self._timer:
                self._timer.cancel()

            if self._callback:
                self._timer = threading.Timer(self._timeout, self._on_timeout)
                self._timer.daemon = True
                self._timer.start()
                log.debug("Idle timer reset", timeout=self._timeout)

    def stop(self):
        """Stop the idle timer."""
        with self._lock:
            if self._timer:
                self._timer.cancel()
                self._timer = None
            self._running = False
            log.debug("Idle timer stopped")

    def is_running(self) -> bool:
        """Check if timer is currently running."""
        return self._running

    def _on_timeout(self):
        """Internal callback when timer expires."""
        log.info("Idle timeout reached", timeout=self._timeout)
        self._running = False

        if self._callback:
            try:
                self._callback()
            except Exception as e:
                log.error("Error in idle timer callback", error=str(e))


# Singleton instance
_idle_timer_instance: Optional[IdleTimerService] = None


def get_idle_timer() -> IdleTimerService:
    """Get the singleton IdleTimerService instance."""
    global _idle_timer_instance
    if _idle_timer_instance is None:
        _idle_timer_instance = IdleTimerService()
    return _idle_timer_instance
