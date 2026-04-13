"""Notification service for human-in-the-loop workflows.

Provides multi-channel notifications:
- In-app notifications (via WebSocket)
- Email notifications (for critical pauses)
- Webhook callbacks (for external integrations)
- Push notifications (for mobile/PWA)
"""

import asyncio
import hmac
import hashlib
import json
import logging
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import aiohttp

from ..models.pause_point import PauseSeverity, PauseReason

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """Available notification channels."""
    IN_APP = "in_app"           # WebSocket/SSE to connected clients
    EMAIL = "email"             # Email notification
    WEBHOOK = "webhook"         # External webhook callback
    PUSH = "push"               # Push notification (mobile/PWA)
    SLACK = "slack"             # Slack message
    TEAMS = "teams"             # Microsoft Teams message


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class NotificationEvent:
    """A notification event to be delivered across channels."""
    event_id: str
    workflow_id: str
    tenant_id: Optional[str]
    user_id: Optional[str]
    event_type: str  # workflow_paused, workflow_completed, etc.
    title: str
    message: str
    priority: NotificationPriority
    channels: List[NotificationChannel]
    payload: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    delivered: Dict[NotificationChannel, bool] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize delivery tracking."""
        for channel in self.channels:
            if channel not in self.delivered:
                self.delivered[channel] = False


@dataclass
class NotificationPreference:
    """User notification preferences."""
    user_id: str
    channels: List[NotificationChannel]
    pause_severity_threshold: PauseSeverity = PauseSeverity.WARNING
    quiet_hours_start: Optional[int] = None  # Hour (0-23) when quiet hours start
    quiet_hours_end: Optional[int] = None    # Hour (0-23) when quiet hours end
    webhook_url: Optional[str] = None
    email: Optional[str] = None
    slack_webhook: Optional[str] = None


class NotificationService:
    """Multi-channel notification service.
    
    Features:
    - Intelligent routing based on severity and preferences
    - Batching for high-frequency events
    - Delivery tracking and retry logic
    - Quiet hours support
    - Webhook signature verification
    
    Example:
        service = NotificationService()
        await service.notify_workflow_paused(
            workflow_id="wf-123",
            user_id="user-001",
            pause_point=pause_point_dict,
            channels=[NotificationChannel.EMAIL, NotificationChannel.WEBHOOK]
        )
    """
    
    def __init__(
        self,
        webhook_secret: Optional[str] = None,
        email_config: Optional[Dict] = None,
        default_channels: Optional[List[NotificationChannel]] = None
    ):
        """Initialize notification service.
        
        Args:
            webhook_secret: Secret for webhook HMAC signatures
            email_config: SMTP configuration for email notifications
            default_channels: Default channels for notifications
        """
        self.webhook_secret = webhook_secret
        self.email_config = email_config or {}
        self.default_channels = default_channels or [NotificationChannel.IN_APP]
        
        # User preferences storage (in production, use database)
        self._preferences: Dict[str, NotificationPreference] = {}
        
        # Event queue for batched processing
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._batch_task: Optional[asyncio.Task] = None
        
        # Webhook session (reused for efficiency)
        self._webhook_session: Optional[aiohttp.ClientSession] = None
        
        # Callbacks for in-app notifications
        self._in_app_callbacks: List[Callable[[NotificationEvent], None]] = []
    
    async def start(self) -> None:
        """Start background batch processing."""
        self._batch_task = asyncio.create_task(self._batch_processor())
        self._webhook_session = aiohttp.ClientSession()
        logger.info("Notification service started")
    
    async def stop(self) -> None:
        """Stop background processing."""
        if self._batch_task:
            self._batch_task.cancel()
            try:
                await self._batch_task
            except asyncio.CancelledError:
                pass
            self._batch_task = None
        if self._webhook_session:
            await self._webhook_session.close()
            self._webhook_session = None
        logger.info("Notification service stopped")
    
    def register_in_app_callback(self, callback: Callable[[NotificationEvent], None]) -> None:
        """Register a callback for in-app notifications.
        
        The callback receives NotificationEvent and should handle
        WebSocket broadcasting or UI updates.
        """
        self._in_app_callbacks.append(callback)
    
    def set_user_preferences(self, preference: NotificationPreference) -> None:
        """Set notification preferences for a user."""
        self._preferences[preference.user_id] = preference
    
    def get_user_preferences(self, user_id: str) -> NotificationPreference:
        """Get notification preferences for a user."""
        if user_id not in self._preferences:
            # Return default preferences
            return NotificationPreference(
                user_id=user_id,
                channels=list(self.default_channels)
            )
        return self._preferences[user_id]
    
    async def notify_workflow_paused(
        self,
        workflow_id: str,
        pause_point: Dict[str, Any],
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        channels: Optional[List[NotificationChannel]] = None
    ) -> NotificationEvent:
        """Send notification when workflow pauses for human input.
        
        Automatically determines priority based on pause severity.
        """
        severity_str = pause_point.get("severity", "warning")
        severity = PauseSeverity(severity_str) if severity_str in [s.value for s in PauseSeverity] else PauseSeverity.WARNING
        
        # Map pause severity to notification priority
        priority_map = {
            PauseSeverity.INFO: NotificationPriority.NORMAL,
            PauseSeverity.WARNING: NotificationPriority.HIGH,
            PauseSeverity.CRITICAL: NotificationPriority.URGENT
        }
        priority = priority_map.get(severity, NotificationPriority.HIGH)
        
        event = NotificationEvent(
            event_id=f"notif-{datetime.now(timezone.utc).timestamp()}-{workflow_id}-{id(pause_point) % 10000:04d}",
            workflow_id=workflow_id,
            tenant_id=tenant_id,
            user_id=user_id,
            event_type="workflow_paused",
            title=pause_point.get("title", "Workflow Paused"),
            message=pause_point.get("message", "Action required"),
            priority=priority,
            channels=channels or self._get_channels_for_user(user_id, severity),
            payload={
                "pause_point": pause_point,
                "pause_reason": pause_point.get("reason"),
                "required_inputs": [
                    f.get("name") for f in pause_point.get("required_inputs", [])
                ]
            }
        )
        
        await self._event_queue.put(event)
        return event
    
    async def notify_workflow_completed(
        self,
        workflow_id: str,
        status: str,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        result_summary: Optional[Dict] = None,
        channels: Optional[List[NotificationChannel]] = None
    ) -> NotificationEvent:
        """Send notification when workflow completes."""
        event = NotificationEvent(
            event_id=f"notif-{datetime.now(timezone.utc).timestamp()}-{workflow_id}-{hash(str(status)) % 10000:04d}",
            workflow_id=workflow_id,
            tenant_id=tenant_id,
            user_id=user_id,
            event_type="workflow_completed",
            title=f"Workflow {status.title()}",
            message=f"Workflow {workflow_id} has {status}",
            priority=NotificationPriority.NORMAL,
            channels=channels or self._get_channels_for_user(user_id),
            payload={
                "status": status,
                "result_summary": result_summary or {}
            }
        )
        
        await self._event_queue.put(event)
        return event
    
    async def notify_checkpoint_reached(
        self,
        workflow_id: str,
        checkpoint_id: str,
        node_name: str,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        channels: Optional[List[NotificationChannel]] = None
    ) -> NotificationEvent:
        """Send notification when workflow reaches a checkpoint."""
        event = NotificationEvent(
            event_id=f"notif-{datetime.now(timezone.utc).timestamp()}-{workflow_id}-{hash(checkpoint_id) % 10000:04d}",
            workflow_id=workflow_id,
            tenant_id=tenant_id,
            user_id=user_id,
            event_type="checkpoint_reached",
            title=f"Checkpoint: {node_name}",
            message=f"Workflow reached checkpoint after {node_name}",
            priority=NotificationPriority.LOW,
            channels=channels or [NotificationChannel.IN_APP],  # Low priority, in-app only
            payload={
                "checkpoint_id": checkpoint_id,
                "node_name": node_name
            }
        )
        
        await self._event_queue.put(event)
        return event
    
    def _get_channels_for_user(
        self,
        user_id: Optional[str],
        severity: PauseSeverity = PauseSeverity.WARNING
    ) -> List[NotificationChannel]:
        """Determine notification channels based on user preferences and severity."""
        if not user_id:
            return list(self.default_channels)
        
        prefs = self.get_user_preferences(user_id)
        
        # Filter channels based on severity threshold
        if severity.value < prefs.pause_severity_threshold.value:
            # Below threshold - only in-app
            return [NotificationChannel.IN_APP]
        
        return prefs.channels
    
    async def _batch_processor(self) -> None:
        """Background task to process notification queue."""
        while True:
            try:
                event = await self._event_queue.get()
                await self._process_notification(event)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing notification: {e}")
    
    async def _process_notification(self, event: NotificationEvent) -> None:
        """Process a single notification event across all channels."""
        for channel in event.channels:
            try:
                if channel == NotificationChannel.IN_APP:
                    await self._send_in_app(event)
                elif channel == NotificationChannel.EMAIL:
                    await self._send_email(event)
                elif channel == NotificationChannel.WEBHOOK:
                    await self._send_webhook(event)
                elif channel == NotificationChannel.SLACK:
                    await self._send_slack(event)
                elif channel == NotificationChannel.TEAMS:
                    await self._send_teams(event)
                
                event.delivered[channel] = True
                
            except Exception as e:
                logger.error(f"Failed to send {channel} notification: {e}")
                event.delivered[channel] = False
    
    async def _send_in_app(self, event: NotificationEvent) -> None:
        """Send in-app notification via registered callbacks."""
        for callback in self._in_app_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"In-app callback failed: {e}")
    
    async def _send_email(self, event: NotificationEvent) -> None:
        """Send email notification."""
        if not event.user_id:
            return
        
        prefs = self.get_user_preferences(event.user_id)
        if not prefs.email:
            logger.warning(f"No email configured for user {event.user_id}")
            return
        
        # In production, integrate with email service (SendGrid, SES, etc.)
        logger.info(f"[EMAIL] To: {prefs.email}, Subject: {event.title}, Body: {event.message}")
    
    async def _send_webhook(self, event: NotificationEvent) -> None:
        """Send webhook notification."""
        if not event.user_id:
            return
        
        prefs = self.get_user_preferences(event.user_id)
        if not prefs.webhook_url:
            return
        
        if not self._webhook_session:
            logger.warning("Webhook session not initialized")
            return
        
        payload = {
            "event_id": event.event_id,
            "workflow_id": event.workflow_id,
            "event_type": event.event_type,
            "title": event.title,
            "message": event.message,
            "priority": event.priority.value,
            "timestamp": event.created_at.isoformat(),
            "payload": event.payload
        }
        
        try:
            async with self._webhook_session.post(
                prefs.webhook_url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Workflow-Event": event.event_type,
                    "X-Workflow-Signature": self._generate_signature(payload)
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status >= 400:
                    logger.warning(f"Webhook returned {response.status}")
        except Exception as e:
            logger.error(f"Webhook delivery failed: {e}")
            raise
    
    async def _send_slack(self, event: NotificationEvent) -> None:
        """Send Slack notification."""
        if not event.user_id:
            return
        
        prefs = self.get_user_preferences(event.user_id)
        if not prefs.slack_webhook:
            return
        
        color = {
            NotificationPriority.LOW: "#36a64f",
            NotificationPriority.NORMAL: "#36a64f",
            NotificationPriority.HIGH: "#daa520",
            NotificationPriority.URGENT: "#ff0000"
        }.get(event.priority, "#36a64f")
        
        slack_payload = {
            "attachments": [
                {
                    "color": color,
                    "title": event.title,
                    "text": event.message,
                    "fields": [
                        {
                            "title": "Workflow ID",
                            "value": event.workflow_id,
                            "short": True
                        },
                        {
                            "title": "Event Type",
                            "value": event.event_type,
                            "short": True
                        }
                    ],
                    "footer": "Value Fabric Layer 4",
                    "ts": int(event.created_at.timestamp())
                }
            ]
        }
        
        if self._webhook_session:
            try:
                async with self._webhook_session.post(
                    prefs.slack_webhook,
                    json=slack_payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        logger.warning(f"Slack webhook returned {response.status}")
            except Exception as e:
                logger.error(f"Slack delivery failed: {e}")
    
    async def _send_teams(self, event: NotificationEvent) -> None:
        """Send Microsoft Teams notification."""
        # Similar to Slack, with Teams-specific message format
        logger.info(f"[TEAMS] {event.title}: {event.message}")
    
    def _generate_signature(self, payload: Dict) -> str:
        """Generate HMAC signature for webhook verification."""
        if not self.webhook_secret:
            return ""

        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            self.webhook_secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        return f"sha256={signature}"
    
    def is_quiet_hours(self, user_id: str) -> bool:
        """Check if current time is in user's quiet hours."""
        prefs = self.get_user_preferences(user_id)
        
        if prefs.quiet_hours_start is None or prefs.quiet_hours_end is None:
            return False
        
        current_hour = datetime.now(timezone.utc).hour
        
        if prefs.quiet_hours_start <= prefs.quiet_hours_end:
            # Simple range (e.g., 22:00 - 08:00 doesn't work here)
            return prefs.quiet_hours_start <= current_hour < prefs.quiet_hours_end
        else:
            # Wrapped range (e.g., 22:00 - 08:00)
            return current_hour >= prefs.quiet_hours_start or current_hour < prefs.quiet_hours_end


# Global singleton
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """Get or create the global notification service."""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
