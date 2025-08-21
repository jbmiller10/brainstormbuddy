"""Tests for onboarding logger."""

import json
import os
import tempfile
from datetime import date
from pathlib import Path

from app.tui.controllers.onboarding_logger import OnboardingLogger


class TestOnboardingLogger:
    """Test onboarding logger functionality."""

    def test_create_logger(self) -> None:
        """Test creating a logger instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = OnboardingLogger(tmpdir)
            assert logger.log_dir == Path(tmpdir)
            assert logger.log_file.parent == Path(tmpdir)
            assert logger.log_file.name == f"onboarding_{date.today().strftime('%Y-%m-%d')}.jsonl"

    def test_verbose_mode(self) -> None:
        """Test verbose mode detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Default mode
            logger = OnboardingLogger(tmpdir)
            assert logger.verbose is False

            # Verbose mode
            os.environ["LOG_ONBOARDING_VERBOSE"] = "1"
            logger_verbose = OnboardingLogger(tmpdir)
            assert logger_verbose.verbose is True

            # Cleanup
            del os.environ["LOG_ONBOARDING_VERBOSE"]

    def test_log_event(self) -> None:
        """Test logging a basic event."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = OnboardingLogger(tmpdir)

            logger.log_event(
                event="onboarding_started",
                project_slug="test-project",
                data={"step": "initial"},
            )

            # Read log file
            with open(logger.log_file, encoding="utf-8") as f:
                lines = f.readlines()

            assert len(lines) == 1
            entry = json.loads(lines[0])
            assert entry["event"] == "onboarding_started"
            assert entry["project_slug"] == "test-project"
            assert entry["data"]["step"] == "initial"
            assert "timestamp" in entry

    def test_content_redaction_default(self) -> None:
        """Test that content is redacted by default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = OnboardingLogger(tmpdir)

            logger.log_onboarding_started("test-project", "My Project Name")

            entries = logger.read_log()
            assert len(entries) == 1

            # Check redaction
            project_name_data = entries[0]["data"]["project_name"]
            assert "content_hash" in project_name_data
            assert "content_length" in project_name_data
            assert "content" not in project_name_data
            assert project_name_data["content_length"] == len("My Project Name")

    def test_content_verbose_mode(self) -> None:
        """Test that content is included in verbose mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["LOG_ONBOARDING_VERBOSE"] = "1"
            logger = OnboardingLogger(tmpdir)

            logger.log_onboarding_started("test-project", "My Project Name")

            entries = logger.read_log()
            assert len(entries) == 1

            # Check full content is present
            project_name_data = entries[0]["data"]["project_name"]
            assert "content" in project_name_data
            assert project_name_data["content"] == "My Project Name"
            assert "content_hash" not in project_name_data
            assert project_name_data["content_length"] == len("My Project Name")

            # Cleanup
            del os.environ["LOG_ONBOARDING_VERBOSE"]

    def test_log_clarify_questions(self) -> None:
        """Test logging clarify questions event."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = OnboardingLogger(tmpdir)

            questions = ["1. What is the purpose?", "2. Who are the users?"]
            braindump = "I want to build an app"

            logger.log_clarify_questions_shown("test-project", questions, braindump)

            entries = logger.read_log()
            assert len(entries) == 1
            assert entries[0]["event"] == "clarify_questions_shown"
            assert entries[0]["data"]["question_count"] == 2
            assert "braindump" in entries[0]["data"]
            # Questions should not be included in non-verbose mode
            assert "questions" not in entries[0]["data"]

    def test_log_clarify_questions_verbose(self) -> None:
        """Test logging clarify questions in verbose mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["LOG_ONBOARDING_VERBOSE"] = "1"
            logger = OnboardingLogger(tmpdir)

            questions = ["1. What is the purpose?", "2. Who are the users?"]
            braindump = "I want to build an app"

            logger.log_clarify_questions_shown("test-project", questions, braindump)

            entries = logger.read_log()
            assert len(entries) == 1
            assert entries[0]["data"]["questions"] == questions
            assert entries[0]["data"]["braindump"]["content"] == braindump

            # Cleanup
            del os.environ["LOG_ONBOARDING_VERBOSE"]

    def test_log_kernel_generated(self) -> None:
        """Test logging kernel generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = OnboardingLogger(tmpdir)

            kernel_content = """# Kernel

## Core Concept
Test concept.

## Key Questions
1. Question?

## Success Criteria
- Criteria

## Constraints
- Constraint

## Primary Value Proposition
Value."""

            logger.log_kernel_generated("test-project", kernel_content)

            entries = logger.read_log()
            assert len(entries) == 1
            assert entries[0]["event"] == "kernel_generated"
            assert entries[0]["data"]["valid_structure"] is True
            assert "kernel" in entries[0]["data"]
            # Content should be redacted
            assert "content_hash" in entries[0]["data"]["kernel"]

    def test_log_proposal_decision(self) -> None:
        """Test logging proposal approval/rejection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = OnboardingLogger(tmpdir)

            # Test approval
            logger.log_proposal_decision("test-project", approved=True, kernel_content="kernel")

            # Test rejection
            logger.log_proposal_decision("test-project", approved=False)

            entries = logger.read_log()
            assert len(entries) == 2
            assert entries[0]["event"] == "proposal_approved"
            assert entries[0]["data"]["approved"] is True
            assert entries[1]["event"] == "proposal_rejected"
            assert entries[1]["data"]["approved"] is False

    def test_log_project_scaffolded(self) -> None:
        """Test logging project scaffolding."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = OnboardingLogger(tmpdir)

            project_path = Path("/projects/test-project")
            logger.log_project_scaffolded("test-project", project_path)

            entries = logger.read_log()
            assert len(entries) == 1
            assert entries[0]["event"] == "project_scaffolded"
            assert entries[0]["data"]["project_path"] == str(project_path)

    def test_log_error(self) -> None:
        """Test logging errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = OnboardingLogger(tmpdir)

            logger.log_error(
                "test-project",
                error_code="kernel_generation_failed",
                last_successful_step="answers",
                details="Connection timeout",
            )

            entries = logger.read_log()
            assert len(entries) == 1
            assert entries[0]["event"] == "error"
            assert entries[0]["data"]["error_code"] == "kernel_generation_failed"
            assert entries[0]["data"]["last_successful_step"] == "answers"
            # Details should be redacted in non-verbose mode
            assert entries[0]["data"]["details"]["redacted"] is True

    def test_log_answers_with_questions(self) -> None:
        """Test logging answers with question context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = OnboardingLogger(tmpdir)

            questions = ["1. What is the purpose?", "2. Who are the users?"]
            answers = "Purpose is X. Users are Y."

            logger.log_answers_collected("test-project", answers, questions)

            entries = logger.read_log()
            assert len(entries) == 1
            assert entries[0]["event"] == "answers_collected"
            assert entries[0]["data"]["question_count"] == 2
            # Questions should not be included in non-verbose mode
            assert "questions" not in entries[0]["data"]
            assert "answers" in entries[0]["data"]
            assert "content_hash" in entries[0]["data"]["answers"]

    def test_log_answers_with_questions_verbose(self) -> None:
        """Test logging answers with question context in verbose mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["LOG_ONBOARDING_VERBOSE"] = "1"
            logger = OnboardingLogger(tmpdir)

            questions = ["1. What is the purpose?", "2. Who are the users?"]
            answers = "Purpose is X. Users are Y."

            logger.log_answers_collected("test-project", answers, questions)

            entries = logger.read_log()
            assert len(entries) == 1
            assert entries[0]["data"]["question_count"] == 2
            assert entries[0]["data"]["questions"] == questions
            assert entries[0]["data"]["answers"]["content"] == answers

            # Cleanup
            del os.environ["LOG_ONBOARDING_VERBOSE"]

    def test_log_error_verbose(self) -> None:
        """Test logging errors in verbose mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["LOG_ONBOARDING_VERBOSE"] = "1"
            logger = OnboardingLogger(tmpdir)

            logger.log_error(
                "test-project",
                error_code="kernel_generation_failed",
                last_successful_step="answers",
                details="Connection timeout",
            )

            entries = logger.read_log()
            assert len(entries) == 1
            assert "content" in entries[0]["data"]["details"]
            assert entries[0]["data"]["details"]["content"] == "Connection timeout"

            # Cleanup
            del os.environ["LOG_ONBOARDING_VERBOSE"]

    def test_daily_log_file(self) -> None:
        """Test that log files are created daily."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger1 = OnboardingLogger(tmpdir)
            logger2 = OnboardingLogger(tmpdir)

            # Both loggers should use the same daily file
            assert logger1.log_file == logger2.log_file

            logger1.log_event("event1", "project1")
            logger2.log_event("event2", "project2")

            entries = logger1.read_log()
            assert len(entries) == 2
            assert entries[0]["event"] == "event1"
            assert entries[1]["event"] == "event2"

    def test_concurrent_logging(self) -> None:
        """Test that concurrent log writes don't corrupt the file."""
        import threading

        with tempfile.TemporaryDirectory() as tmpdir:
            logger = OnboardingLogger(tmpdir)

            # Create multiple concurrent log threads
            threads = []
            for i in range(10):
                thread = threading.Thread(
                    target=logger.log_event,
                    args=(f"event_{i}", f"project_{i}"),
                    kwargs={"data": {"index": i}},
                )
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            entries = logger.read_log()
            assert len(entries) == 10

            # Check all entries are valid
            indices = [e["data"]["index"] for e in entries]
            assert sorted(indices) == list(range(10))

    def test_validate_kernel_structure(self) -> None:
        """Test kernel structure validation."""
        logger = OnboardingLogger()

        # Valid structure
        valid_kernel = """# Kernel

## Core Concept
Concept.

## Key Questions
Questions.

## Success Criteria
Criteria.

## Constraints
Constraints.

## Primary Value Proposition
Value."""

        assert logger._validate_kernel_structure(valid_kernel) is True

        # Missing section
        invalid_kernel = """# Kernel

## Core Concept
Concept.

## Key Questions
Questions.

## Success Criteria
Criteria.

## Primary Value Proposition
Value."""

        assert logger._validate_kernel_structure(invalid_kernel) is False
