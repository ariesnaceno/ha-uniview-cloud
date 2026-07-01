"""Uniview Cloud integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import UniviewCloudAuthError, UniviewCloudClient, UniviewCloudError
from .const import (
    CONF_API_BASE_URL,
    CONF_REGION,
    DEFAULT_API_BASE_URL,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DOMAIN,
    PLATFORMS,
)

_LOGGER = logging.getLogger(__name__)


class UniviewCloudData:
    """Runtime data for a Uniview Cloud config entry."""

    def __init__(
        self,
        client: UniviewCloudClient,
        coordinator: DataUpdateCoordinator[dict],
    ) -> None:
        self.client = client
        self.coordinator = coordinator


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old Uniview Cloud config entries."""
    if entry.data.get(CONF_API_BASE_URL) == "https://ezcloud.uniview.com":
        data = dict(entry.data)
        data[CONF_API_BASE_URL] = DEFAULT_API_BASE_URL
        hass.config_entries.async_update_entry(entry, data=data)
        _LOGGER.info(
            "Migrated Uniview Cloud API host from EZCloud China to UniEase overseas"
        )
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up Uniview Cloud from a config entry."""
    session = async_get_clientsession(hass)
    client = UniviewCloudClient(
        session=session,
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        region=entry.data.get(CONF_REGION),
        api_base_url=entry.data.get(CONF_API_BASE_URL),
    )

    try:
        await client.async_login()
    except UniviewCloudAuthError as err:
        raise ConfigEntryAuthFailed(str(err)) from err
    except UniviewCloudError as err:
        raise UpdateFailed(str(err)) from err

    async def async_update_data() -> dict:
        try:
            return await client.async_get_devices()
        except UniviewCloudAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except UniviewCloudError as err:
            raise UpdateFailed(str(err)) from err

    coordinator: DataUpdateCoordinator[dict] = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL_SECONDS),
    )
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = UniviewCloudData(client, coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
