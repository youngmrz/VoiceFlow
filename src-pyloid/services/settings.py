from dataclasses import dataclass
from typing import Literal, Optional
from .database import DatabaseService


# Whisper model options
WHISPER_MODELS = ["tiny", "base", "small", "medium", "large-v3", "turbo"]

# Supported languages (subset - full list at https://github.com/openai/whisper)
WHISPER_LANGUAGES = [
    "auto",  # Auto-detect
    "en", "es", "fr", "de", "it", "pt", "nl", "pl", "ru",
    "zh", "ja", "ko", "ar", "hi", "tr", "vi", "th", "id"
]

# History retention options (in days, -1 = forever)
RETENTION_OPTIONS = {
    "7 days": 7,
    "30 days": 30,
    "90 days": 90,
    "Forever": -1,
}

# Theme options
THEME_OPTIONS = ["system", "light", "dark"]


@dataclass
class Settings:
    language: str = "auto"
    model: str = "tiny"
    auto_start: bool = True
    retention: int = -1  # days, -1 = forever
    theme: str = "system"
    onboarding_complete: bool = False
    microphone: int = -1  # -1 = default device, otherwise device id
    save_audio_to_history: bool = False


class SettingsService:
    def __init__(self, db: DatabaseService):
        self.db = db
        self._cache: Optional[Settings] = None

    def get_settings(self) -> Settings:
        if self._cache:
            return self._cache

        settings = Settings(
            language=self.db.get_setting("language", "auto"),
            model=self.db.get_setting("model", "tiny"),
            auto_start=self.db.get_setting("auto_start", "true") == "true",
            retention=int(self.db.get_setting("retention", "-1")),
            theme=self.db.get_setting("theme", "system"),
            onboarding_complete=self.db.get_setting("onboarding_complete", "false") == "true",
            microphone=int(self.db.get_setting("microphone", "-1")),
            save_audio_to_history=self.db.get_setting("save_audio_to_history", "false") == "true",
        )
        self._cache = settings
        return settings

    def update_settings(
        self,
        *,
        language: Optional[str] = None,
        model: Optional[str] = None,
        auto_start: Optional[bool] = None,
        retention: Optional[int] = None,
        theme: Optional[str] = None,
        onboarding_complete: Optional[bool] = None,
        microphone: Optional[int] = None,
        save_audio_to_history: Optional[bool] = None,
    ) -> Settings:
        if language is not None:
            self.db.set_setting("language", language)
        if model is not None:
            self.db.set_setting("model", model)
        if auto_start is not None:
            self.db.set_setting("auto_start", "true" if auto_start else "false")
        if retention is not None:
            self.db.set_setting("retention", str(retention))
        if theme is not None:
            self.db.set_setting("theme", theme)
        if onboarding_complete is not None:
            self.db.set_setting("onboarding_complete", "true" if onboarding_complete else "false")
        if microphone is not None:
            self.db.set_setting("microphone", str(microphone))
        if save_audio_to_history is not None:
            self.db.set_setting("save_audio_to_history", "true" if save_audio_to_history else "false")

        self._cache = None  # Invalidate cache
        return self.get_settings()

    def get_available_models(self) -> list:
        return WHISPER_MODELS

    def get_available_languages(self) -> list:
        return WHISPER_LANGUAGES

    def get_retention_options(self) -> dict:
        return RETENTION_OPTIONS

    def get_theme_options(self) -> list:
        return THEME_OPTIONS
