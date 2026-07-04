"""Camera platform for Uniview Cloud."""

from __future__ import annotations

from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import UniviewCloudEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Uniview Cloud cameras."""
    async_add_entities(
        UniviewCloudCamera(entry, device_id)
        for device_id, device in entry.runtime_data.coordinator.data.items()
        if device.stream_url or device.snapshot_url
    )


class UniviewCloudCamera(UniviewCloudEntity, Camera):
    """Representation of a Uniview Cloud camera."""

    _attr_name = None

    @property
    def available(self) -> bool:
        """Return whether the camera has a playable stream or preview image."""
        device = self.uniview_device
        return super().available and bool(device.stream_url or device.snapshot_url)

    @property
    def supported_features(self) -> CameraEntityFeature:
        """Return supported camera features."""
        if self.uniview_device.stream_url:
            return CameraEntityFeature.STREAM
        return CameraEntityFeature(0)

    async def stream_source(self) -> str | None:
        """Return the stream source."""
        return await self._entry.runtime_data.client.async_get_stream_url(
            self.uniview_device
        )

    async def async_camera_image(
        self,
        width: int | None = None,
        height: int | None = None,
    ) -> bytes | None:
        """Return a still image response from the device if available."""
        snapshot_url = await self._entry.runtime_data.client.async_get_snapshot_url(
            self.uniview_device
        )
        if not snapshot_url:
            return None

        return await self._entry.runtime_data.client.async_get_bytes(snapshot_url)
