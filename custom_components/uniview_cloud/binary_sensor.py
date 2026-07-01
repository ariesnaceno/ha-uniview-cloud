"""Binary sensors for Uniview Cloud."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import UniviewCloudEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Uniview Cloud binary sensors."""
    async_add_entities(
        UniviewCloudOnlineSensor(entry, device_id)
        for device_id in entry.runtime_data.coordinator.data
    )


class UniviewCloudOnlineSensor(UniviewCloudEntity, BinarySensorEntity):
    """Device online status."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_name = "Online"

    def __init__(self, entry: ConfigEntry, device_id: str) -> None:
        super().__init__(entry, device_id)
        self._attr_unique_id = f"{self._attr_unique_id}_online"

    @property
    def is_on(self) -> bool:
        """Return whether the device is online."""
        return self.uniview_device.online
