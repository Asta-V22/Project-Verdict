"""
Notification service — abstraction layer for desktop notifications.

The business logic calls `NotificationService.send()` without knowing
which platform-specific implementation is in use. Future implementations
can swap to Tauri native notifications or mobile push without changing
any service or router code.

Phase 1 implementation: windows-toasts (modern WinRT-based library).
"""

from __future__ import annotations

import logging
import sys
from abc import ABC, abstractmethod
from typing import ClassVar

logger = logging.getLogger(__name__)


class NotificationService(ABC):
    """
    Abstract base for notification delivery.

    All notification implementations must inherit from this class.
    This allows the reminder engine and other services to remain
    decoupled from the notification transport.
    """

    @abstractmethod
    def send(self, title: str, message: str, urgency: str = "gentle") -> bool:
        """
        Send a desktop notification.

        Args:
            title: Notification title.
            message: Notification body text.
            urgency: One of 'gentle', 'moderate', 'urgent'.
                     Controls display duration and styling.

        Returns:
            True if the notification was sent successfully.
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this notification backend is functional."""
        ...


class WindowsNotificationService(NotificationService):
    """
    Windows toast notification implementation using windows-toasts.

    Uses modern WinRT APIs for reliable, native toast notifications
    on Windows 10/11.
    """

    # Urgency maps to notification scenario/duration behavior
    _URGENCY_PREFIX: ClassVar[dict[str, str]] = {
        "gentle": "📋",
        "moderate": "⚠️",
        "urgent": "🚨",
    }

    def __init__(self) -> None:
        self._toaster = None
        self._toast_class = None
        self._available = False
        try:
            from windows_toasts import Toast, WindowsToaster

            self._toaster = WindowsToaster("Project Verdict")
            self._toast_class = Toast
            self._available = True
            logger.info("Windows notification service initialized (windows-toasts)")
        except ImportError:
            logger.warning(
                "windows-toasts not installed — notifications disabled. "
                "Install with: pip install windows-toasts"
            )
        except Exception:
            logger.exception("Failed to initialize Windows notifications")

    def send(self, title: str, message: str, urgency: str = "gentle") -> bool:
        if not self._available or self._toaster is None or self._toast_class is None:
            logger.debug("Notification skipped (service unavailable): %s", title)
            return False

        prefix = self._URGENCY_PREFIX.get(urgency, "")
        display_title = f"{prefix} {title}" if prefix else title

        try:
            toast = self._toast_class()
            toast.text_fields = [display_title, message]
            self._toaster.show_toast(toast)
            logger.info("Notification sent: %s (urgency=%s)", title, urgency)
            return True
        except Exception:
            logger.exception("Failed to send notification: %s", title)
            return False

    def is_available(self) -> bool:
        return self._available


class StubNotificationService(NotificationService):
    """
    No-op notification service for non-Windows platforms or testing.

    Logs all notifications without displaying them.
    """

    def send(self, title: str, message: str, urgency: str = "gentle") -> bool:
        logger.info(
            "[STUB NOTIFICATION] title=%r, message=%r, urgency=%s",
            title,
            message,
            urgency,
        )
        return True

    def is_available(self) -> bool:
        return True


def create_notification_service() -> NotificationService:
    """
    Factory function that returns the appropriate notification service
    for the current platform.
    """
    if sys.platform == "win32":
        service = WindowsNotificationService()
        if service.is_available():
            return service

    logger.info("Using stub notification service")
    return StubNotificationService()
