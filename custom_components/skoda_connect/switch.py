"""Switch platform for the Škoda Connect integration."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from myskoda import MySkoda
from myskoda.models.charging import ChargingState, MaxChargeCurrent
from myskoda.models.common import ActiveState
from myskoda import Vehicle

from .coordinator import SkodaConfigEntry, SkodaDataUpdateCoordinator
from .entity import SkodaVehicleEntity


@dataclass(frozen=True, kw_only=True)
class SkodaSwitchEntityDescription(SwitchEntityDescription):
    """Describes a Škoda Connect switch entity."""

    is_on_fn: Callable[[Vehicle], bool | None]
    turn_on_fn: Callable[[MySkoda, str], Coroutine[Any, Any, Any]]
    turn_off_fn: Callable[[MySkoda, str], Coroutine[Any, Any, Any]]
    exists_fn: Callable[[Vehicle], bool] = lambda vehicle: True


SWITCH_DESCRIPTIONS: tuple[SkodaSwitchEntityDescription, ...] = (
    SkodaSwitchEntityDescription(
        key="window_heating",
        translation_key="window_heating",
        is_on_fn=lambda v: v.air_conditioning.window_heating_enabled,
        turn_on_fn=lambda api, vin: api.start_window_heating(vin),
        turn_off_fn=lambda api, vin: api.stop_window_heating(vin),
        exists_fn=lambda v: v.air_conditioning is not None,
    ),
    SkodaSwitchEntityDescription(
        key="charging",
        translation_key="charging",
        is_on_fn=lambda v: v.charging.status.state == ChargingState.CHARGING,
        turn_on_fn=lambda api, vin: api.start_charging(vin),
        turn_off_fn=lambda api, vin: api.stop_charging(vin),
        exists_fn=lambda v: v.charging is not None and v.charging.status is not None,
    ),
    SkodaSwitchEntityDescription(
        key="battery_care_mode",
        translation_key="battery_care_mode",
        entity_category=EntityCategory.CONFIG,
        is_on_fn=lambda v: v.charging.settings.charging_care_mode
        == ActiveState.ACTIVATED,
        turn_on_fn=lambda api, vin: api.set_battery_care_mode(vin, True),
        turn_off_fn=lambda api, vin: api.set_battery_care_mode(vin, False),
        exists_fn=lambda v: v.charging is not None
        and v.charging.settings is not None
        and v.charging.settings.charging_care_mode is not None,
    ),
    SkodaSwitchEntityDescription(
        key="reduced_charging_current",
        translation_key="reduced_charging_current",
        entity_category=EntityCategory.CONFIG,
        is_on_fn=lambda v: v.charging.settings.max_charge_current_ac
        == MaxChargeCurrent.REDUCED,
        turn_on_fn=lambda api, vin: api.set_reduced_current_limit(vin, True),
        turn_off_fn=lambda api, vin: api.set_reduced_current_limit(vin, False),
        exists_fn=lambda v: v.charging is not None
        and v.charging.settings is not None
        and v.charging.settings.max_charge_current_ac is not None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SkodaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Škoda Connect switches from a config entry."""
    coordinator = entry.runtime_data
    entities: list[SkodaSwitch] = []
    for vin, vehicle in coordinator.data.vehicles.items():
        for description in SWITCH_DESCRIPTIONS:
            if description.exists_fn(vehicle):
                entities.append(SkodaSwitch(coordinator, vin, description))
    async_add_entities(entities)


class SkodaSwitch(SkodaVehicleEntity, SwitchEntity):
    """Represents a togglable remote function of a Škoda vehicle."""

    entity_description: SkodaSwitchEntityDescription

    def __init__(
        self,
        coordinator: SkodaDataUpdateCoordinator,
        vin: str,
        description: SkodaSwitchEntityDescription,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, vin)
        self.entity_description = description
        self._attr_unique_id = f"{vin}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        """Return true if the function is currently active."""
        try:
            return self.entity_description.is_on_fn(self.vehicle)
        except (AttributeError, KeyError, TypeError):
            return None

    def _ensure_writable(self) -> None:
        if self.coordinator.read_only:
            raise HomeAssistantError(
                "Škoda Connect is configured in read-only mode; enable it in the "
                "integration options to use this control"
            )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the function on."""
        self._ensure_writable()
        await self.entity_description.turn_on_fn(self.coordinator.myskoda, self.vin)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the function off."""
        self._ensure_writable()
        await self.entity_description.turn_off_fn(self.coordinator.myskoda, self.vin)
        await self.coordinator.async_request_refresh()
