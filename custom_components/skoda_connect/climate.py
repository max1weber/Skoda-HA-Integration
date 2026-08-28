"""Climate platform for the Škoda Connect integration (air conditioning)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from myskoda.models.air_conditioning import AirConditioningState
from myskoda import Vehicle

from .coordinator import SkodaConfigEntry, SkodaDataUpdateCoordinator
from .entity import SkodaVehicleEntity

_STATE_TO_HVAC_MODE = {
    AirConditioningState.OFF: HVACMode.OFF,
    AirConditioningState.ON: HVACMode.HEAT_COOL,
    AirConditioningState.COOLING: HVACMode.HEAT_COOL,
    AirConditioningState.HEATING: HVACMode.HEAT_COOL,
    AirConditioningState.HEATING_AUXILIARY: HVACMode.HEAT_COOL,
    AirConditioningState.VENTILATION: HVACMode.FAN_ONLY,
}

_STATE_TO_HVAC_ACTION = {
    AirConditioningState.OFF: HVACAction.OFF,
    AirConditioningState.ON: HVACAction.IDLE,
    AirConditioningState.COOLING: HVACAction.COOLING,
    AirConditioningState.HEATING: HVACAction.HEATING,
    AirConditioningState.HEATING_AUXILIARY: HVACAction.HEATING,
    AirConditioningState.VENTILATION: HVACAction.FAN,
}


def _has_air_conditioning(vehicle: Vehicle) -> bool:
    return vehicle.air_conditioning is not None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SkodaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Škoda Connect climate entity from a config entry."""
    coordinator = entry.runtime_data
    entities = [
        SkodaClimate(coordinator, vin)
        for vin, vehicle in coordinator.data.vehicles.items()
        if _has_air_conditioning(vehicle)
    ]
    async_add_entities(entities)


class SkodaClimate(SkodaVehicleEntity, ClimateEntity):
    """Represents the remote air conditioning of a Škoda vehicle."""

    _attr_translation_key = "air_conditioning"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT_COOL, HVACMode.FAN_ONLY]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.TURN_OFF | ClimateEntityFeature.TURN_ON
    )
    _attr_min_temp = 16
    _attr_max_temp = 29.5
    _attr_target_temperature_step = 0.5

    def __init__(self, coordinator: SkodaDataUpdateCoordinator, vin: str) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator, vin)
        self._attr_unique_id = f"{vin}_air_conditioning"

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current HVAC mode."""
        try:
            return _STATE_TO_HVAC_MODE.get(
                self.vehicle.air_conditioning.state, HVACMode.OFF
            )
        except AttributeError:
            return HVACMode.OFF

    @property
    def hvac_action(self) -> HVACAction | None:
        """Return the current HVAC action."""
        try:
            return _STATE_TO_HVAC_ACTION.get(self.vehicle.air_conditioning.state)
        except AttributeError:
            return None

    @property
    def target_temperature(self) -> float | None:
        """Return the target cabin temperature."""
        try:
            return self.vehicle.air_conditioning.target_temperature.temperature_value
        except AttributeError:
            return None

    def _ensure_writable(self) -> None:
        if self.coordinator.read_only:
            raise HomeAssistantError(
                "Škoda Connect is configured in read-only mode; enable it in the "
                "integration options to control the climate system"
            )

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set a new target temperature."""
        self._ensure_writable()
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        await self.coordinator.myskoda.set_target_temperature(self.vin, temperature)
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Turn the air conditioning on, off, or into ventilation mode."""
        self._ensure_writable()
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.myskoda.stop_air_conditioning(self.vin)
        elif hvac_mode == HVACMode.FAN_ONLY:
            await self.coordinator.myskoda.start_ventilation(self.vin)
        else:
            temperature = self.target_temperature or 21
            await self.coordinator.myskoda.start_air_conditioning(self.vin, temperature)
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self) -> None:
        """Turn the air conditioning on."""
        await self.async_set_hvac_mode(HVACMode.HEAT_COOL)

    async def async_turn_off(self) -> None:
        """Turn the air conditioning off."""
        await self.async_set_hvac_mode(HVACMode.OFF)
