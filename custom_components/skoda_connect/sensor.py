"""Sensor platform for the Škoda Connect integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfLength,
    UnitOfPower,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from myskoda import Vehicle

from .coordinator import SkodaConfigEntry, SkodaDataUpdateCoordinator
from .entity import SkodaVehicleEntity


@dataclass(frozen=True, kw_only=True)
class SkodaSensorEntityDescription(SensorEntityDescription):
    """Describes a Škoda Connect sensor entity."""

    value_fn: Callable[[Vehicle], StateType]
    exists_fn: Callable[[Vehicle], bool] = lambda vehicle: True


def _charging_battery_percent(vehicle: Vehicle) -> StateType:
    return vehicle.charging.status.battery.state_of_charge_in_percent


def _charge_power(vehicle: Vehicle) -> StateType:
    return vehicle.charging.status.charge_power_in_kw


def _charging_rate(vehicle: Vehicle) -> StateType:
    return vehicle.charging.status.charging_rate_in_kilometers_per_hour


def _remaining_charge_time(vehicle: Vehicle) -> StateType:
    return vehicle.charging.status.remaining_time_to_fully_charged_in_minutes


def _battery_range_km(vehicle: Vehicle) -> StateType:
    meters = vehicle.charging.status.battery.remaining_cruising_range_in_meters
    return None if meters is None else round(meters / 1000)


def _total_range_km(vehicle: Vehicle) -> StateType:
    return vehicle.driving_range.total_range_in_km


def _fuel_level(vehicle: Vehicle) -> StateType:
    return vehicle.driving_range.primary_engine_range.current_fuel_level_in_percent


def _ad_blue_range(vehicle: Vehicle) -> StateType:
    return vehicle.driving_range.ad_blue_range


def _mileage(vehicle: Vehicle) -> StateType:
    return vehicle.health.mileage_in_km


def _outside_temperature(vehicle: Vehicle) -> StateType:
    return vehicle.air_conditioning.outside_temperature.temperature_value


def _target_temperature(vehicle: Vehicle) -> StateType:
    return vehicle.air_conditioning.target_temperature.temperature_value


def _software_version(vehicle: Vehicle) -> StateType:
    return vehicle.info.software_version


SENSOR_DESCRIPTIONS: tuple[SkodaSensorEntityDescription, ...] = (
    SkodaSensorEntityDescription(
        key="battery_level",
        translation_key="battery_level",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=_charging_battery_percent,
        exists_fn=lambda v: v.charging is not None and v.charging.status is not None,
    ),
    SkodaSensorEntityDescription(
        key="charge_power",
        translation_key="charge_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        value_fn=_charge_power,
        exists_fn=lambda v: v.charging is not None and v.charging.status is not None,
    ),
    SkodaSensorEntityDescription(
        key="charging_rate",
        translation_key="charging_rate",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        value_fn=_charging_rate,
        exists_fn=lambda v: v.charging is not None and v.charging.status is not None,
    ),
    SkodaSensorEntityDescription(
        key="remaining_charging_time",
        translation_key="remaining_charging_time",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement="min",
        value_fn=_remaining_charge_time,
        exists_fn=lambda v: v.charging is not None and v.charging.status is not None,
    ),
    SkodaSensorEntityDescription(
        key="battery_range",
        translation_key="battery_range",
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        value_fn=_battery_range_km,
        exists_fn=lambda v: v.charging is not None and v.charging.status is not None,
    ),
    SkodaSensorEntityDescription(
        key="total_range",
        translation_key="total_range",
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        value_fn=_total_range_km,
        exists_fn=lambda v: v.driving_range is not None,
    ),
    SkodaSensorEntityDescription(
        key="fuel_level",
        translation_key="fuel_level",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=_fuel_level,
        exists_fn=lambda v: v.driving_range is not None
        and v.driving_range.primary_engine_range.current_fuel_level_in_percent is not None,
    ),
    SkodaSensorEntityDescription(
        key="ad_blue_range",
        translation_key="ad_blue_range",
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        value_fn=_ad_blue_range,
        exists_fn=lambda v: v.driving_range is not None
        and v.driving_range.ad_blue_range is not None,
    ),
    SkodaSensorEntityDescription(
        key="mileage",
        translation_key="mileage",
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        value_fn=_mileage,
        exists_fn=lambda v: v.health is not None,
    ),
    SkodaSensorEntityDescription(
        key="outside_temperature",
        translation_key="outside_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=_outside_temperature,
        exists_fn=lambda v: v.air_conditioning is not None
        and v.air_conditioning.outside_temperature is not None,
    ),
    SkodaSensorEntityDescription(
        key="target_temperature",
        translation_key="target_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_registry_enabled_default=False,
        value_fn=_target_temperature,
        exists_fn=lambda v: v.air_conditioning is not None
        and v.air_conditioning.target_temperature is not None,
    ),
    SkodaSensorEntityDescription(
        key="software_version",
        translation_key="software_version",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=_software_version,
        exists_fn=lambda v: v.info.software_version is not None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SkodaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Škoda Connect sensors from a config entry."""
    coordinator = entry.runtime_data
    entities: list[SkodaSensor] = []
    for vin, vehicle in coordinator.data.vehicles.items():
        for description in SENSOR_DESCRIPTIONS:
            if description.exists_fn(vehicle):
                entities.append(SkodaSensor(coordinator, vin, description))
    async_add_entities(entities)


class SkodaSensor(SkodaVehicleEntity, SensorEntity):
    """Represents a single data point of a Škoda vehicle."""

    entity_description: SkodaSensorEntityDescription

    def __init__(
        self,
        coordinator: SkodaDataUpdateCoordinator,
        vin: str,
        description: SkodaSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, vin)
        self.entity_description = description
        self._attr_unique_id = f"{vin}_{description.key}"

    @property
    def native_value(self) -> StateType:
        """Return the current value, tolerating missing upstream data."""
        try:
            return self.entity_description.value_fn(self.vehicle)
        except (AttributeError, KeyError, TypeError):
            return None
