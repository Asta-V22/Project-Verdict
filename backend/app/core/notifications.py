"""
Notification abstractions and providers.
"""

from __future__ import annotations

import logging
from typing import Protocol

from plyer import notification

from app.models.enums import UrgencyLevel

logger = logging.getLogger(__name__)


class NotificationProvider(Protocol):
    """Abstract interface for sending notifications."""

    def send_notification(
        self, title: str, message: str, urgency: UrgencyLevel
    ) -> None:
        """Dispatch a notification using the provider's mechanism."""
        ...


class DesktopNotificationProvider:
    """Uses plyer to send native desktop notifications."""

    def send_notification(
        self, title: str, message: str, urgency: UrgencyLevel
    ) -> None:
        """Send a desktop toast notification."""
        # Simple escalation behavior isolated to the desktop provider layer:
        # adjust timeout duration based on urgency.
        timeout_map = {
            UrgencyLevel.GENTLE: 5,
            UrgencyLevel.MODERATE: 10,
            UrgencyLevel.URGENT: 20,
        }
        timeout = timeout_map.get(urgency, 10)

        try:
            notification.notify(
                title=title,
                message=message,
                app_name="Project Verdict",
                timeout=timeout,
            )
        except Exception:
            logger.exception("Failed to send desktop notification")
