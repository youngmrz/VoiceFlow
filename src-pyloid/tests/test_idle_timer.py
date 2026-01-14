import pytest
import time
from services.idle_timer import IdleTimerService, get_idle_timer


class TestIdleTimerService:
    def test_initial_state_not_running(self):
        """Idle timer starts in non-running state."""
        service = IdleTimerService()
        assert service.is_running() == False

    def test_configure_sets_timeout_and_callback(self):
        """Can configure timeout and callback."""
        service = IdleTimerService()
        callback_called = []

        def callback():
            callback_called.append(True)

        service.configure(timeout=1, callback=callback)
        # Should not raise, configuration stored internally

    def test_start_without_callback_does_not_run(self):
        """Starting without callback configured does nothing."""
        service = IdleTimerService()
        service.start()

        assert service.is_running() == False

    def test_start_with_callback_changes_state(self):
        """Starting with callback changes state to running."""
        service = IdleTimerService()
        service.configure(timeout=10, callback=lambda: None)
        service.start()

        assert service.is_running() == True

        # Cleanup
        service.stop()

    def test_stop_changes_state_to_not_running(self):
        """Stopping the timer changes state back to not running."""
        service = IdleTimerService()
        service.configure(timeout=10, callback=lambda: None)
        service.start()
        service.stop()

        assert service.is_running() == False

    def test_stop_without_start_is_safe(self):
        """Stopping without starting doesn't cause issues."""
        service = IdleTimerService()
        service.stop()  # Should not error

        assert service.is_running() == False

    def test_callback_is_called_after_timeout(self):
        """Callback is called when timer expires."""
        service = IdleTimerService()
        callback_called = []

        def callback():
            callback_called.append(True)

        service.configure(timeout=0.1, callback=callback)
        service.start()

        # Wait for timeout
        time.sleep(0.2)

        assert len(callback_called) == 1
        assert service.is_running() == False

    def test_callback_not_called_before_timeout(self):
        """Callback is not called before timer expires."""
        service = IdleTimerService()
        callback_called = []

        def callback():
            callback_called.append(True)

        service.configure(timeout=1, callback=callback)
        service.start()

        # Wait less than timeout
        time.sleep(0.1)

        assert len(callback_called) == 0
        assert service.is_running() == True

        # Cleanup
        service.stop()

    def test_stop_cancels_pending_callback(self):
        """Stopping the timer prevents callback from firing."""
        service = IdleTimerService()
        callback_called = []

        def callback():
            callback_called.append(True)

        service.configure(timeout=0.2, callback=callback)
        service.start()

        # Stop before timeout
        time.sleep(0.05)
        service.stop()

        # Wait past original timeout
        time.sleep(0.2)

        assert len(callback_called) == 0
        assert service.is_running() == False

    def test_reset_restarts_timer(self):
        """Reset restarts the timer from 0."""
        service = IdleTimerService()
        callback_called = []

        def callback():
            callback_called.append(True)

        service.configure(timeout=0.15, callback=callback)
        service.start()

        # Wait partway through timeout
        time.sleep(0.1)

        # Reset timer
        service.reset()

        # Wait another 0.1s (total 0.2s from start, but 0.1s from reset)
        time.sleep(0.1)

        # Callback should not have fired yet (reset extended the time)
        assert len(callback_called) == 0
        assert service.is_running() == True

        # Wait for new timeout to complete
        time.sleep(0.1)

        assert len(callback_called) == 1
        assert service.is_running() == False

    def test_reset_without_start_starts_timer(self):
        """Reset on non-running timer starts it."""
        service = IdleTimerService()
        callback_called = []

        def callback():
            callback_called.append(True)

        service.configure(timeout=0.1, callback=callback)

        # Reset without start
        service.reset()

        assert service.is_running() == True

        # Wait for timeout
        time.sleep(0.15)

        assert len(callback_called) == 1

    def test_start_twice_restarts_timer(self):
        """Starting twice restarts the timer."""
        service = IdleTimerService()
        callback_called = []

        def callback():
            callback_called.append(True)

        service.configure(timeout=0.15, callback=callback)
        service.start()

        # Wait partway through timeout
        time.sleep(0.1)

        # Start again
        service.start()

        # Wait another 0.1s (total 0.2s from first start, but 0.1s from second)
        time.sleep(0.1)

        # Callback should not have fired yet
        assert len(callback_called) == 0

        # Wait for new timeout to complete
        time.sleep(0.1)

        assert len(callback_called) == 1

    def test_callback_exception_does_not_crash(self):
        """Exception in callback doesn't crash the service."""
        service = IdleTimerService()

        def bad_callback():
            raise ValueError("Test exception")

        service.configure(timeout=0.1, callback=bad_callback)
        service.start()

        # Wait for timeout
        time.sleep(0.15)

        # Should not crash, timer should be stopped
        assert service.is_running() == False

    def test_reconfigure_while_running(self):
        """Can reconfigure timeout and callback while running."""
        service = IdleTimerService()
        first_called = []
        second_called = []

        def first_callback():
            first_called.append(True)

        def second_callback():
            second_called.append(True)

        service.configure(timeout=10, callback=first_callback)
        service.start()

        # Reconfigure with shorter timeout
        service.configure(timeout=0.1, callback=second_callback)
        service.start()  # Need to restart for new config

        # Wait for timeout
        time.sleep(0.15)

        # Only second callback should fire
        assert len(first_called) == 0
        assert len(second_called) == 1

    def test_multiple_resets_work_correctly(self):
        """Multiple resets work correctly."""
        service = IdleTimerService()
        callback_called = []

        def callback():
            callback_called.append(True)

        service.configure(timeout=0.1, callback=callback)
        service.start()

        # Reset multiple times
        time.sleep(0.05)
        service.reset()
        time.sleep(0.05)
        service.reset()
        time.sleep(0.05)
        service.reset()

        # Callback should not have fired yet
        assert len(callback_called) == 0

        # Wait for final timeout
        time.sleep(0.12)

        assert len(callback_called) == 1


class TestGetIdleTimer:
    def test_returns_singleton_instance(self):
        """get_idle_timer returns the same instance."""
        timer1 = get_idle_timer()
        timer2 = get_idle_timer()

        assert timer1 is timer2

    def test_singleton_maintains_state(self):
        """Singleton maintains state across calls."""
        timer = get_idle_timer()
        timer.configure(timeout=10, callback=lambda: None)
        timer.start()

        # Get instance again
        same_timer = get_idle_timer()

        assert same_timer.is_running() == True

        # Cleanup
        timer.stop()
