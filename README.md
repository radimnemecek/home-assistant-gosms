# GoSMS for Home Assistant

Custom Home Assistant integration for sending SMS messages using the GoSMS gateway.

## Status

Early testing version.

## Features

- Setup through Home Assistant UI
- Send SMS from automations, scripts and Developer Tools
- Supports GoSMS Client ID, Client Secret and Channel ID
- Adds a GoSMS Balance sensor refreshed periodically from organization detail

## Manual Installation

1. Copy `custom_components/gosms` to `/config/custom_components/gosms`
2. Restart Home Assistant

## Setup

1. Go to Settings -> Devices & services -> Add integration
2. Search for GoSMS
3. Enter Client ID, Client Secret and Channel ID
4. To update credentials later, open the integration card menu and use Reconfigure

## Usage


### Single Recipient (Default Channel)

```yaml
action: gosms.send_sms
data:
  recipient: "+420777123456"
  message: "Test SMS from Home Assistant"
```

### Multiple Recipients

```yaml
action: gosms.send_sms
data:
  recipients:
    - "+420777123456"
    - "+420777987654"
  message: "Test SMS to multiple recipients"
```

### Channel Override Example

```yaml
action: gosms.send_sms
data:
  channel: 123456
  recipient: "+420777123456"
  message: "Test from another GoSMS channel"
```

### SMS Preview (Dry Run)

`gosms.preview_sms` checks message details using GoSMS test endpoint and does not send an SMS.

```yaml
action: gosms.preview_sms
data:
  channel: 123456
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

## Notes

- GoSMS API credentials are stored in Home Assistant config entries.
- Do not share your Client Secret publicly.
- The GoSMS Balance sensor refresh interval is configurable in integration options.
- Allowed balance update interval range is 5 to 1440 minutes.
- Default balance update interval is 30 minutes.
- Provide phone numbers explicitly, preferably in international format (for example `+420777123456`).

## Diagnostics

- Home Assistant can generate integration diagnostics when reporting issues.
- GoSMS diagnostics redact sensitive data.
- Review diagnostics before posting them publicly.

## Security and Privacy

- Never share your Client Secret.
- Prefer international phone number format such as `+420777123456`.
- The integration does not store SMS history.

## Validation

- GitHub Actions validates this repository on push, pull request, and manual runs.
- The workflow runs HACS validation and Home Assistant Hassfest validation.

## Changelog


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
