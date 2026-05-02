---
name: schedule_meeting
description: Schedules meetings with attendees using calendar APIs
---

# Schedule Meeting

Schedule meetings using Google Calendar or Outlook calendar APIs.

## Parameters

- `title`: string — Meeting title (required)
- `attendees`: array — Attendee email addresses (required)
- `duration_minutes`: integer — Duration 15-240 (default: 30)
- `preferred_times`: array — Preferred time slots ISO format (optional)
- `description`: string — Meeting description (optional)

## Steps

1. Authenticate with calendar provider
2. Find available time slot
3. Create calendar event with video conference
4. Send invitations to attendees
5. Return meeting details

## Output

Returns ScheduleMeetingOutput with:
- `meeting_id`: Calendar event ID
- `scheduled_time`: Confirmed time ISO format
- `calendar_link`: Calendar event link
- `success`: Boolean status
- `error`: Error message if failed
