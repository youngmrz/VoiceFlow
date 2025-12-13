from pyloid.tray import TrayEvent
from pyloid.utils import get_production_path, is_production
from pyloid.serve import pyloid_serve
from pyloid import Pyloid

from server import server, register_onboarding_complete_callback, register_data_reset_callback
from app_controller import get_controller
from services.logger import setup_logger, info, error, debug, exception

# Setup logging first thing
logger = setup_logger()

# Initialize app
app = Pyloid(app_name="VoiceFlow", single_instance=True, server=server)

app.set_icon(get_production_path("src-pyloid/icons/icon.png"))
app.set_tray_icon(get_production_path("src-pyloid/icons/icon.png"))

# Initialize controller
controller = get_controller()

# Store reference to popup window
popup_window = None


def show_dashboard():
    app.show_and_focus_main_window()


def open_settings():
    app.show_and_focus_main_window()
    # Frontend will handle showing settings tab via URL hash or event


# Tray setup
app.set_tray_actions({
    TrayEvent.DoubleClick: show_dashboard,
})

app.set_tray_menu_items([
    {"label": "Open Dashboard", "callback": show_dashboard},
    {"label": "Settings", "callback": open_settings},
    {"label": "Quit", "callback": app.quit},
])


# Recording popup window management
import json
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor

# Popup dimensions for different states
POPUP_IDLE_WIDTH = 110
POPUP_IDLE_HEIGHT = 18
POPUP_ACTIVE_WIDTH = 190
POPUP_ACTIVE_HEIGHT = 50

# Screen info cache
_screen_width = 1920
_screen_height = 1080


def get_screen_info():
    """Get and cache screen dimensions."""
    global _screen_width, _screen_height
    try:
        monitors = app.get_all_monitors()
        if monitors:
            primary = monitors[0]
            geometry = primary.geometry()
            if isinstance(geometry, dict):
                _screen_width = geometry.get('width', 1920)
                _screen_height = geometry.get('height', 1080)
            else:
                _screen_width = geometry.width() if hasattr(geometry, 'width') else 1920
                _screen_height = geometry.height() if hasattr(geometry, 'height') else 1080
            info(f"Screen size: {_screen_width}x{_screen_height}")
    except Exception as e:
        error(f"Failed to get screen info: {e}")


def resize_popup(width: int, height: int):
    """Resize and reposition popup window."""
    global popup_window
    if popup_window is None:
        return

    try:
        # Resize the window
        popup_window.set_size(width, height)

        # Recenter horizontally, keep at bottom
        popup_x = (_screen_width - width) // 2
        popup_y = _screen_height - 100
        popup_window.set_position(popup_x, popup_y)

        # Ensure stay-on-top is maintained after resize
        qwindow = popup_window._window._window
        qwindow.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        qwindow.show()
    except Exception as e:
        error(f"Failed to resize popup: {e}")


def init_popup():
    """Initialize the recording popup."""
    global popup_window
    info("init_popup called")

    try:
        if popup_window is None:
            # Get screen info first
            get_screen_info()

            # Create window with idle size initially
            # frame=False makes it frameless, transparent=True enables transparency
            popup_window = app.create_window(
                title="Recording",
                width=POPUP_IDLE_WIDTH,
                height=POPUP_IDLE_HEIGHT,
                frame=False,
                transparent=True,
            )

            # Access internal Qt objects for transparency setup
            qwindow = popup_window._window._window
            webview = popup_window._window.web_view

            # CRITICAL: Set background color BEFORE loading URL
            # Qt WebEngineView requires this order to avoid black/white background
            webview.page().setBackgroundColor(QColor(0, 0, 0, 0))

            # Load the URL
            if is_production():
                url = pyloid_serve(directory=get_production_path("dist-front"))
                popup_window.load_url(f"{url}#/popup")
            else:
                popup_window.load_url("http://localhost:5173#/popup")

            # Position at bottom center
            popup_x = (_screen_width - POPUP_IDLE_WIDTH) // 2
            popup_y = _screen_height - 100
            popup_window.set_position(popup_x, popup_y)

            # Set window flags for stay-on-top and no taskbar icon
            # Must be done before show() and requires hide/show cycle
            qwindow.setWindowFlags(
                Qt.FramelessWindowHint |
                Qt.WindowStaysOnTopHint |
                Qt.Tool  # Prevents taskbar icon
            )

            # Show the window
            popup_window.show()
            info("Popup window created and shown")

            # Send initial idle state after a brief delay to ensure page is loaded
            def send_initial_state():
                send_popup_event('popup-state', {'state': 'idle'})
                info("Sent initial idle state to popup")

            QTimer.singleShot(200, send_initial_state)
        else:
            info("Popup window already exists, skipping creation")
    except Exception as e:
        exception(f"Failed to initialize popup: {e}")

def send_popup_event(name, detail):
    """Send event to popup window using Pyloid's invoke method."""
    global popup_window
    if popup_window:
        try:
            popup_window.invoke(name, detail)
        except Exception as e:
            error(f"Failed to send popup event: {e}")

def on_recording_start():
    info("Recording started")
    # Resize to active size for recording
    resize_popup(POPUP_ACTIVE_WIDTH, POPUP_ACTIVE_HEIGHT)
    send_popup_event('popup-state', {'state': 'recording'})

def on_recording_stop():
    info("Recording stopped - now processing")
    # Keep active size during processing
    send_popup_event('popup-state', {'state': 'processing'})

def on_transcription_complete(text: str):
    info(f"Transcription complete: {text[:50]}...")
    # Resize back to idle size
    resize_popup(POPUP_IDLE_WIDTH, POPUP_IDLE_HEIGHT)
    send_popup_event('popup-state', {'state': 'idle'})

def on_amplitude(amp: float):
    # Only send if recording? Or always?
    # Visualizer is usually only active during recording.
    send_popup_event('amplitude', amp)


def on_onboarding_complete():
    """Called when user completes onboarding - hide main window, show popup."""
    global window
    info("Onboarding complete - initializing popup")
    # Hide the main window (user can reopen via tray)
    if window:
        window.hide()
    # Initialize the popup directly (QTimer doesn't work reliably from async RPC context)
    init_popup()


def hide_popup():
    """Hide the popup window (used when returning to onboarding)."""
    global popup_window
    info("Hiding popup window")
    if popup_window:
        try:
            popup_window.hide()
            popup_window.close()
            popup_window = None
            info("Popup window hidden and destroyed")
        except Exception as e:
            error(f"Failed to hide popup: {e}")


def on_data_reset():
    """Called when user resets all data - show main window, hide popup."""
    global window
    info("Data reset - returning to onboarding")
    # Hide the popup
    hide_popup()
    # Show the main window for onboarding
    if window:
        window.show()
        try:
            qwindow = window._window._window
            qwindow.showMaximized()
        except Exception as e:
            error(f"Could not maximize window: {e}")


# Register callbacks
register_onboarding_complete_callback(on_onboarding_complete)
register_data_reset_callback(on_data_reset)

# Set UI callbacks
controller.set_ui_callbacks(
    on_recording_start=on_recording_start,
    on_recording_stop=on_recording_stop,
    on_transcription_complete=on_transcription_complete,
    on_amplitude=on_amplitude,
)

# Initialize controller (load model, start hotkey listener)
controller.initialize()


# Check if onboarding is complete
settings = controller.get_settings()
onboarding_complete = settings.get("onboardingComplete", False)
info(f"Startup: onboarding_complete={onboarding_complete}")

# Main window setup
if is_production():
    url = pyloid_serve(directory=get_production_path("dist-front"))
    window = app.create_window(title="VoiceFlow")
    window.load_url(url)
else:
    window = app.create_window(title="VoiceFlow", dev_tools=True)
    window.load_url("http://localhost:5173")

if onboarding_complete:
    # Start minimized - user can open via tray icon
    info("Onboarding already complete - hiding window and scheduling popup init")
    window.hide()
    # Initialize popup after a short delay
    QTimer.singleShot(500, init_popup)
else:
    # Show maximized for onboarding experience
    window.show()
    window.set_size(1280, 800)  # Good default size
    try:
        # Try to maximize the window
        qwindow = window._window._window
        qwindow.showMaximized()
    except Exception as e:
        error(f"Could not maximize window: {e}")
    # Don't initialize popup during onboarding

app.run()

# Cleanup on exit
controller.shutdown()
