"""Base entity for the Škoda Connect integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from myskoda.models.info import CapabilityId
from myskoda import Vehicle

from .const import DOMAIN, MANUFACTURER
from .coordinator import SkodaDataUpdateCoordinator


class SkodaVehicleEntity(CoordinatorEntity[SkodaDataUpdateCoordinator]):
    """Base class for all entities tied to a single Škoda vehicle."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SkodaDataUpdateCoordinator, vin: str) -> None:
        """Initialize the entity for a given vehicle VIN."""
        super().__init__(coordinator)
        self.vin = vin
        info = self.vehicle.info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, vin)},
            manufacturer=MANUFACTURER,
            name=info.name,
            model=info.get_model_name(),
            serial_number=vin,
            sw_version=info.software_version,
        )

    @property
    def vehicle(self) -> Vehicle:
        """Return the current vehicle data from the coordinator."""
        return self.coordinator.data.vehicles[self.vin]

    @property
    def available(self) -> bool:
        """Return True if the coordinator succeeded and this vehicle is present."""
        return super().available and self.vin in self.coordinator.data.vehicles

    def has_capability(self, capability: CapabilityId) -> bool:
        """Return whether the vehicle reports the given capability as available."""
        try:
            return self.vehicle.info.is_capability_available(capability)
        except Exception:  # noqa: BLE001 - defensive against upstream model changes
            return True
