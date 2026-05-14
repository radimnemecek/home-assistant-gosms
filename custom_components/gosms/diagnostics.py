from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_CHANNEL, DATA_COORDINATOR, DOMAIN

TO_REDACT = {
    "client_id",
    "client_secret",
    "access_token",
    "token",
    "raw",
    "message",
    "recipient",
    "recipients",
    "phone",
    "phone_number",
}


def _integration_version() -> str | None:
    """Read integration version from manifest when available."""
    manifest_path = Path(__file__).with_name("manifest.json")
    try:
        with manifest_path.open(encoding="utf-8") as file_handle:
            manifest = json.load(file_handle)
    except (OSError, json.JSONDecodeError):
        return None

    version = manifest.get("version")
    return str(version) if version is not None else None


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    domain_data: dict[str, Any] = hass.data.get(DOMAIN, {})
    entry_runtime_data: dict[str, Any] = domain_data.get(entry.entry_id, {})

    coordinator_data: dict[str, Any] = {}
    coordinator = entry_runtime_data.get(DATA_COORDINATOR)
    runtime_coordinator_data = getattr(coordinator, "data", None)
    if isinstance(runtime_coordinator_data, dict):
        coordinator_data = {
            "balance": runtime_coordinator_data.get("balance"),
            "currency": runtime_coordinator_data.get("currency"),
            "invoicing_type": runtime_coordinator_data.get("invoicing_type"),
        }

    diagnostics: dict[str, Any] = {
        "domain": DOMAIN,
        "entry_title": entry.title,
        "entry_version": getattr(entry, "version", None),
        "entry_minor_version": getattr(entry, "minor_version", None),
        "integration_version": _integration_version(),
        "configured_channel": entry.data.get(CONF_CHANNEL),
        "options": dict(entry.options),
        "is_loaded": entry.entry_id in domain_data,
        "entry_state": str(getattr(entry, "state", "unknown")),
        "coordinator": coordinator_data,
    }

    return async_redact_data(diagnostics, TO_REDACT)
