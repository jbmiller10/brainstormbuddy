"""Logging utilities for synthesis operations."""

import contextlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class SynthesisLogger:
    """Logger for synthesis and critic operations."""

    def __init__(self, log_dir: Path | str = "logs") -> None:
        """
        Initialize logger.

        Args:
            log_dir: Directory for log files
        """
        self.log_dir = Path(log_dir) if isinstance(log_dir, str) else log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create log file with timestamp
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"run-{timestamp}.jsonl"

    async def log_event(
        self,
        stage: str,
        event: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        """
        Log an event to the JSON Lines log file.

        Args:
            stage: Stage name (synthesis, critic)
            event: Event type (start, complete, error, etc.)
            data: Optional event data
        """
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "stage": stage,
            "event": event,
            "data": data or {},
        }

        # Append to log file
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")

    async def log_decision(
        self,
        stage: str,
        decision: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Log a decision made during synthesis.

        Args:
            stage: Stage name
            decision: Decision type (applied_as_is, applied_with_autofix, canceled)
            details: Optional decision details
        """
        await self.log_event(
            stage=stage,
            event="decision",
            data={"decision": decision, "details": details or {}},
        )

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

    def get_summary(self) -> dict[str, Any]:
        """
        Get a summary of the current log.

        Returns:
            Summary statistics
        """
        entries = self.read_log()

        summary: dict[str, Any] = {
            "total_events": len(entries),
            "stages": {},
            "decisions": [],
            "errors": [],
        }

        for entry in entries:
            stage = entry.get("stage", "unknown")
            event = entry.get("event", "unknown")

            # Count by stage
            if stage not in summary["stages"]:
                summary["stages"][stage] = {"events": 0, "types": {}}

            summary["stages"][stage]["events"] += 1

            if event not in summary["stages"][stage]["types"]:
                summary["stages"][stage]["types"][event] = 0
            summary["stages"][stage]["types"][event] += 1

            # Collect decisions
            if event == "decision":
                summary["decisions"].append(entry.get("data", {}))

            # Collect errors
            if event == "error":
                summary["errors"].append(entry.get("data", {}))

        return summary
