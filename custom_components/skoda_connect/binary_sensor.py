"""Binary sensor platform for the Škoda Connect integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from myskoda.models.charging import ChargingState
from myskoda.models.common import ConnectionState, OnOffState, OpenState
from myskoda import Vehicle

from .coordinator import SkodaConfigEntry, SkodaDataUpdateCoordinator
from .entity import SkodaVehicleEntity


@dataclass(frozen=True, kw_only=True)
class SkodaBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a Škoda Connect binary sensor entity."""

    value_fn: Callable[[Vehicle], bool | None]
    exists_fn: Callable[[Vehicle], bool] = lambda vehicle: True


BINARY_SENSOR_DESCRIPTIONS: tuple[SkodaBinarySensorEntityDescription, ...] = (
    SkodaBinarySensorEntityDescription(
        key="doors_open",
        translation_key="doors_open",
        device_class=BinarySensorDeviceClass.DOOR,
        value_fn=lambda v: v.status.overall.doors == OpenState.OPEN,
        exists_fn=lambda v: v.status is not None and v.status.overall is not None,
    ),
    SkodaBinarySensorEntityDescription(
        key="windows_open",
        translation_key="windows_open",
        device_class=BinarySensorDeviceClass.WINDOW,
        value_fn=lambda v: v.status.overall.windows == OpenState.OPEN,
        exists_fn=lambda v: v.status is not None and v.status.overall is not None,
    ),
    SkodaBinarySensorEntityDescription(
        key="trunk_open",
        translation_key="trunk_open",
        device_class=BinarySensorDeviceClass.OPENING,
        value_fn=lambda v: v.status.detail.trunk == OpenState.OPEN,
        exists_fn=lambda v: v.status is not None and v.status.detail is not None,
    ),
    SkodaBinarySensorEntityDescription(
        key="bonnet_open",
        translation_key="bonnet_open",
        device_class=BinarySensorDeviceClass.OPENING,
        value_fn=lambda v: v.status.detail.bonnet == OpenState.OPEN,
        exists_fn=lambda v: v.status is not None and v.status.detail is not None,
    ),
    SkodaBinarySensorEntityDescription(
        key="lights_on",
        translation_key="lights_on",
        device_class=BinarySensorDeviceClass.LIGHT,
        value_fn=lambda v: v.status.overall.lights == OnOffState.ON,
        exists_fn=lambda v: v.status is not None and v.status.overall is not None,
    ),
    SkodaBinarySensorEntityDescription(
        key="charging",
        translation_key="charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        value_fn=lambda v: v.charging.status.state == ChargingState.CHARGING,
        exists_fn=lambda v: v.charging is not None and v.charging.status is not None,
    ),
    SkodaBinarySensorEntityDescription(
        key="plugged_in",
        translation_key="plugged_in",
        device_class=BinarySensorDeviceClass.PLUG,
        value_fn=lambda v: v.air_conditioning.charger_connection_state
        == ConnectionState.CONNECTED,
        exists_fn=lambda v: v.air_conditioning is not None
        and v.air_conditioning.charger_connection_state is not None,
    ),
    SkodaBinarySensorEntityDescription(
        key="vehicle_in_saved_location",
        translation_key="vehicle_in_saved_location",
        icon="mdi:home-map-marker",
        value_fn=lambda v: v.charging.is_vehicle_in_saved_location,
        exists_fn=lambda v: v.charging is not None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SkodaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Škoda Connect binary sensors from a config entry."""
    coordinator = entry.runtime_data
    entities: list[SkodaBinarySensor] = []
    for vin, vehicle in coordinator.data.vehicles.items():
        for description in BINARY_SENSOR_DESCRIPTIONS:
            if description.exists_fn(vehicle):
                entities.append(SkodaBinarySensor(coordinator, vin, description))
    async_add_entities(entities)


class SkodaBinarySensor(SkodaVehicleEntity, BinarySensorEntity):
    """Represents a boolean state of a Škoda vehicle."""

    entity_description: SkodaBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: SkodaDataUpdateCoordinator,
        vin: str,
        description: SkodaBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, vin)
        self.entity_description = description
        self._attr_unique_id = f"{vin}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        """Return true if the condition described is active, tolerating missing data."""
        try:
            return self.entity_description.value_fn(self.vehicle)
        except (AttributeError, KeyError, TypeError):
            return None
