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


def test_extract_list_common_shapes() -> None:
    """Extract device lists from common API response shapes."""
    assert UniviewCloudClient._extract_list([{"id": "1"}]) == [{"id": "1"}]
    assert UniviewCloudClient._extract_list({"list": [{"id": "2"}]}) == [{"id": "2"}]
    assert UniviewCloudClient._extract_list({"page": {"records": [{"id": "3"}]}}) == [
        {"id": "3"}
    ]


def test_hash_password_matches_ezcloud_web_algorithm() -> None:
    """Hash passwords like the EZCloud web portal."""
    assert (
        UniviewCloudClient._hash_password("test123")
        == "35cc16b1c17a46c71c40f8c89ca892d8"
    )
