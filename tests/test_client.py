"""Tests for the Uniview Cloud client."""

from custom_components.uniview_cloud.client import UniviewCloudClient


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
