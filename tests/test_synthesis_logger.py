"""Tests for synthesis logger."""

import json
import tempfile
from pathlib import Path

import pytest

from app.synthesis.logger import SynthesisLogger


class TestSynthesisLogger:
    """Test synthesis logger functionality."""

    @pytest.mark.asyncio
    async def test_create_logger(self) -> None:
        """Test creating a logger instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SynthesisLogger(tmpdir)
            assert logger.log_dir == Path(tmpdir)
            assert logger.log_file.parent == Path(tmpdir)
            assert logger.log_file.name.startswith("run-")
            assert logger.log_file.suffix == ".jsonl"

    @pytest.mark.asyncio
    async def test_log_event(self) -> None:
        """Test logging an event."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SynthesisLogger(tmpdir)

            await logger.log_event(
                stage="synthesis",
                event="start",
                data={"workstream": "ui-ux"},
            )

            # Read log file
            with open(logger.log_file, encoding="utf-8") as f:
                lines = f.readlines()

            assert len(lines) == 1
            entry = json.loads(lines[0])
            assert entry["stage"] == "synthesis"
            assert entry["event"] == "start"
            assert entry["data"]["workstream"] == "ui-ux"
            assert "timestamp" in entry

    @pytest.mark.asyncio
    async def test_log_multiple_events(self) -> None:
        """Test logging multiple events."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SynthesisLogger(tmpdir)

            await logger.log_event("synthesis", "start")
            await logger.log_event("synthesis", "findings_loaded", {"count": 10})
            await logger.log_event("synthesis", "complete")

            entries = logger.read_log()
            assert len(entries) == 3
            assert entries[0]["event"] == "start"
            assert entries[1]["event"] == "findings_loaded"
            assert entries[2]["event"] == "complete"

    @pytest.mark.asyncio
    async def test_log_decision(self) -> None:
        """Test logging a decision."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SynthesisLogger(tmpdir)

            await logger.log_decision(
                stage="synthesis",
                decision="applied_as_is",
                details={"workstream": "backend"},
            )

            entries = logger.read_log()
            assert len(entries) == 1
            assert entries[0]["stage"] == "synthesis"
            assert entries[0]["event"] == "decision"
            assert entries[0]["data"]["decision"] == "applied_as_is"
            assert entries[0]["data"]["details"]["workstream"] == "backend"

    def test_read_log_empty(self) -> None:
        """Test reading an empty log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SynthesisLogger(tmpdir)
            entries = logger.read_log()
            assert entries == []

    def test_read_log_with_invalid_lines(self) -> None:
        """Test reading a log with invalid JSON lines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SynthesisLogger(tmpdir)

            # Write valid and invalid lines
            with open(logger.log_file, "w", encoding="utf-8") as f:
                f.write('{"stage": "test", "event": "valid"}\n')
                f.write("invalid json\n")
                f.write('{"stage": "test", "event": "valid2"}\n')

            entries = logger.read_log()
            assert len(entries) == 2  # Only valid entries
            assert entries[0]["event"] == "valid"
            assert entries[1]["event"] == "valid2"

    @pytest.mark.asyncio
    async def test_get_summary(self) -> None:
        """Test getting log summary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SynthesisLogger(tmpdir)

            # Log various events
            await logger.log_event("synthesis", "start")
            await logger.log_event("synthesis", "complete")
            await logger.log_event("critic", "start")
            await logger.log_event("critic", "complete")
            await logger.log_decision("synthesis", "applied_as_is", {"workstream": "ui"})
            await logger.log_event("synthesis", "error", {"message": "Test error"})

            summary = logger.get_summary()

            assert summary["total_events"] == 6
            assert "synthesis" in summary["stages"]
            assert "critic" in summary["stages"]
            assert summary["stages"]["synthesis"]["events"] == 4
            assert summary["stages"]["critic"]["events"] == 2
            assert len(summary["decisions"]) == 1
            assert len(summary["errors"]) == 1

    def test_get_log_path(self) -> None:
        """Test getting the log file path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SynthesisLogger(tmpdir)
            path = logger.get_log_path()
            assert path == logger.log_file
            assert path.parent == Path(tmpdir)

    @pytest.mark.asyncio
    async def test_concurrent_logging(self) -> None:
        """Test that concurrent log writes don't corrupt the file."""
        import asyncio

        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SynthesisLogger(tmpdir)

            # Create multiple concurrent log tasks
            tasks = []
            for i in range(10):
                tasks.append(
                    logger.log_event(
                        stage=f"stage_{i}",
                        event="test",
                        data={"index": i},
                    )
                )

            await asyncio.gather(*tasks)

            entries = logger.read_log()
            assert len(entries) == 10

            # Check all entries are valid
            indices = [e["data"]["index"] for e in entries]
            assert sorted(indices) == list(range(10))
