"""The Škoda Connect integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from myskoda import AuthorizationFailedError, MySkoda

from .const import CONF_READ_ONLY, DEFAULT_SCAN_INTERVAL_MINUTES
from .coordinator import SkodaConfigEntry, SkodaDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.CLIMATE,
    Platform.DEVICE_TRACKER,
    Platform.LOCK,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: SkodaConfigEntry) -> bool:
    """Set up Škoda Connect from a config entry."""
    session = async_get_clientsession(hass)
    # MQTT push events are not used by this integration; data is refreshed by polling.
    myskoda = MySkoda(session, mqtt_enabled=False)

    try:
        await myskoda.connect(entry.data[CONF_EMAIL], entry.data[CONF_PASSWORD])
        vins = await myskoda.list_vehicle_vins()
    except AuthorizationFailedError as err:
        raise ConfigEntryAuthFailed("Škoda Connect login failed") from err
    except Exception as err:  # noqa: BLE001 - underlying client raises plain Exceptions
        raise ConfigEntryNotReady(f"Unable to reach Škoda Connect: {err}") from err

    if not vins:
        raise ConfigEntryNotReady("No vehicles found on this Škoda Connect account")

    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES)
    coordinator = SkodaDataUpdateCoordinator(
        hass,
        entry,
        myskoda,
        vins,
        update_interval=timedelta(minutes=scan_interval),
    )
    coordinator.read_only = entry.options.get(CONF_READ_ONLY, False)

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: SkodaConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.myskoda.disconnect()
    return unloaded


async def _async_update_listener(hass: HomeAssistant, entry: SkodaConfigEntry) -> None:
    """Reload the entry when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)
