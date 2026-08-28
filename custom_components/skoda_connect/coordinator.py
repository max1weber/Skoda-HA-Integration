"""Data update coordinator for the Škoda Connect integration."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from myskoda import AuthorizationFailedError, MySkoda, Vehicle

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass
class SkodaData:
    """Container for all vehicles known to the account."""

    vehicles: dict[str, Vehicle] = field(default_factory=dict)


class SkodaDataUpdateCoordinator(DataUpdateCoordinator[SkodaData]):
    """Coordinator that polls the MySkoda API for every vehicle on the account."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: SkodaConfigEntry,
        myskoda: MySkoda,
        vins: list[str],
        update_interval: timedelta,
    ) -> None:
        """Set up the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self.myskoda = myskoda
        self.vins = vins
        self.read_only = False

    async def _async_update_data(self) -> SkodaData:
        """Fetch the latest data for every vehicle from the cloud API."""
        try:
            vehicles = await asyncio.gather(
                *(self.myskoda.get_vehicle(vin) for vin in self.vins)
            )
        except AuthorizationFailedError as err:
            raise ConfigEntryAuthFailed("Authentication with Škoda Connect failed") from err
        except Exception as err:  # noqa: BLE001 - the underlying client raises plain Exceptions
            raise UpdateFailed(f"Error communicating with Škoda Connect API: {err}") from err

        return SkodaData(vehicles={vehicle.info.vin: vehicle for vehicle in vehicles})


# Generic alias used to type-annotate config entries for this integration.
SkodaConfigEntry = ConfigEntry[SkodaDataUpdateCoordinator]
