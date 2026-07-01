"""Entity helpers for Uniview Cloud."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .client import UniviewDevice
from .const import DOMAIN


class UniviewCloudEntity(CoordinatorEntity):
    """Base Uniview Cloud entity."""

    _attr_has_entity_name = True

    def __init__(self, entry, device_id: str) -> None:
        super().__init__(entry.runtime_data.coordinator)
        self._entry = entry
        self._device_id = device_id
        self._attr_unique_id = f"{entry.entry_id}_{device_id}"

    @property
    def uniview_device(self) -> UniviewDevice:
        """Return the coordinator device model."""
        return self.coordinator.data[self._device_id]

    @property
    def device_info(self) -> DeviceInfo:
        """Return device registry information."""
        device = self.uniview_device
        return DeviceInfo(
            identifiers={(DOMAIN, device.identifier)},
            manufacturer="Uniview",
            model=device.model,
            name=device.name,
            serial_number=device.serial_number,
        )
