"""Client for Uniview Cloud.

The public API details still need to be confirmed against a test account.
This module intentionally keeps all cloud assumptions isolated from Home
Assistant entity code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aiohttp import ClientError, ClientSession


class UniviewCloudError(Exception):
    """Base Uniview Cloud error."""


class UniviewCloudAuthError(UniviewCloudError):
    """Authentication failed."""


class UniviewCloudApiNotConfiguredError(UniviewCloudError):
    """The cloud API endpoint is not configured yet."""


@dataclass(slots=True)
class UniviewDevice:
    """A Uniview camera or NVR channel."""

    identifier: str
    name: str
    online: bool
    model: str | None = None
    serial_number: str | None = None
    stream_url: str | None = None
    snapshot_url: str | None = None
    raw: dict[str, Any] | None = None


class UniviewCloudClient:
    """Minimal async client for the Uniview cloud service."""

    def __init__(
        self,
        *,
        session: ClientSession,
        username: str,
        password: str,
        region: str | None = None,
        api_base_url: str | None = None,
    ) -> None:
        self._session = session
        self._username = username
        self._password = password
        self._region = region
        self._api_base_url = api_base_url.rstrip("/") if api_base_url else None
        self._access_token: str | None = None

    async def async_login(self) -> None:
        """Authenticate with Uniview Cloud."""
        if not self._api_base_url:
            raise UniviewCloudApiNotConfiguredError(
                "Uniview Cloud API base URL is not configured yet"
            )

        try:
            response = await self._session.post(
                f"{self._api_base_url}/login",
                json={
                    "username": self._username,
                    "password": self._password,
                    "region": self._region,
                },
            )
        except ClientError as err:
            raise UniviewCloudError(f"Unable to connect to Uniview Cloud: {err}") from err

        if response.status in (401, 403):
            raise UniviewCloudAuthError("Invalid Uniview Cloud credentials")
        if response.status >= 400:
            raise UniviewCloudError(
                f"Uniview Cloud login failed with HTTP {response.status}"
            )

        payload = await response.json(content_type=None)
        token = payload.get("access_token") or payload.get("token")
        if not token:
            raise UniviewCloudError("Uniview Cloud login response did not include a token")
        self._access_token = str(token)

    async def async_get_devices(self) -> dict[str, UniviewDevice]:
        """Return devices visible to the Uniview account."""
        if not self._api_base_url:
            raise UniviewCloudApiNotConfiguredError(
                "Uniview Cloud API base URL is not configured yet"
            )
        if not self._access_token:
            await self.async_login()

        try:
            response = await self._session.get(
                f"{self._api_base_url}/devices",
                headers={"Authorization": f"Bearer {self._access_token}"},
            )
        except ClientError as err:
            raise UniviewCloudError(f"Unable to fetch Uniview devices: {err}") from err

        if response.status == 401:
            self._access_token = None
            raise UniviewCloudAuthError("Uniview Cloud session expired")
        if response.status >= 400:
            raise UniviewCloudError(
                f"Uniview Cloud device fetch failed with HTTP {response.status}"
            )

        payload = await response.json(content_type=None)
        devices_payload = payload.get("devices", payload if isinstance(payload, list) else [])
        devices: dict[str, UniviewDevice] = {}
        for item in devices_payload:
            device = self._parse_device(item)
            devices[device.identifier] = device
        return devices

    async def async_get_bytes(self, url: str) -> bytes | None:
        """Fetch binary content."""
        try:
            response = await self._session.get(url)
        except ClientError:
            return None
        if response.status >= 400:
            return None
        return await response.read()

    def _parse_device(self, item: dict[str, Any]) -> UniviewDevice:
        identifier = str(
            item.get("id")
            or item.get("device_id")
            or item.get("serial")
            or item.get("sn")
            or item.get("channel_id")
        )
        return UniviewDevice(
            identifier=identifier,
            name=str(item.get("name") or item.get("device_name") or identifier),
            online=bool(item.get("online") or item.get("is_online")),
            model=item.get("model"),
            serial_number=item.get("serial") or item.get("sn"),
            stream_url=item.get("stream_url") or item.get("rtsp_url"),
            snapshot_url=item.get("snapshot_url"),
            raw=item,
        )
