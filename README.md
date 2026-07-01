# Uniview Cloud for Home Assistant

Custom Home Assistant integration for Uniview cloud/app accounts.

This project is an early scaffold. The Home Assistant side is structured for HACS, but the Uniview cloud endpoints still need to be confirmed against a test account before this can be used with real devices.

## Current scope

- Config flow for Uniview app credentials.
- Cloud client isolated in `custom_components/uniview_cloud/client.py`.
- Camera entities when a stream URL is available.
- Online binary sensor per device.
- Model sensor per device.
- Diagnostics with username/password/token redaction.

## HACS install

1. Open HACS.
2. Add this repository as a custom repository.
3. Select category `Integration`.
4. Install `Uniview Cloud`.
5. Restart Home Assistant.
6. Go to Settings > Devices & services > Add integration > Uniview Cloud.

## Development status

The initial client assumes placeholder routes:

- `POST /login`
- `GET /devices`

These routes are intentionally isolated and expected to change once the Uniview app/cloud API is confirmed.

Do not commit real Uniview credentials, tokens, packet captures, or account-specific device identifiers.

## Repository layout

```text
custom_components/uniview_cloud/
  __init__.py
  binary_sensor.py
  camera.py
  client.py
  config_flow.py
  const.py
  diagnostics.py
  entity.py
  manifest.json
  sensor.py
  translations/en.json
```

## License

MIT
