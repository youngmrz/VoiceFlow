from pyloid.rpc import PyloidRPC, RPCContext
from app_controller import get_controller
from services.logger import debug

server = PyloidRPC()

# Callbacks that main.py will register
_on_onboarding_complete = None
_on_data_reset = None


def register_onboarding_complete_callback(callback):
    """Register callback to be called when onboarding completes."""
    global _on_onboarding_complete
    _on_onboarding_complete = callback


def register_data_reset_callback(callback):
    """Register callback to be called when data is reset."""
    global _on_data_reset
    _on_data_reset = callback


@server.method()
async def get_settings():
    controller = get_controller()
    return controller.get_settings()


@server.method()
async def update_settings(
    language: str = None,
    model: str = None,
    autoStart: bool = None,
    retention: int = None,
    theme: str = None,
    onboardingComplete: bool = None,
    microphone: int = None,
):
    controller = get_controller()
    kwargs = {}
    if language is not None:
        kwargs["language"] = language
    if model is not None:
        kwargs["model"] = model
    if autoStart is not None:
        kwargs["autoStart"] = autoStart
    if retention is not None:
        kwargs["retention"] = retention
    if theme is not None:
        kwargs["theme"] = theme
    if onboardingComplete is not None:
        kwargs["onboardingComplete"] = onboardingComplete
    if microphone is not None:
        kwargs["microphone"] = microphone

    # Check if onboarding was already complete before this update
    old_settings = controller.get_settings()
    was_onboarding_complete = old_settings.get("onboardingComplete", False)

    result = controller.update_settings(**kwargs)

    # If onboarding JUST NOW completed (was false, now true), trigger the callback
    if onboardingComplete is True and not was_onboarding_complete and _on_onboarding_complete:
        debug("Onboarding just completed - triggering popup initialization")
        _on_onboarding_complete()

    return result


@server.method()
async def get_options():
    controller = get_controller()
    return controller.get_options()


@server.method()
async def get_history(limit: int = 100, offset: int = 0, search: str = None):
    controller = get_controller()
    return controller.get_history(limit, offset, search)


@server.method()
async def get_stats():
    controller = get_controller()
    stats = controller.get_stats()
    debug(f"get_stats returning: {stats}")
    return stats


@server.method()
async def delete_history(history_id: int):
    controller = get_controller()
    controller.delete_history(history_id)
    return {"success": True}


@server.method()
async def copy_to_clipboard(text: str):
    controller = get_controller()
    controller.clipboard_service.copy_to_clipboard(text)
    return {"success": True}


@server.method()
async def stop_recording():
    """Manually stop recording from the popup stop button."""
    controller = get_controller()
    controller.stop_recording()
    return {"success": True}


@server.method()
async def start_test_recording():
    """Start recording for onboarding test (no hotkey needed)."""
    controller = get_controller()
    controller.start_test_recording()
    return {"success": True}


@server.method()
async def stop_test_recording():
    """Stop test recording, transcribe, and return result (no paste/history)."""
    controller = get_controller()
    result = controller.stop_test_recording()
    return result


@server.method()
async def open_data_folder():
    """Open the application data folder."""
    controller = get_controller()
    controller.open_data_folder()
    return {"success": True}


@server.method()
async def set_popup_enabled(enabled: bool):
    """Enable or disable the popup (used during onboarding)."""
    controller = get_controller()
    controller.set_popup_enabled(enabled)
    return {"success": True}


@server.method()
async def reset_all_data():
    """Reset all user data and return to onboarding state."""
    controller = get_controller()
    controller.reset_all_data()
    # Trigger callback to hide popup and show main window
    if _on_data_reset:
        _on_data_reset()
    return {"success": True}
