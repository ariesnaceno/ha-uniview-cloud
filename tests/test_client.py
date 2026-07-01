"""Tests for the Uniview Cloud client."""

from custom_components.uniview_cloud.client import UniviewCloudClient
from custom_components.uniview_cloud.const import DEFAULT_API_BASE_URL


def test_default_api_base_url_targets_uniease_overseas_host() -> None:
    """Use the host verified for UniEase accounts."""
    client = UniviewCloudClient(
        session=None,
        username="user",
        password="pass",
    )

    assert client._api_base_url == DEFAULT_API_BASE_URL
    assert client._api_base_url == "https://en.ezcloud.uniview.com"


def test_parse_device_minimal() -> None:
    """Parse a minimal cloud device payload."""
    client = UniviewCloudClient(
        session=None,
        username="user",
        password="pass",
        region="global",
        api_base_url="https://example.test",
    )

    device = client._parse_device(
        {
            "id": "camera-1",
            "name": "Front Gate",
            "online": True,
            "model": "IPC",
            "serial": "ABC123",
        }
    )

    assert device.identifier == "camera-1"
    assert device.name == "Front Gate"
    assert device.online is True
    assert device.model == "IPC"
    assert device.serial_number == "ABC123"


def test_parse_device_ezcloud_shape() -> None:
    """Parse a likely EZCloud device payload."""
    client = UniviewCloudClient(
        session=None,
        username="user",
        password="pass",
        region="global",
        api_base_url="https://example.test",
    )

    device = client._parse_device(
        {
            "deviceSerial": "SN123",
            "deviceName": "NVR",
            "deviceStatus": 1,
            "deviceModel": "NVR301",
        }
    )

    assert device.identifier == "SN123"
    assert device.name == "NVR"
    assert device.online is True
    assert device.model == "NVR301"
    assert device.serial_number == "SN123"


def test_parse_device_cdn_shape() -> None:
    """Parse the CDN device list shape used by some UniEase accounts."""
    client = UniviewCloudClient(
        session=None,
        username="user",
        password="pass",
        region="global",
        api_base_url="https://example.test",
    )

    device = client._parse_device(
        {
            "deviceSerial": "SN456",
            "deviceName": "Driveway",
            "deviceType": "IPC",
            "enable": True,
            "status": 1,
        }
    )

    assert device.identifier == "SN456"
    assert device.name == "Driveway"
    assert device.online is True
    assert device.model == "IPC"
    assert device.serial_number == "SN456"


def test_parse_channel_shape() -> None:
    """Parse a channel returned by an NVR."""
    client = UniviewCloudClient(
        session=None,
        username="user",
        password="pass",
        region="global",
        api_base_url="https://example.test",
    )

    device = client._parse_channel(
        {"deviceSerial": "NVR123", "deviceName": "Moon Home"},
        {
            "channelNo": 1,
            "channelSn": "NVR123_1",
            "channelName": "Front Door",
            "channelType": 0,
            "status": 1,
        },
    )

    assert device.identifier == "NVR123_1"
    assert device.name == "Moon Home Front Door"
    assert device.online is True
    assert device.model == "Camera Channel"
    assert device.serial_number == "NVR123_1"


def test_extract_list_common_shapes() -> None:
    """Extract device lists from common API response shapes."""
    assert UniviewCloudClient._extract_list([{"id": "1"}]) == [{"id": "1"}]
    assert UniviewCloudClient._extract_list({"list": [{"id": "2"}]}) == [{"id": "2"}]
    assert UniviewCloudClient._extract_list({"page": {"records": [{"id": "3"}]}}) == [
        {"id": "3"}
    ]
    assert UniviewCloudClient._extract_list({"shareableDeviceList": [{"id": "4"}]}) == [
        {"id": "4"}
    ]
    assert UniviewCloudClient._extract_list({"channelList": [{"id": "5"}]}) == [
        {"id": "5"}
    ]


def test_hash_password_matches_ezcloud_web_algorithm() -> None:
    """Hash passwords like the EZCloud web portal."""
    assert (
        UniviewCloudClient._hash_password("test123")
        == "35cc16b1c17a46c71c40f8c89ca892d8"
    )


def test_normalize_api_base_url_from_login_server_address() -> None:
    """Normalize the account-specific server address returned by login."""
    assert (
        UniviewCloudClient._normalize_api_base_url("ap.ezcloud.uniview.com")
        == "https://ap.ezcloud.uniview.com"
    )
    assert (
        UniviewCloudClient._normalize_api_base_url("https://ap.ezcloud.uniview.com")
        == "https://ap.ezcloud.uniview.com"
    )


def test_invalid_parameter_error_detection() -> None:
    """Detect retryable UniEase parameter-shape errors."""
    assert UniviewCloudClient._is_invalid_parameter_error(Exception("Invalid parameter."))
    assert not UniviewCloudClient._is_invalid_parameter_error(Exception("User locked"))
