"""
JARVIS Brain Layer - Calendar & Email Orchestrator

High-level orchestrator for calendar and email operations with:
- Email triage: auto-classify, auto-archive promotions, flag real mail
- Calendar conflict detection and smart meeting time suggestions
- HITL gates for send/create/delete operations
- Draft reply generation with user approval
"""

import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from loguru import logger

from tools.base import RiskLevel


class EmailPriority(Enum):
    """Email priority classification."""
    URGENT = "urgent"
    IMPORTANT = "important"
    NORMAL = "normal"
    PROMOTIONAL = "promotional"
    SPAM = "spam"


@dataclass
class EmailDraft:
    """A draft email reply."""
    to: str
    subject: str
    body: str
    in_reply_to: str | None = None
    priority: EmailPriority = EmailPriority.NORMAL


@dataclass
class CalendarConflict:
    """A calendar conflict between events."""
    event_a: dict
    event_b: dict
    overlap_minutes: int
    suggestion: str


@dataclass
class TriageResult:
    """Result of email triage."""
    message_id: str
    subject: str
    sender: str
    priority: EmailPriority
    reason: str
    suggested_action: str
    auto_archived: bool = False


# === PROMOTIONAL DETECTION ===

_PROMO_SENDERS = {
    "noreply", "no-reply", "donotreply", "do-not-reply",
    "newsletter", "marketing", "promo", "deals", "offers",
    "notification", "updates", "digest", "weekly", "daily",
}

_PROMO_SUBJECT_PATTERNS = [
    r"unsubscribe", r"special offer", r"limited time", r"% off",
    r"sale", r"deal", r"promo", r"coupon", r"discount",
    r"newsletter", r"digest", r"weekly update", r"monthly update",
    r"your .* summary", r"what you missed", r"catch up",
]

_URGENT_SUBJECT_PATTERNS = [
    r"urgent", r"asap", r"immediate", r"critical", r"deadline",
    r"overdue", r"action required", r"please respond",
    r"time.sensitive", r"expires? (today|soon|tomorrow)",
]


class EmailTriage:
    """
    Email triage engine that classifies and prioritizes incoming emails.

    Rules:
    - Urgent/important emails → flagged for user attention
    - Promotional emails → auto-archived (with logging)
    - Normal emails → listed for review
    """

    def __init__(self, whitelisted_senders: list[str] | None = None):
        self.whitelisted_senders = set(
            s.lower() for s in (whitelisted_senders or [])
        )

    def classify(self, sender: str, subject: str, snippet: str = "") -> TriageResult:
        """
        Classify an email by priority.

        Args:
            sender: Email sender address
            subject: Email subject line
            snippet: Preview snippet of the email body

        Returns:
            TriageResult with priority and suggested action
        """
        sender_lower = sender.lower()
        subject_lower = subject.lower()
        combined = f"{subject_lower} {snippet.lower()}"

        # Check whitelisted senders first
        for wl in self.whitelisted_senders:
            if wl in sender_lower:
                return TriageResult(
                    message_id="",
                    subject=subject,
                    sender=sender,
                    priority=EmailPriority.IMPORTANT,
                    reason=f"Whitelisted sender: {wl}",
                    suggested_action="flag_for_review",
                )

        # Check for urgent patterns
        for pattern in _URGENT_SUBJECT_PATTERNS:
            if re.search(pattern, subject_lower):
                return TriageResult(
                    message_id="",
                    subject=subject,
                    sender=sender,
                    priority=EmailPriority.URGENT,
                    reason=f"Urgent keyword: {pattern}",
                    suggested_action="flag_for_review",
                )

        # Check for promotional patterns
        is_promo_sender = any(p in sender_lower for p in _PROMO_SENDERS)
        is_promo_subject = any(
            re.search(p, combined) for p in _PROMO_SUBJECT_PATTERNS
        )

        if is_promo_sender or is_promo_subject:
            return TriageResult(
                message_id="",
                subject=subject,
                sender=sender,
                priority=EmailPriority.PROMOTIONAL,
                reason="Promotional content detected",
                suggested_action="auto_archive",
                auto_archived=True,
            )

        # Default to normal
        return TriageResult(
            message_id="",
            subject=subject,
            sender=sender,
            priority=EmailPriority.NORMAL,
            reason="No special classification",
            suggested_action="list_for_review",
        )

    def triage_batch(self, messages: list[dict]) -> dict[str, list[TriageResult]]:
        """
        Triage a batch of emails.

        Args:
            messages: List of email dicts with 'sender', 'subject', 'snippet'

        Returns:
            Dict grouping results by priority
        """
        results: dict[str, list[TriageResult]] = {
            "urgent": [],
            "important": [],
            "normal": [],
            "promotional": [],
            "spam": [],
        }

        for msg in messages:
            result = self.classify(
                sender=msg.get("sender", ""),
                subject=msg.get("subject", ""),
                snippet=msg.get("snippet", ""),
            )
            result.message_id = msg.get("id", "")
            results[result.priority.value].append(result)

        return results


class CalendarOrchestrator:
    """
    Calendar orchestrator with conflict detection and smart suggestions.

    Features:
    - Detect scheduling conflicts between events
    - Suggest optimal meeting times based on focus blocks
    - Check availability before creating events
    """

    FOCUS_HOURS = (9, 12)  # Morning focus block
    AFTERNOON_HOURS = (14, 17)  # Afternoon focus block

    def detect_conflicts(
        self, events: list[dict], new_event: dict | None = None
    ) -> list[CalendarConflict]:
        """
        Detect conflicts between events.

        Args:
            events: List of existing calendar events
            new_event: Optional new event to check against existing

        Returns:
            List of detected conflicts
        """
        conflicts = []
        check_events = list(events)
        if new_event:
            check_events.append(new_event)

        for i, ev_a in enumerate(check_events):
            for ev_b in check_events[i + 1:]:
                overlap = self._calc_overlap(ev_a, ev_b)
                if overlap > 0:
                    conflicts.append(CalendarConflict(
                        event_a=ev_a,
                        event_b=ev_b,
                        overlap_minutes=overlap,
                        suggestion=self._suggest_resolution(ev_a, ev_b, overlap),
                    ))

        return conflicts

    def suggest_meeting_times(
        self,
        existing_events: list[dict],
        duration_minutes: int = 60,
        preferred_date: datetime | None = None,
    ) -> list[dict]:
        """
        Suggest available meeting times avoiding focus blocks.

        Args:
            existing_events: Current calendar events
            duration_minutes: Required meeting duration
            preferred_date: Target date (defaults to today/tomorrow)

        Returns:
            List of suggested time slots
        """
        if preferred_date is None:
            preferred_date = datetime.now(timezone.utc)

        # Build occupied time blocks
        occupied = []
        for ev in existing_events:
            start = self._parse_event_time(ev.get("start", ""))
            end = self._parse_event_time(ev.get("end", ""))
            if start and end:
                occupied.append((start, end))

        suggestions = []
        check_date = preferred_date

        # Check next 3 days
        for _ in range(3):
            for hour in range(9, 18):
                slot_start = check_date.replace(
                    hour=hour, minute=0, second=0, microsecond=0
                )
                slot_end = slot_start + timedelta(minutes=duration_minutes)

                # Skip focus hours for meetings
                if self.FOCUS_HOURS[0] <= hour < self.FOCUS_HOURS[1]:
                    continue

                # Check if slot is free
                is_free = True
                for occ_start, occ_end in occupied:
                    if slot_start < occ_end and slot_end > occ_start:
                        is_free = False
                        break

                if is_free:
                    suggestions.append({
                        "start": slot_start.isoformat(),
                        "end": slot_end.isoformat(),
                        "day": slot_start.strftime("%A"),
                        "time": slot_start.strftime("%I:%M %p"),
                    })

                if len(suggestions) >= 5:
                    return suggestions

            check_date += timedelta(days=1)

        return suggestions

    def _calc_overlap(self, ev_a: dict, ev_b: dict) -> int:
        """Calculate overlap in minutes between two events."""
        start_a = self._parse_event_time(ev_a.get("start", ""))
        end_a = self._parse_event_time(ev_a.get("end", ""))
        start_b = self._parse_event_time(ev_b.get("start", ""))
        end_b = self._parse_event_time(ev_b.get("end", ""))

        if not all([start_a, end_a, start_b, end_b]):
            return 0

        overlap_start = max(start_a, start_b)
        overlap_end = min(end_a, end_b)

        if overlap_start < overlap_end:
            return int((overlap_end - overlap_start).total_seconds() / 60)
        return 0

    def _parse_event_time(self, time_str: str) -> datetime | None:
        """Parse event time string to datetime."""
        if not time_str:
            return None
        try:
            return datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None

    def _suggest_resolution(
        self, ev_a: dict, ev_b: dict, overlap_minutes: int
    ) -> str:
        """Suggest how to resolve a conflict."""
        title_a = ev_a.get("title", ev_a.get("summary", "Event A"))
        title_b = ev_b.get("title", ev_b.get("summary", "Event B"))
        return (
            f"Conflict ({overlap_minutes}min overlap) between "
            f"'{title_a}' and '{title_b}'. "
            f"Consider rescheduling one or making '{title_b}' shorter."
        )


class CalendarEmailOrchestrator:
    """
    Unified orchestrator for calendar and email operations.

    Wraps raw tools with intelligence:
    - Email triage and draft replies
    - Calendar conflict detection
    - HITL gates for write operations
    """

    def __init__(self, whitelisted_senders: list[str] | None = None):
        self.email_triage = EmailTriage(whitelisted_senders)
        self.calendar = CalendarOrchestrator()
        self._pending_drafts: list[EmailDraft] = []

    def triage_emails(self, messages: list[dict]) -> dict[str, list[TriageResult]]:
        """Triage a batch of emails by priority."""
        return self.email_triage.triage_batch(messages)

    def draft_reply(
        self, to: str, subject: str, context: str, tone: str = "professional"
    ) -> EmailDraft:
        """
        Generate a draft email reply.

        Args:
            to: Recipient email
            subject: Original subject (will be prefixed with Re:)
            context: Context about what the reply should contain
            tone: Email tone (professional, casual, friendly)

        Returns:
            EmailDraft that needs user approval before sending
        """
        # Simple template-based draft generation
        tone_prefix = {
            "professional": "Hello,\n\nThank you for your email.",
            "casual": "Hi there,\n\nThanks for reaching out!",
            "friendly": "Hey!\n\nGreat to hear from you.",
        }

        greeting = tone_prefix.get(tone, tone_prefix["professional"])
        body = f"{greeting}\n\n{context}\n\nBest regards"

        draft = EmailDraft(
            to=to,
            subject=f"Re: {subject}" if not subject.startswith("Re:") else subject,
            body=body,
            priority=EmailPriority.NORMAL,
        )

        self._pending_drafts.append(draft)
        return draft

    def get_pending_drafts(self) -> list[EmailDraft]:
        """Get drafts awaiting user approval."""
        return list(self._pending_drafts)

    def approve_draft(self, index: int) -> EmailDraft | None:
        """Approve and remove a draft by index."""
        if 0 <= index < len(self._pending_drafts):
            return self._pending_drafts.pop(index)
        return None

    def cancel_draft(self, index: int) -> bool:
        """Cancel a draft by index."""
        if 0 <= index < len(self._pending_drafts):
            self._pending_drafts.pop(index)
            return True
        return False

    def check_calendar_conflicts(
        self, events: list[dict], new_event: dict | None = None
    ) -> list[CalendarConflict]:
        """Check for calendar conflicts."""
        return self.calendar.detect_conflicts(events, new_event)

    def suggest_meeting_times(
        self,
        existing_events: list[dict],
        duration_minutes: int = 60,
    ) -> list[dict]:
        """Suggest available meeting times."""
        return self.calendar.suggest_meeting_times(existing_events, duration_minutes)


__all__ = [
    "EmailTriage",
    "CalendarOrchestrator",
    "CalendarEmailOrchestrator",
    "EmailDraft",
    "CalendarConflict",
    "TriageResult",
    "EmailPriority",
]
