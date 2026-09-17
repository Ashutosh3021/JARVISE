"""
JARVIS Brain Layer - Proactive Suggestions Module

Detects patterns in user interactions and suggests follow-up actions.
Tracks command sequences, learns from corrections, and provides
context-aware suggestions based on time, frequency, and recent activity.
"""

import json
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loguru import logger


@dataclass
class Interaction:
    """A single user interaction record."""
    user_input: str
    tools_used: list[str]
    timestamp: float
    session_id: str = "default"

    def to_dict(self) -> dict:
        return {
            "user_input": self.user_input,
            "tools_used": self.tools_used,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Interaction":
        return cls(
            user_input=data["user_input"],
            tools_used=data.get("tools_used", []),
            timestamp=data["timestamp"],
            session_id=data.get("session_id", "default"),
        )


@dataclass
class Suggestion:
    """A proactive suggestion for the user."""
    text: str
    reason: str
    confidence: float  # 0.0 - 1.0
    source: str  # "pattern", "frequency", "time", "followup"

    def __str__(self) -> str:
        return f"[{self.source}] {self.text} (confidence: {self.confidence:.0%})"


class ProactiveEngine:
    """
    Detects patterns in user interactions and generates proactive suggestions.

    Tracks:
    - Command sequences (what follows what)
    - Frequency patterns (what the user does most)
    - Time-based patterns (what the user does at certain times)
    - Tool usage patterns (which tools are commonly used together)
    """

    def __init__(self, storage_path: str = "./data/proactive.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        self._interactions: list[Interaction] = []
        self._sequence_counts: dict[tuple[str, str], int] = defaultdict(int)
        self._tool_sequences: dict[tuple[str, str], int] = defaultdict(int)
        self._command_frequency: Counter = Counter()
        self._tool_frequency: Counter = Counter()
        self._time_patterns: dict[str, Counter] = defaultdict(Counter)

        self._load()

    def _load(self) -> None:
        if not self.storage_path.exists():
            return
        try:
            data = json.loads(self.storage_path.read_text(encoding="utf-8"))
            for item in data.get("interactions", []):
                self._interactions.append(Interaction.from_dict(item))
            for seq, count in data.get("sequence_counts", {}).items():
                parts = tuple(seq.split("||"))
                if len(parts) == 2:
                    self._sequence_counts[parts] = count
            for seq, count in data.get("tool_sequences", {}).items():
                parts = tuple(seq.split("||"))
                if len(parts) == 2:
                    self._tool_sequences[parts] = count
            self._command_frequency = Counter(data.get("command_frequency", {}))
            self._tool_frequency = Counter(data.get("tool_frequency", {}))
            for hour, freq in data.get("time_patterns", {}).items():
                self._time_patterns[hour] = Counter(freq)
            logger.debug(f"Loaded {len(self._interactions)} interactions")
        except Exception as e:
            logger.warning(f"Failed to load proactive data: {e}")

    def _save(self) -> None:
        try:
            data = {
                "interactions": [i.to_dict() for i in self._interactions[-500:]],
                "sequence_counts": {
                    f"{k[0]}||{k[1]}": v
                    for k, v in self._sequence_counts.items()
                },
                "tool_sequences": {
                    f"{k[0]}||{k[1]}": v
                    for k, v in self._tool_sequences.items()
                },
                "command_frequency": dict(self._command_frequency),
                "tool_frequency": dict(self._tool_frequency),
                "time_patterns": {
                    h: dict(freq) for h, freq in self._time_patterns.items()
                },
            }
            self.storage_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error(f"Failed to save proactive data: {e}")

    def record_interaction(
        self,
        user_input: str,
        tools_used: list[str] | None = None,
        session_id: str = "default",
    ) -> None:
        """Record a user interaction for pattern learning."""
        interaction = Interaction(
            user_input=user_input,
            tools_used=tools_used or [],
            timestamp=time.time(),
            session_id=session_id,
        )
        self._interactions.append(interaction)

        # Update sequence counts (bigram)
        normalized = self._normalize(user_input)
        self._command_frequency[normalized] += 1

        if len(self._interactions) >= 2:
            prev = self._normalize(self._interactions[-2].user_input)
            self._sequence_counts[(prev, normalized)] += 1

        # Update tool frequency and sequences
        for tool in tools_used:
            self._tool_frequency[tool] += 1

        if tools_used and len(self._interactions) >= 2:
            prev_tools = self._interactions[-2].tools_used
            for pt in prev_tools:
                for t in tools_used:
                    self._tool_sequences[(pt, t)] += 1

        # Time pattern (hour bucket)
        hour = str(datetime.now().hour)
        self._time_patterns[hour][normalized] += 1

        self._save()

    def suggest(self, last_input: str = "", tools_used: list[str] | None = None) -> list[Suggestion]:
        """
        Generate proactive suggestions based on recent activity.

        Args:
            last_input: The most recent user input
            tools_used: Tools used in the last interaction

        Returns:
            List of suggestions sorted by confidence
        """
        suggestions: list[Suggestion] = []

        # 1. Follow-up suggestions based on command sequences
        if last_input:
            suggestions.extend(self._followup_suggestions(last_input))

        # 2. Tool-based follow-ups
        if tools_used:
            suggestions.extend(self._tool_followup_suggestions(tools_used))

        # 3. Frequency-based suggestions (common commands)
        suggestions.extend(self._frequency_suggestions(last_input))

        # 4. Time-based suggestions
        suggestions.extend(self._time_suggestions())

        # Deduplicate by text
        seen = set()
        unique = []
        for s in suggestions:
            if s.text not in seen:
                seen.add(s.text)
                unique.append(s)

        # Sort by confidence descending, return top 5
        unique.sort(key=lambda s: s.confidence, reverse=True)
        return unique[:5]

    def _normalize(self, text: str) -> str:
        """Normalize input for pattern matching."""
        return text.lower().strip()

    def _followup_suggestions(self, last_input: str) -> list[Suggestion]:
        """Suggest actions based on what typically follows the last input."""
        normalized = self._normalize(last_input)
        suggestions = []

        # Find sequences where this input was the first element
        followups: Counter = Counter()
        for (prev, nxt), count in self._sequence_counts.items():
            if prev == normalized:
                followups[nxt] = count

        if not followups:
            return suggestions

        total = sum(followups.values())
        for command, count in followups.most_common(3):
            confidence = min(count / max(total, 1), 0.9)
            if confidence >= 0.2:
                suggestions.append(Suggestion(
                    text=command,
                    reason=f"Often follows '{last_input[:40]}...' ({count}x)",
                    confidence=confidence,
                    source="followup",
                ))

        return suggestions

    def _tool_followup_suggestions(self, tools_used: list[str]) -> list[Suggestion]:
        """Suggest tools that commonly follow the tools just used."""
        suggestions = []

        for tool in tools_used:
            followups: Counter = Counter()
            for (prev, nxt), count in self._tool_sequences.items():
                if prev == tool:
                    followups[nxt] = count

            total = sum(followups.values())
            for next_tool, count in followups.most_common(2):
                confidence = min(count / max(total, 1), 0.85)
                if confidence >= 0.25:
                    suggestions.append(Suggestion(
                        text=f"Use {next_tool} next",
                        reason=f"Commonly follows {tool} ({count}x)",
                        confidence=confidence,
                        source="pattern",
                    ))

        return suggestions

    def _frequency_suggestions(self, last_input: str) -> list[Suggestion]:
        """Suggest the most frequently used commands."""
        suggestions = []
        normalized = self._normalize(last_input)

        for command, count in self._command_frequency.most_common(5):
            if command == normalized:
                continue
            # Higher frequency = higher confidence, capped
            confidence = min(count / 10, 0.7)
            if confidence >= 0.15:
                suggestions.append(Suggestion(
                    text=command,
                    reason=f"Frequently used ({count}x)",
                    confidence=confidence,
                    source="frequency",
                ))

        return suggestions

    def _time_suggestions(self) -> list[Suggestion]:
        """Suggest commands based on time of day patterns."""
        suggestions = []
        current_hour = str(datetime.now().hour)

        if current_hour not in self._time_patterns:
            return suggestions

        hour_freq = self._time_patterns[current_hour]
        total = sum(hour_freq.values())

        for command, count in hour_freq.most_common(3):
            confidence = min(count / max(total, 1), 0.6)
            if confidence >= 0.2:
                suggestions.append(Suggestion(
                    text=command,
                    reason=f"Usually done around this time ({count}x)",
                    confidence=confidence,
                    source="time",
                ))

        return suggestions

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about tracked patterns."""
        return {
            "total_interactions": len(self._interactions),
            "unique_commands": len(self._command_frequency),
            "unique_tools": len(self._tool_frequency),
            "sequence_patterns": len(self._sequence_counts),
            "tool_patterns": len(self._tool_sequences),
            "time_buckets": len(self._time_patterns),
        }

    def clear(self) -> None:
        """Clear all learned patterns."""
        self._interactions.clear()
        self._sequence_counts.clear()
        self._tool_sequences.clear()
        self._command_frequency.clear()
        self._tool_frequency.clear()
        self._time_patterns.clear()
        self._save()


__all__ = ["ProactiveEngine", "Suggestion", "Interaction"]
