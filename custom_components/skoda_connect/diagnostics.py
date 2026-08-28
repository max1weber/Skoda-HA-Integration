"""Diagnostics support for the Škoda Connect integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from .const import CONF_SPIN
from .coordinator import SkodaConfigEntry

TO_REDACT = {CONF_EMAIL, CONF_PASSWORD, CONF_SPIN, "vin", "gps_coordinates", "address"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: SkodaConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data

    vehicles: dict[str, Any] = {}
    for vin, vehicle in coordinator.data.vehicles.items():
        sections: dict[str, Any] = {}
        for field_name in vars(vehicle):
            section = getattr(vehicle, field_name, None)
            to_dict = getattr(section, "to_dict", None)
            if callable(to_dict):
                sections[field_name] = to_dict()
            elif section is not None:
                sections[field_name] = str(section)
        vehicles[vin] = sections

    return {
        "options": dict(entry.options),
        "read_only": coordinator.read_only,
        "vehicle_count": len(coordinator.vins),
        "vehicles": async_redact_data(vehicles, TO_REDACT),
    }
