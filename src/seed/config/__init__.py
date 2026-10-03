"""Configuração por alvo (settings, alvos e, nas próximas fases, perfis de volume)."""

from seed.config.settings import (
    ConfigError,
    Settings,
    Target,
    get_settings,
    load_settings,
    mask_host,
    resolve_target,
)

__all__ = [
    "ConfigError",
    "Settings",
    "Target",
    "get_settings",
    "load_settings",
    "mask_host",
    "resolve_target",
]
