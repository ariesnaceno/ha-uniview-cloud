"""Sensors for Uniview Cloud."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import UniviewCloudEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Uniview Cloud sensors."""
    async_add_entities(
        UniviewCloudModelSensor(entry, device_id)
        for device_id in entry.runtime_data.coordinator.data
    )


class UniviewCloudModelSensor(UniviewCloudEntity, SensorEntity):
    """Device model sensor."""

    _attr_name = "Model"

    def __init__(self, entry: ConfigEntry, device_id: str) -> None:
        super().__init__(entry, device_id)
        self._attr_unique_id = f"{self._attr_unique_id}_model"

    @property
    def native_value(self) -> str | None:
        """Return the device model."""
        return self.uniview_device.model
