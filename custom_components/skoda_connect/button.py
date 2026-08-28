"""Button platform for the Škoda Connect integration."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from myskoda import MySkoda
from myskoda import Vehicle

from .coordinator import SkodaConfigEntry, SkodaDataUpdateCoordinator
from .entity import SkodaVehicleEntity


@dataclass(frozen=True, kw_only=True)
class SkodaButtonEntityDescription(ButtonEntityDescription):
    """Describes a Škoda Connect button entity."""

    press_fn: Callable[[MySkoda, str], Coroutine[Any, Any, Any]]
    exists_fn: Callable[[Vehicle], bool] = lambda vehicle: True


BUTTON_DESCRIPTIONS: tuple[SkodaButtonEntityDescription, ...] = (
    SkodaButtonEntityDescription(
        key="honk_and_flash",
        translation_key="honk_and_flash",
        press_fn=lambda api, vin: api.honk_flash(vin),
    ),
    SkodaButtonEntityDescription(
        key="flash",
        translation_key="flash",
        press_fn=lambda api, vin: api.flash(vin),
    ),
    SkodaButtonEntityDescription(
        key="wakeup",
        translation_key="wakeup",
        press_fn=lambda api, vin: api.wakeup(vin),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SkodaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Škoda Connect buttons from a config entry."""
    coordinator = entry.runtime_data
    entities: list[SkodaButton] = []
    for vin, vehicle in coordinator.data.vehicles.items():
        for description in BUTTON_DESCRIPTIONS:
            if description.exists_fn(vehicle):
                entities.append(SkodaButton(coordinator, vin, description))
    async_add_entities(entities)


class SkodaButton(SkodaVehicleEntity, ButtonEntity):
    """Represents a one-shot remote action of a Škoda vehicle."""

    entity_description: SkodaButtonEntityDescription

    def __init__(
        self,
        coordinator: SkodaDataUpdateCoordinator,
        vin: str,
        description: SkodaButtonEntityDescription,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, vin)
        self.entity_description = description
        self._attr_unique_id = f"{vin}_{description.key}"

    async def async_press(self) -> None:
        """Trigger the remote action."""
        if self.coordinator.read_only:
            raise HomeAssistantError(
                "Škoda Connect is configured in read-only mode; enable it in the "
                "integration options to use this control"
            )
        await self.entity_description.press_fn(self.coordinator.myskoda, self.vin)
