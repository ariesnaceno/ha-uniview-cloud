"""Tests for the Uniview Cloud client."""

from importlib import util
from pathlib import Path
import sys

COMPONENT_DIR = Path(__file__).parents[1] / "custom_components" / "uniview_cloud"

const_spec = util.spec_from_file_location(
    "custom_components.uniview_cloud.const",
    COMPONENT_DIR / "const.py",
)
const_module = util.module_from_spec(const_spec)
sys.modules[const_spec.name] = const_module
const_spec.loader.exec_module(const_module)

client_spec = util.spec_from_file_location(
    "custom_components.uniview_cloud.client",
    COMPONENT_DIR / "client.py",
)
client_module = util.module_from_spec(client_spec)
sys.modules[client_spec.name] = client_module
client_spec.loader.exec_module(client_module)

DEFAULT_API_BASE_URL = const_module.DEFAULT_API_BASE_URL
UniviewCloudClient = client_module.UniviewCloudClient


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


def test_parse_device_cdn_shape_with_stream_url() -> None:
    """Attach a CDN HLS URL to a single-channel camera."""
    client = UniviewCloudClient(
        session=None,
        username="user",
        password="pass",
        region="global",
        api_base_url="https://example.test",
    )

    device = client._parse_device(
        {
            "deviceSerial": "SN789",
            "deviceName": "DoorBell",
            "deviceModel": "OEU",
            "status": 1,
        },
        "https://example.test/live/doorbell.m3u8",
    )

    assert device.identifier == "SN789"
    assert device.name == "DoorBell"
    assert device.stream_url == "https://example.test/live/doorbell.m3u8"


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


def test_parse_channel_shape_with_stream_url() -> None:
    """Attach a CDN HLS URL to a channel camera."""
    client = UniviewCloudClient(
        session=None,
        username="user",
        password="pass",
        region="global",
        api_base_url="https://example.test",
    )

    device = client._parse_channel(
        {"deviceSerial": "NVR123", "deviceName": "Moon Home"},
        {"channelNo": "2", "channelName": "Kitchen", "status": 1},
        "https://example.test/live/channel-2.m3u8",
    )

    assert device.identifier == "NVR123_2"
    assert device.stream_url == "https://example.test/live/channel-2.m3u8"


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
    assert UniviewCloudClient._extract_list({"liveUrlList": [{"id": "6"}]}) == [
        {"id": "6"}
    ]


def test_live_url_by_channel() -> None:
    """Extract live stream URLs by channel number."""
    assert UniviewCloudClient._live_url_by_channel(
        {
            "liveUrlList": [
                {"channelNo": 1, "url": "https://example.test/one.m3u8"},
                {"channelNo": "2", "url": "https://example.test/two.m3u8"},
                {"channelNo": None, "url": "https://example.test/missing.m3u8"},
                {"channelNo": 3},
            ]
        }
    ) == {
        1: "https://example.test/one.m3u8",
        2: "https://example.test/two.m3u8",
    }


def test_first_live_url() -> None:
    """Extract the first live stream URL from a live URL payload."""
    assert (
        UniviewCloudClient._first_live_url(
            {
                "liveUrlList": [
                    {"channelNo": 1},
                    {"channelNo": 2, "url": "https://example.test/two.m3u8"},
                    {"channelNo": 3, "url": "https://example.test/three.m3u8"},
                ]
            }
        )
        == "https://example.test/two.m3u8"
    )
    assert UniviewCloudClient._first_live_url({"liveUrlList": []}) is None


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
