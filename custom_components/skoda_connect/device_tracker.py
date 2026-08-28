"""Device tracker platform for the Škoda Connect integration."""

from __future__ import annotations

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from myskoda.models.position import PositionType
from myskoda import Vehicle

from .coordinator import SkodaConfigEntry, SkodaDataUpdateCoordinator
from .entity import SkodaVehicleEntity


def _has_position(vehicle: Vehicle) -> bool:
    return vehicle.positions is not None and bool(vehicle.positions.positions)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SkodaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Škoda Connect device tracker from a config entry."""
    coordinator = entry.runtime_data
    entities = [
        SkodaDeviceTracker(coordinator, vin)
        for vin, vehicle in coordinator.data.vehicles.items()
        if _has_position(vehicle)
    ]
    async_add_entities(entities)


class SkodaDeviceTracker(SkodaVehicleEntity, TrackerEntity):
    """Represents the last known GPS position of a Škoda vehicle."""

    _attr_translation_key = "vehicle_location"

    def __init__(self, coordinator: SkodaDataUpdateCoordinator, vin: str) -> None:
        """Initialize the device tracker."""
        super().__init__(coordinator, vin)
        self._attr_unique_id = f"{vin}_location"

    @property
    def source_type(self) -> SourceType:
        """Return the source type of the device tracker."""
        return SourceType.GPS

    def _vehicle_coordinates(self):
        try:
            for position in self.vehicle.positions.positions:
                if position.type == PositionType.VEHICLE:
                    return position.gps_coordinates
        except (AttributeError, TypeError):
            pass
        return None

    @property
    def latitude(self) -> float | None:
        """Return the latitude of the vehicle."""
        coordinates = self._vehicle_coordinates()
        return coordinates.latitude if coordinates else None

    @property
    def longitude(self) -> float | None:
        """Return the longitude of the vehicle."""
        coordinates = self._vehicle_coordinates()
        return coordinates.longitude if coordinates else None

    @property
    def icon(self) -> str:
        """Return the icon for the tracker."""
        return "mdi:car"
