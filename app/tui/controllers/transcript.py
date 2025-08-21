"""Transcript data structures for conversation tracking."""

from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TranscriptRole(Enum):
    """Role identifiers for transcript entries."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass(frozen=True)
class TranscriptEntry:
    """Immutable transcript entry representing a single conversation turn.

    Attributes:
        role: The role of the speaker (user, assistant, or system)
        content: The actual message content
        timestamp: When this entry was created
        metadata: Optional additional data (e.g., error info, token counts)
    """

    role: TranscriptRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert entry to dictionary for serialization."""
        data: dict[str, Any] = {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
        }
        if self.metadata:
            data["metadata"] = self.metadata
        return data

    def to_string(self) -> str:
        """Convert to simple string format for backward compatibility."""
        role_prefix = {
            TranscriptRole.USER: "User",
            TranscriptRole.ASSISTANT: "Assistant",
            TranscriptRole.SYSTEM: "System",
        }
        prefix = role_prefix.get(self.role, self.role.value.title())

        # Special formatting for specific content types
        if self.role == TranscriptRole.USER and "Braindump" in self.content:
            return f"User Braindump: {self.content.replace('Braindump: ', '')}"
        elif self.role == TranscriptRole.USER and "Feedback" in self.content:
            return f"User Feedback: {self.content.replace('Feedback: ', '')}"
        elif self.role == TranscriptRole.USER and "Answers" in self.content:
            return f"User Answers: {self.content.replace('Answers: ', '')}"
        elif self.role == TranscriptRole.ASSISTANT and "Summary" in self.content:
            if "Refined" in self.content:
                return f"Assistant Refined Summary: {self.content.replace('Refined Summary: ', '')}"
            return f"Assistant Summary: {self.content.replace('Summary: ', '')}"
        elif self.role == TranscriptRole.ASSISTANT and "Questions" in self.content:
            return f"Assistant Questions: {self.content.replace('Questions: ', '')}"

        return f"{prefix}: {self.content}"


class Transcript:
    """Manages conversation transcript with structured entries.

    This class provides both structured access to transcript entries
    and backward-compatible string representations.
    """

    def __init__(self) -> None:
        """Initialize an empty transcript."""
        self._entries: list[TranscriptEntry] = []

    def add_entry(
        self,
        role: TranscriptRole,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a new entry to the transcript.

        Args:
            role: The role of the speaker
            content: The message content
            metadata: Optional metadata for this entry
        """
        entry = TranscriptEntry(
            role=role,
            content=content,
            metadata=metadata,
        )
        self._entries.append(entry)

    def add_user(self, content: str, metadata: dict[str, Any] | None = None) -> None:
        """Convenience method to add a user entry."""
        self.add_entry(TranscriptRole.USER, content, metadata)

    def add_assistant(self, content: str, metadata: dict[str, Any] | None = None) -> None:
        """Convenience method to add an assistant entry."""
        self.add_entry(TranscriptRole.ASSISTANT, content, metadata)

    def add_system(self, content: str, metadata: dict[str, Any] | None = None) -> None:
        """Convenience method to add a system entry."""
        self.add_entry(TranscriptRole.SYSTEM, content, metadata)

    def clear(self) -> None:
        """Clear all entries from the transcript."""
        self._entries.clear()

    def to_string_list(self) -> list[str]:
        """Convert to list of strings for backward compatibility with LLMService."""
        return [entry.to_string() for entry in self._entries]

    def to_dict(self) -> list[dict[str, Any]]:
        """Convert all entries to dictionaries for serialization."""
        return [entry.to_dict() for entry in self._entries]

    def get_entries(self) -> list[TranscriptEntry]:
        """Get a copy of all entries."""
        return list(self._entries)

    def get_last_entry(self) -> TranscriptEntry | None:
        """Get the most recent entry, or None if empty."""
        return self._entries[-1] if self._entries else None

    def __len__(self) -> int:
        """Return the number of entries in the transcript."""
        return len(self._entries)

    def __bool__(self) -> bool:
        """Return True if transcript has entries."""
        return bool(self._entries)

    def __iter__(self) -> Iterator[TranscriptEntry]:
        """Iterate over entries."""
        return iter(self._entries)
