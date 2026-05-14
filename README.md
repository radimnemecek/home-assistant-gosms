# GoSMS for Home Assistant

Custom Home Assistant integration for sending SMS messages through GoSMS.

## Status

Release candidate for public testing.

## Features

- UI setup and reconfigure flow
- Send SMS via `gosms.send_sms`
- Preview SMS via `gosms.preview_sms` (does not send)
- Optional per-action channel override (`channel`)
- Single recipient (`recipient`) and multiple recipients (`recipients`)
- GoSMS Balance sensor
- Configurable balance refresh interval via integration options
- Safe Home Assistant diagnostics with sensitive field redaction

## Requirements

- Home Assistant `2024.6.0` or newer
- Valid GoSMS API credentials:
  - Client ID
  - Client Secret
  - Channel ID

## Installation

### HACS (Custom Repository)

Until this integration is listed in default HACS repositories, install it as a custom repository:

1. Open HACS.
2. Open the three-dots menu in the top-right corner.
3. Select **Custom repositories**.
4. Add repository URL: `https://github.com/radaogg207/home-assistant-gosms`.
5. Select category: **Integration**.
6. Install **GoSMS** from HACS.
7. Restart Home Assistant.

### Manual Installation

1. Copy `custom_components/gosms` to `/config/custom_components/gosms`.
2. Restart Home Assistant.

## Setup

1. Go to **Settings -> Devices & services -> Add integration**.
2. Search for **GoSMS**.
3. Enter:
   - Client ID
   - Client Secret
   - Channel ID

These values are available in GoSMS administration/API settings.

## Actions / Services

### `gosms.send_sms`

Single recipient:

```yaml
action: gosms.send_sms
data:
  recipient: "+420777123456"
  message: "Test SMS from Home Assistant"
```

Multiple recipients:

```yaml
action: gosms.send_sms
data:
  recipients:
    - "+420777123456"
    - "+420777987654"
  message: "Test SMS to multiple recipients"
```

Optional channel override:

```yaml
action: gosms.send_sms
data:
  channel: 123456
  recipient: "+420777123456"
  message: "Test from another GoSMS channel"
```

### `gosms.preview_sms`

`gosms.preview_sms` checks message details using the GoSMS test endpoint and does not send an SMS.

Basic preview:

```yaml
action: gosms.preview_sms
data:
  recipient: "+420777123456"
  message: "Preview SMS from Home Assistant"
```

Preview with response variable:

```yaml
action: gosms.preview_sms
data:
  recipients:
    - "+420777123456"
    - "+420777987654"
  message: "Preview SMS from Home Assistant"
response_variable: preview_result
```

## Example Automation

```yaml
alias: Freezer Temperature SMS Alert
description: Send an SMS when the freezer temperature rises above the safe threshold.
triggers:
  - trigger: numeric_state
    entity_id: sensor.freezer_temperature
    above: -10
conditions: []
actions:
  - action: gosms.send_sms
    data:
      recipient: "+420777123456"
      message: >-
        Warning: Freezer temperature is {{ states('sensor.freezer_temperature') }} °C.
mode: single
```

## Balance Sensor

- Provides GoSMS account balance data in Home Assistant.
- Default update interval: 30 minutes.
- Configurable range: 5 to 1440 minutes.

## Options

The integration currently supports one option:

- `balance_update_interval_minutes`

## Diagnostics

- Home Assistant can generate diagnostics for this integration when reporting issues.
- Diagnostics redact sensitive data (for example credentials/tokens and phone/message fields).
- Review diagnostics before posting publicly.

## Security and Privacy

- Never share your Client Secret.
- Prefer international phone number format such as `+420777123456`.
- The integration does not store SMS history.
- Diagnostics redact sensitive fields, but always review diagnostic output before sharing it publicly.

## Development

GitHub Actions validate this repository on push, pull request, and manual runs.

The workflow runs:

- HACS validation
- Home Assistant Hassfest validation

## Troubleshooting

- GoSMS does not appear after manual installation:
  - Verify folder path is `/config/custom_components/gosms`.
  - Restart Home Assistant.
- Authentication failed:
  - Verify Client ID and Client Secret.
- SMS fails:
  - Verify account credit, Channel ID, and recipient format.
- Balance unavailable:
  - Check GoSMS API connectivity and Home Assistant logs.
- `preview_sms` returns no visible output:
  - Use `response_variable` in automations or check the response panel in Developer Tools.

## Changelog

### v0.9.3

- Adjusted HACS validation workflow to pass repository explicitly.
- No Home Assistant runtime behavior changed.

### v0.9.2

- Adjusted hacs.json for HACS validation.
- No Home Assistant runtime behavior changed.

### v0.9.1

- Fixed HACS/Hassfest validation metadata.
- Corrected repository URLs in manifest.
- Simplified hacs.json.
- No Home Assistant runtime behavior changed.

### v0.9.0

- README polished for public/HACS release readiness.
- Added explicit HACS custom repository installation instructions.
- Expanded setup, services, options, diagnostics, security/privacy, and troubleshooting documentation.
- No Home Assistant runtime behavior changed.

### v0.8.0

- Added GitHub Actions validation workflow for HACS and Hassfest checks.
- Added validation documentation for development/public-readiness.
- No Home Assistant runtime behavior changed.

### v0.7.0

- Added Home Assistant diagnostics support for GoSMS config entries.
- Diagnostics include safe integration and runtime information while redacting sensitive fields.
- Diagnostics do not expose raw API payload/response data.
- Integration behavior for SMS sending, preview, channel override, and balance updates remains unchanged.

### v0.6.0

- Added a minimal integration options flow with a single option: `balance_update_interval_minutes`.
- Balance sensor refresh interval can now be configured in integration options within bounds 5-1440 minutes.
- Default balance refresh interval remains 30 minutes.
- SMS sending, SMS preview, recipient/recipients behavior, and channel override behavior remain unchanged.

### v0.5.0

- Added optional `channel` field to `gosms.send_sms` and `gosms.preview_sms` services. If omitted, the default configured channel is used. If provided, the specified GoSMS Channel ID is used for that call only.
- Removed support for `config_entry_id` in service calls (was never released in a public version).
- Existing automations remain backward compatible.

### v0.4.0

- Added `gosms.preview_sms` service using GoSMS test endpoint for safe SMS preview without sending.
- `gosms.preview_sms` supports `recipient` and `recipients` inputs with the same normalization behavior as `gosms.send_sms`.
- Preview service supports response data for `response_variable` (for example price/currency/sms count when available).

### v0.3.1

- Added missing translation for `reconfigure_successful` so reconfigure no longer shows raw key text.
- Fixed Channel ID form behavior: no misleading default during initial setup and validation now requires integer value >= 1.

### v0.3.0

- Added GoSMS Balance sensor using organization detail data from GoSMS API.
- Balance refresh is handled by a DataUpdateCoordinator (30-minute interval).
- Existing `gosms.send_sms`, `recipient`, `recipients`, config flow, and reconfigure flow stay unchanged.

### v0.2.0

- Added reconfigure flow to update Client ID, Client Secret and Channel ID from Home Assistant UI.
- Enhanced `gosms.send_sms` to support multiple recipients via `recipients` while keeping `recipient` compatibility.
- Added service documentation for `recipient` and `recipients` fields.
