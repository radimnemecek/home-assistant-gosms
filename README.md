# GoSMS for Home Assistant

Custom integration for sending SMS messages from Home Assistant using GoSMS.

## Status

Early private testing version.

## Usage

After setup, call:

```yaml
action: gosms.send_sms
data:
  recipient: "+420777123456"
  message: "Test SMS from Home Assistant"