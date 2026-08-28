"""Lock platform for the Škoda Connect integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.lock import LockEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from myskoda.models.common import DoorLockedState

from .const import CONF_SPIN
from .coordinator import SkodaConfigEntry, SkodaDataUpdateCoordinator
from .entity import SkodaVehicleEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SkodaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Škoda Connect locks from a config entry."""
    coordinator = entry.runtime_data
    entities = [
        SkodaLock(coordinator, vin, entry.data.get(CONF_SPIN))
        for vin, vehicle in coordinator.data.vehicles.items()
        if vehicle.status is not None and vehicle.status.overall is not None
    ]
    async_add_entities(entities)


class SkodaLock(SkodaVehicleEntity, LockEntity):
    """Represents the central locking system of a Škoda vehicle."""

    _attr_translation_key = "vehicle_lock"

    def __init__(
        self, coordinator: SkodaDataUpdateCoordinator, vin: str, spin: str | None
    ) -> None:
        """Initialize the lock entity."""
        super().__init__(coordinator, vin)
        self._spin = spin
        self._attr_unique_id = f"{vin}_lock"

    @property
    def is_locked(self) -> bool | None:
        """Return True if the vehicle is currently locked."""
        try:
            return self.vehicle.status.overall.locked == DoorLockedState.LOCKED
        except (AttributeError, TypeError):
            return None

    def _ensure_writable(self) -> None:
        if self.coordinator.read_only:
            raise HomeAssistantError(
                "Škoda Connect is configured in read-only mode; enable it in the "
                "integration options to lock or unlock the vehicle"
            )
        if not self._spin:
            raise HomeAssistantError(
                "An S-PIN is required to lock or unlock this vehicle. Set it when "
                "configuring the Škoda Connect integration"
            )

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the vehicle."""
        self._ensure_writable()
        await self.coordinator.myskoda.lock(self.vin, self._spin)
        await self.coordinator.async_request_refresh()

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the vehicle."""
        self._ensure_writable()
        await self.coordinator.myskoda.unlock(self.vin, self._spin)
        await self.coordinator.async_request_refresh()
