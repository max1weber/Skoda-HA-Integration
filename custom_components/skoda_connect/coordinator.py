"""Data update coordinator for the Škoda Connect integration."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime

from aiohttp import ClientResponseError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from myskoda import AuthorizationFailedError, MySkoda, Vehicle

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# The public MySkoda API enforces a strict per-account request quota and responds
# with HTTP 429 (and, in the wild, the non-standard 430) once it is exceeded. The
# myskoda client itself does not retry or back off on this, so the coordinator has
# to do so explicitly to avoid hammering the API and risking an account lockout.
RATE_LIMIT_STATUS_CODES = (429, 430)
MIN_RATE_LIMIT_BACKOFF = timedelta(minutes=15)
MAX_RATE_LIMIT_BACKOFF = timedelta(hours=1)


@dataclass
class SkodaData:
    """Container for all vehicles known to the account."""

    vehicles: dict[str, Vehicle] = field(default_factory=dict)


def _parse_retry_after(value: str | None) -> timedelta | None:
    """Parse a Retry-After header into a timedelta.

    The header may either be a number of seconds, or an HTTP-date. Returns None if
    the value is missing or cannot be parsed.
    """
    if not value:
        return None
    value = value.strip()
    try:
        return timedelta(seconds=int(value))
    except ValueError:
        pass
    try:
        retry_at = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if retry_at.tzinfo is None:
        retry_at = retry_at.replace(tzinfo=UTC)
    return retry_at - datetime.now(UTC)


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
        except ClientResponseError as err:
            if err.status in RATE_LIMIT_STATUS_CODES:
                backoff = self._rate_limit_backoff(err)
                _LOGGER.warning(
                    "Škoda Connect API rate limit hit (HTTP %s); pausing polling "
                    "for %s before trying again",
                    err.status,
                    backoff,
                )
                raise UpdateFailed(
                    "Škoda Connect API rate limit reached; backing off",
                    retry_after=backoff.total_seconds(),
                ) from err
            raise UpdateFailed(f"Error communicating with Škoda Connect API: {err}") from err
        except Exception as err:  # noqa: BLE001 - the underlying client raises plain Exceptions
            raise UpdateFailed(f"Error communicating with Škoda Connect API: {err}") from err

        return SkodaData(vehicles={vehicle.info.vin: vehicle for vehicle in vehicles})

    @staticmethod
    def _rate_limit_backoff(err: ClientResponseError) -> timedelta:
        """Compute how long to pause polling for after being rate limited."""
        retry_after = _parse_retry_after(err.headers.get("Retry-After") if err.headers else None)
        backoff = retry_after if retry_after is not None else MIN_RATE_LIMIT_BACKOFF
        backoff = max(backoff, MIN_RATE_LIMIT_BACKOFF)
        return min(backoff, MAX_RATE_LIMIT_BACKOFF)


# Generic alias used to type-annotate config entries for this integration.
SkodaConfigEntry = ConfigEntry[SkodaDataUpdateCoordinator]
