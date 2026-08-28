"""Number platform for the Škoda Connect integration."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import SkodaConfigEntry, SkodaDataUpdateCoordinator
from .entity import SkodaVehicleEntity


def _has_charge_limit(vehicle) -> bool:
    return (
        vehicle.charging is not None
        and vehicle.charging.settings is not None
        and vehicle.charging.settings.target_state_of_charge_in_percent is not None
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SkodaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Škoda Connect charge limit number entity from a config entry."""
    coordinator = entry.runtime_data
    entities = [
        SkodaChargeLimitNumber(coordinator, vin)
        for vin, vehicle in coordinator.data.vehicles.items()
        if _has_charge_limit(vehicle)
    ]
    async_add_entities(entities)


class SkodaChargeLimitNumber(SkodaVehicleEntity, NumberEntity):
    """Represents the target state-of-charge limit for AC charging."""

    _attr_translation_key = "charge_limit"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_native_min_value = 50
    _attr_native_max_value = 100
    _attr_native_step = 10
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: SkodaDataUpdateCoordinator, vin: str) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator, vin)
        self._attr_unique_id = f"{vin}_charge_limit"

    @property
    def native_value(self) -> float | None:
        """Return the currently configured charge limit."""
        try:
            return self.vehicle.charging.settings.target_state_of_charge_in_percent
        except AttributeError:
            return None

    async def async_set_native_value(self, value: float) -> None:
        """Set a new charge limit."""
        if self.coordinator.read_only:
            raise HomeAssistantError(
                "Škoda Connect is configured in read-only mode; enable it in the "
                "integration options to change the charge limit"
            )
        await self.coordinator.myskoda.set_charge_limit(self.vin, int(value))
        await self.coordinator.async_request_refresh()
