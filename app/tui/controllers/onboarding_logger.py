"""Logging utilities for onboarding operations with privacy-by-default."""

import contextlib
import fcntl
import hashlib
import json
import os
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any


class OnboardingLogger:
    """Logger for onboarding milestones with privacy protection."""

    def __init__(self, log_dir: Path | str = "logs") -> None:
        """
        Initialize onboarding logger.

        Args:
            log_dir: Directory for log files
        """
        self.log_dir = Path(log_dir) if isinstance(log_dir, str) else log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create daily log file
        today = date.today()
        self.log_file = self.log_dir / f"onboarding_{today.strftime('%Y-%m-%d')}.jsonl"

        # Check for verbose mode
        self.verbose = os.environ.get("LOG_ONBOARDING_VERBOSE", "").strip() == "1"

    def _redact_content(self, content: str | None) -> dict[str, Any]:
        """
        Redact user content for privacy.

        Args:
            content: User content to redact

        Returns:
            Dictionary with redacted content info
        """
        if content is None:
            return {}

        result: dict[str, Any] = {}

        # Always include length
        result["content_length"] = len(content)

        if self.verbose:
            # In verbose mode, include full content
            result["content"] = content
        else:
            # In privacy mode, only include hash
            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            result["content_hash"] = content_hash

        return result

    def log_event(
        self,
        event: str,
        project_slug: str,
        data: dict[str, Any] | None = None,
        *,
        redact_fields: list[str] | None = None,
    ) -> None:
        """
        Log an onboarding event with privacy protection.

        Args:
            event: Event type (e.g., "onboarding_started", "kernel_generated")
            project_slug: Project slug for context
            data: Optional event data
            redact_fields: List of field names in data to redact
        """
        log_entry = {
            "event": event,
            "timestamp": datetime.now(UTC).isoformat(),
            "project_slug": project_slug,
            "data": {},
        }

        if data:
            # Process data with redaction
            processed_data = {}
            redact_fields = redact_fields or []

            for key, value in data.items():
                if key in redact_fields and isinstance(value, str):
                    # Redact sensitive fields
                    processed_data[key] = self._redact_content(value)
                else:
                    # Keep non-sensitive data as-is
                    processed_data[key] = value

            log_entry["data"] = processed_data

        # Append to log file with exclusive lock for atomicity
        with open(self.log_file, "a", encoding="utf-8") as f:
            # Acquire exclusive lock to prevent concurrent writes
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                f.write(json.dumps(log_entry) + "\n")
                f.flush()  # Ensure data is written to disk
            finally:
                # Release lock
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def log_onboarding_started(self, project_slug: str, project_name: str) -> None:
        """Log onboarding start event."""
        self.log_event(
            event="onboarding_started",
            project_slug=project_slug,
            data={"project_name": self._redact_content(project_name)},
            redact_fields=[],
        )

    def log_clarify_questions_shown(
        self, project_slug: str, questions: list[str], braindump: str
    ) -> None:
        """Log clarifying questions shown event."""
        data = {
            "question_count": len(questions),
            "braindump": self._redact_content(braindump),
        }

        if self.verbose:
            data["questions"] = questions

        self.log_event(
            event="clarify_questions_shown",
            project_slug=project_slug,
            data=data,
        )

    def log_answers_collected(
        self, project_slug: str, answers: str, questions: list[str] | None = None
    ) -> None:
        """Log answers collected event with optional question context."""
        data: dict[str, Any] = {"answers": self._redact_content(answers)}

        # Include question context for correlation
        if questions:
            data["question_count"] = len(questions)
            if self.verbose:
                data["questions"] = questions

        self.log_event(
            event="answers_collected",
            project_slug=project_slug,
            data=data,
        )

    def log_kernel_generated(self, project_slug: str, kernel_content: str) -> None:
        """Log kernel generation event."""
        self.log_event(
            event="kernel_generated",
            project_slug=project_slug,
            data={
                "kernel": self._redact_content(kernel_content),
                "valid_structure": self._validate_kernel_structure(kernel_content),
            },
        )

    def log_proposal_decision(
        self, project_slug: str, approved: bool, kernel_content: str | None = None
    ) -> None:
        """Log kernel proposal approval/rejection."""
        event = "proposal_approved" if approved else "proposal_rejected"
        data: dict[str, Any] = {"approved": approved}

        if kernel_content:
            data["kernel"] = self._redact_content(kernel_content)

        self.log_event(
            event=event,
            project_slug=project_slug,
            data=data,
        )

    def log_project_scaffolded(self, project_slug: str, project_path: Path) -> None:
        """Log project scaffolding completion."""
        self.log_event(
            event="project_scaffolded",
            project_slug=project_slug,
            data={"project_path": str(project_path)},
        )

    def log_error(
        self,
        project_slug: str,
        error_code: str,
        last_successful_step: str,
        details: str | None = None,
    ) -> None:
        """Log an error during onboarding."""
        data: dict[str, Any] = {
            "error_code": error_code,
            "last_successful_step": last_successful_step,
        }

        if details:
            data["details"] = self._redact_content(details) if self.verbose else {"redacted": True}

        self.log_event(
            event="error",
            project_slug=project_slug,
            data=data,
        )

    def _validate_kernel_structure(self, kernel_content: str) -> bool:
        """
        Check if kernel has valid structure.

        Args:
            kernel_content: Kernel markdown content

        Returns:
            True if structure is valid
        """
        required_sections = [
            "## Core Concept",
            "## Key Questions",
            "## Success Criteria",
            "## Constraints",
            "## Primary Value Proposition",
        ]

        return all(section in kernel_content for section in required_sections)

    def get_log_path(self) -> Path:
        """Get the path to the current log file."""
        return self.log_file

    def read_log(self) -> list[dict[str, Any]]:
        """
        Read all log entries from the current log file.

        Returns:
            List of log entries
        """
        if not self.log_file.exists():
            return []

        entries = []
        with open(self.log_file, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    with contextlib.suppress(json.JSONDecodeError):
                        entries.append(json.loads(line))

        return entries
