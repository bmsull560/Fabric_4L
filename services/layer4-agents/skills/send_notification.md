---
name: send_notification
description: Sends notifications via email, Slack, or Microsoft Teams
---

# Send Notification

Send notifications via email (SendGrid), Slack, or Microsoft Teams.

## Parameters

- `channel`: enum — email, slack, teams (required)
- `recipients`: array — Recipient addresses/channels (required)
- `subject`: string — Message subject (required)
- `message`: string — Message body (required)
- `attachments`: array — Optional file attachments (optional)

## Steps

1. Validate channel and recipient format
2. Build channel-specific payload
3. Send via appropriate API
4. Return delivery status

## Output

Returns SendNotificationOutput with:
- `success`: Boolean delivery status
- `message_id`: Provider message ID
- `error`: Error message if failed
