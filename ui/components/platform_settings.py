"""Global platform settings for the Streamlit shell."""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

PLATFORM_SETTING_PRESETS: dict[str, dict[str, object]] = {
    "default": {
        "shell_mode": "enterprise",
        "visual_theme": "bright_lab",
        "font_size": "medium",
        "content_density": "comfortable",
        "content_width": "standard",
        "show_hero_sections": True,
        "show_platform_footer": True,
    },
    "presentation": {
        "shell_mode": "enterprise",
        "visual_theme": "bright_lab",
        "font_size": "large",
        "content_density": "comfortable",
        "content_width": "wide",
        "show_hero_sections": True,
        "show_platform_footer": True,
    },
    "compact_lab": {
        "shell_mode": "standard",
        "visual_theme": "bright_lab",
        "font_size": "small",
        "content_density": "compact",
        "content_width": "wide",
        "show_hero_sections": False,
        "show_platform_footer": True,
    },
    "accessibility_large_text": {
        "shell_mode": "enterprise",
        "visual_theme": "bright_lab",
        "font_size": "large",
        "content_density": "comfortable",
        "content_width": "full",
        "show_hero_sections": True,
        "show_platform_footer": True,
    },
}

DEFAULT_PLATFORM_SETTINGS: dict[str, object] = {
    "theme_preset": "default",
    **PLATFORM_SETTING_PRESETS["default"],
}

_SETTINGS_DIR = Path.home() / ".shieldlab-g4"
_SETTINGS_FILE = _SETTINGS_DIR / "platform_settings.json"
_MAX_SETTINGS_BYTES = 64 * 1024  # 64 KB guard — reject oversized/crafted settings files
_THEME_OPTIONS = {"bright_lab", "dark_glass", "classic_blue"}
_SHELL_MODE_OPTIONS = {"standard", "enterprise"}
_FONT_OPTIONS = {"small", "medium", "large"}
_DENSITY_OPTIONS = {"compact", "comfortable"}
_WIDTH_OPTIONS = {"standard", "wide", "full"}
_PRESET_OPTIONS = set(PLATFORM_SETTING_PRESETS) | {"custom"}


def _normalize_platform_settings(raw: dict[str, object] | None) -> dict[str, object]:
    settings = DEFAULT_PLATFORM_SETTINGS.copy()
    if raw:
        settings.update(raw)

    if str(settings.get("visual_theme")) not in _THEME_OPTIONS:
        settings["visual_theme"] = DEFAULT_PLATFORM_SETTINGS["visual_theme"]

    if str(settings.get("shell_mode")) not in _SHELL_MODE_OPTIONS:
        settings["shell_mode"] = DEFAULT_PLATFORM_SETTINGS["shell_mode"]

    if str(settings.get("font_size")) not in _FONT_OPTIONS:
        settings["font_size"] = DEFAULT_PLATFORM_SETTINGS["font_size"]
    if str(settings.get("content_density")) not in _DENSITY_OPTIONS:
        settings["content_density"] = DEFAULT_PLATFORM_SETTINGS["content_density"]
    if str(settings.get("content_width")) not in _WIDTH_OPTIONS:
        settings["content_width"] = DEFAULT_PLATFORM_SETTINGS["content_width"]

    settings["show_hero_sections"] = bool(settings.get("show_hero_sections", True))
    settings["show_platform_footer"] = bool(settings.get("show_platform_footer", True))

    preset = str(settings.get("theme_preset", "default"))
    settings["theme_preset"] = preset if preset in _PRESET_OPTIONS else "custom"
    settings["theme_preset"] = infer_platform_preset(settings)
    return settings


def _load_persisted_settings() -> dict[str, object]:
    if not _SETTINGS_FILE.exists():
        return {}
    try:
        if _SETTINGS_FILE.stat().st_size > _MAX_SETTINGS_BYTES:
            return {}
        data = json.loads(_SETTINGS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def _persist_platform_settings(settings: dict[str, object]) -> None:
    _SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    _SETTINGS_FILE.write_text(json.dumps(settings, indent=2), encoding="utf-8")


def infer_platform_preset(settings: dict[str, object]) -> str:
    comparable = {
        "shell_mode": str(settings.get("shell_mode")),
        "visual_theme": str(settings.get("visual_theme")),
        "font_size": str(settings.get("font_size")),
        "content_density": str(settings.get("content_density")),
        "content_width": str(settings.get("content_width")),
        "show_hero_sections": bool(settings.get("show_hero_sections")),
        "show_platform_footer": bool(settings.get("show_platform_footer")),
    }
    for preset_name, preset_settings in PLATFORM_SETTING_PRESETS.items():
        if comparable == preset_settings:
            return preset_name
    return "custom"


def init_platform_settings() -> dict[str, object]:
    """Ensure platform settings exist in session state and return them."""
    if "platform_settings" not in st.session_state:
        st.session_state.platform_settings = _normalize_platform_settings(_load_persisted_settings())
    else:
        st.session_state.platform_settings = _normalize_platform_settings(
            dict(st.session_state.platform_settings),
        )
    return st.session_state.platform_settings


def get_platform_settings() -> dict[str, object]:
    """Return the current platform settings."""
    return init_platform_settings()


def update_platform_settings(**kwargs: object) -> None:
    """Update platform settings in session state and persist them."""
    settings = init_platform_settings().copy()
    settings.update(kwargs)
    normalized = _normalize_platform_settings(settings)
    st.session_state.platform_settings = normalized
    _persist_platform_settings(normalized)


def apply_platform_preset(preset_name: str) -> None:
    """Apply a named platform preset and persist it."""
    if preset_name not in PLATFORM_SETTING_PRESETS:
        raise ValueError(f"Unknown platform preset: {preset_name}")
    update_platform_settings(theme_preset=preset_name, **PLATFORM_SETTING_PRESETS[preset_name])


def reset_platform_settings() -> None:
    """Restore the default platform settings and persist them."""
    st.session_state.platform_settings = DEFAULT_PLATFORM_SETTINGS.copy()
    _persist_platform_settings(DEFAULT_PLATFORM_SETTINGS)