"""Client for Uniview EZCloud."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import platform
from typing import Any
import uuid

from aiohttp import ClientError, ClientSession

from .const import DEFAULT_API_BASE_URL

_DEVICE_LIST_PAYLOADS: tuple[dict[str, Any], ...] = (
    {"pageNo": 1, "pageSize": 200},
    {"pageNum": 1, "pageSize": 200},
    {"page": 1, "pageSize": 200},
    {},
)

_DEVICE_LIST_PATHS: tuple[str, ...] = (
    "/openapi/device/list",
    "/openapi/cdn/device/list",
)


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
    """Minimal async client for the Uniview EZCloud service."""

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
        self._api_base_url = (api_base_url or DEFAULT_API_BASE_URL).rstrip("/")
        self._access_token: str | None = None
        self._hard_id = uuid.uuid4().hex

    async def async_login(self) -> None:
        """Authenticate with Uniview EZCloud."""
        payload = await self._async_post(
            "/openapi/user/account/token/get",
            {
                "username": self._username,
                "password": self._hash_password(self._password),
                "clientId": "",
                "passwordVersion": 1,
                "clientName": "Home Assistant",
                "hardId": self._hard_id,
                "platform": platform.platform(),
            },
            require_auth=False,
        )

        token = (
            payload.get("accessToken")
            or payload.get("access_token")
            or payload.get("token")
        )
        if not token:
            raise UniviewCloudError("Uniview Cloud login response did not include a token")
        self._access_token = str(token)
        if server_address := payload.get("serverAddress"):
            self._api_base_url = self._normalize_api_base_url(str(server_address))

    async def async_get_devices(self) -> dict[str, UniviewDevice]:
        """Return devices visible to the Uniview account."""
        if not self._access_token:
            await self.async_login()

        payload = await self._async_post_device_list()
        devices_payload = self._extract_list(payload)
        devices: dict[str, UniviewDevice] = {}
        for item in devices_payload:
            device = self._parse_device(item)
            devices[device.identifier] = device
            if item.get("supportMultiChannel"):
                for channel in await self._async_get_channels(item):
                    channel_device = self._parse_channel(item, channel)
                    devices[channel_device.identifier] = channel_device
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

    async def _async_post(
        self,
        path: str,
        data: dict[str, Any],
        *,
        require_auth: bool = True,
    ) -> Any:
        """Send an EZCloud JSON POST and return the response data."""
        if not self._api_base_url:
            raise UniviewCloudApiNotConfiguredError(
                "Uniview Cloud API base URL is not configured yet"
            )

        headers = {
            "Accept": "application/json, text/plain, */*",
            "Origin": self._api_base_url,
            "Referer": f"{self._api_base_url}/userWeb/login",
        }
        if require_auth:
            if not self._access_token:
                raise UniviewCloudAuthError("Uniview Cloud session is not authenticated")
            headers["Authorization"] = self._access_token

        try:
            response = await self._session.post(
                f"{self._api_base_url}{path}",
                json=data,
                headers=headers,
            )
        except ClientError as err:
            raise UniviewCloudError(f"Unable to connect to Uniview Cloud: {err}") from err

        if response.status in (401, 403):
            self._access_token = None
            raise UniviewCloudAuthError("Uniview Cloud authentication failed")
        if response.status >= 400:
            raise UniviewCloudError(
                f"Uniview Cloud request failed with HTTP {response.status}"
            )

        payload = await response.json(content_type=None)
        code = payload.get("code")
        if code == 200:
            return payload.get("data") or {}
        if code in (2004, 401, 403):
            raise UniviewCloudAuthError(
                payload.get("message")
                or payload.get("msg")
                or "Invalid Uniview Cloud credentials"
            )
        raise UniviewCloudError(
            payload.get("message")
            or payload.get("msg")
            or f"Uniview Cloud request failed with code {code}"
        )

    async def _async_post_device_list(self) -> Any:
        """Fetch the device list with the request shapes seen across UniEase hosts."""
        last_error: UniviewCloudError | None = None
        for path in _DEVICE_LIST_PATHS:
            for data in _DEVICE_LIST_PAYLOADS:
                try:
                    payload = await self._async_post(path, data)
                except UniviewCloudError as err:
                    if not self._is_invalid_parameter_error(err):
                        raise
                    last_error = err
                    continue

                if self._extract_list(payload) or path == _DEVICE_LIST_PATHS[-1]:
                    return payload

        raise UniviewCloudError(
            f"Device list request rejected by UniEase: {last_error}"
        ) from last_error

    async def _async_get_channels(self, device: dict[str, Any]) -> list[dict[str, Any]]:
        """Fetch channel records for a multi-channel device."""
        device_serial = device.get("deviceSerial") or device.get("serial") or device.get("sn")
        if not device_serial:
            return []

        try:
            payload = await self._async_post(
                "/openapi/inner/device/channel/list",
                {
                    "deviceSerial": device_serial,
                    "pageNo": 1,
                    "pageSize": 64,
                },
            )
        except UniviewCloudError:
            return []
        return self._extract_list(payload)

    @staticmethod
    def _hash_password(password: str) -> str:
        """Return the password hash used by the EZCloud web portal."""
        first = hashlib.md5(password.encode("utf-8")).hexdigest()
        return hashlib.md5((first + first[:8]).encode("utf-8")).hexdigest()

    @staticmethod
    def _normalize_api_base_url(server_address: str) -> str:
        """Return a complete HTTPS API URL for a login server address."""
        server_address = server_address.rstrip("/")
        if server_address.startswith(("http://", "https://")):
            return server_address
        return f"https://{server_address}"

    @staticmethod
    def _is_invalid_parameter_error(err: Exception) -> bool:
        """Return true when UniEase rejects only the request parameter shape."""
        return "invalid parameter" in str(err).lower()

    @staticmethod
    def _extract_list(payload: Any) -> list[dict[str, Any]]:
        """Extract a list from common EZCloud response shapes."""
        if isinstance(payload, list):
            return payload
        if not isinstance(payload, dict):
            return []
        for key in (
            "list",
            "rows",
            "records",
            "devices",
            "deviceList",
            "channelList",
            "shareableDeviceList",
        ):
            value = payload.get(key)
            if isinstance(value, list):
                return value
        page = payload.get("page")
        if isinstance(page, dict):
            return UniviewCloudClient._extract_list(page)
        return []

    def _parse_device(self, item: dict[str, Any]) -> UniviewDevice:
        identifier = str(
            item.get("id")
            or item.get("deviceId")
            or item.get("device_id")
            or item.get("deviceSerial")
            or item.get("serial")
            or item.get("sn")
            or item.get("deviceSn")
            or item.get("channel_id")
        )
        return UniviewDevice(
            identifier=identifier,
            name=str(
                item.get("name")
                or item.get("deviceName")
                or item.get("device_name")
                or item.get("channelName")
                or identifier
            ),
            online=self._parse_online(item),
            model=item.get("model") or item.get("deviceModel") or item.get("deviceType"),
            serial_number=item.get("deviceSerial") or item.get("serial") or item.get("sn"),
            stream_url=item.get("stream_url") or item.get("rtsp_url"),
            snapshot_url=item.get("snapshot_url"),
            raw=item,
        )

    def _parse_channel(
        self,
        parent: dict[str, Any],
        item: dict[str, Any],
    ) -> UniviewDevice:
        parent_serial = str(
            parent.get("deviceSerial")
            or parent.get("serial")
            or parent.get("sn")
            or parent.get("deviceSn")
        )
        channel_no = item.get("channelNo") or item.get("channel_id") or item.get("id")
        identifier = str(
            item.get("channelSn")
            or f"{parent_serial}_{channel_no}"
        )
        parent_name = parent.get("deviceName") or parent.get("name") or parent_serial
        channel_name = item.get("channelName") or item.get("name") or f"Channel {channel_no}"

        return UniviewDevice(
            identifier=identifier,
            name=f"{parent_name} {channel_name}",
            online=self._parse_online(item),
            model=item.get("channelType") or "Camera Channel",
            serial_number=item.get("channelSn") or parent_serial,
            stream_url=item.get("stream_url") or item.get("rtsp_url"),
            snapshot_url=item.get("snapshot_url"),
            raw={**item, "parentDevice": parent},
        )

    @staticmethod
    def _parse_online(item: dict[str, Any]) -> bool:
        for key in ("online", "is_online", "isOnline"):
            if key in item:
                return bool(item[key])
        status = item.get("status") or item.get("deviceStatus") or item.get("netStatus")
        if isinstance(status, str):
            return status.lower() in {"online", "1", "true", "enable", "enabled"}
        if status is None and "enable" in item:
            return bool(item["enable"])
        return status == 1
