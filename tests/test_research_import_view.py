"""Unit tests for research import view."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from textual.widgets import DataTable, TextArea

from app.tui.views.research import ResearchImportModal


@pytest.fixture
def temp_db_path(tmp_path):
    """Create a temporary database path."""
    return tmp_path / "test_research.db"


@pytest.mark.asyncio
async def test_research_import_modal_init(temp_db_path):
    """Test ResearchImportModal initialization."""
    modal = ResearchImportModal(workstream="test", db_path=temp_db_path)
    assert modal.workstream == "test"
    assert modal.db_path == temp_db_path
    assert modal.status_message == ""
    assert modal.findings == []


def test_research_import_modal_compose():
    """Test ResearchImportModal UI composition returns widgets."""
    modal = ResearchImportModal()

    # We can't actually call compose() without an app context,
    # but we can verify the modal has the expected attributes
    assert hasattr(modal, "workstream")
    assert hasattr(modal, "db_path")
    assert hasattr(modal, "compose")
    assert modal.workstream == "research"  # default value


@pytest.mark.asyncio
async def test_handle_import_empty_content(temp_db_path):
    """Test handling import with empty content."""
    modal = ResearchImportModal(db_path=temp_db_path)

    # Mock the query_one method to return mock widgets
    text_area_mock = MagicMock(spec=TextArea)
    text_area_mock.text = ""

    modal.query_one = MagicMock(side_effect=lambda _selector, _widget_type: text_area_mock)
    modal.update_status = MagicMock()

    await modal.handle_import()

    modal.update_status.assert_called_with("No content to import", is_error=True)


@pytest.mark.asyncio
async def test_handle_import_valid_markdown(temp_db_path):
    """Test importing valid markdown content."""
    modal = ResearchImportModal(workstream="test", db_path=temp_db_path)

    # Mock widgets
    text_area_mock = MagicMock(spec=TextArea)
    text_area_mock.text = "- Test claim | Test evidence | https://example.com | 0.8 | tag1,tag2"

    modal.query_one = MagicMock(side_effect=lambda _selector, _widget_type: text_area_mock)
    modal.update_status = MagicMock()
    modal.refresh_table = AsyncMock()

    # Ensure the database is initialized first
    from app.research.db import ResearchDB

    async with ResearchDB(temp_db_path):
        pass  # Just initialize the DB

    await modal.handle_import()

    # Verify text area was cleared
    assert text_area_mock.text == ""

    # Verify status was updated
    modal.update_status.assert_called()
    status_call = modal.update_status.call_args[0][0]
    assert "Import complete" in status_call
    assert "1 added" in status_call

    # Verify table refresh was called
    modal.refresh_table.assert_called_once()


@pytest.mark.asyncio
async def test_handle_import_duplicate_detection(temp_db_path):
    """Test duplicate detection during import."""
    from app.research.db import ResearchDB

    # Pre-populate database with a finding
    async with ResearchDB(temp_db_path) as db:
        await db.insert_finding(
            url="https://example.com",
            source_type="web",
            claim="Test claim",
            evidence="Test evidence",
            confidence=0.7,
            tags=["existing"],
            workstream="test",
        )

    modal = ResearchImportModal(workstream="test", db_path=temp_db_path)

    # Mock widgets - same claim and URL as existing
    text_area_mock = MagicMock(spec=TextArea)
    text_area_mock.text = "- Test claim | Different evidence | https://example.com | 0.9 | new"

    modal.query_one = MagicMock(side_effect=lambda _selector, _widget_type: text_area_mock)
    modal.update_status = MagicMock()
    modal.refresh_table = AsyncMock()

    await modal.handle_import()

    # Verify status shows skipped duplicate
    modal.update_status.assert_called()
    status_call = modal.update_status.call_args[0][0]
    assert "0 added" in status_call
    assert "1 skipped" in status_call


@pytest.mark.asyncio
async def test_handle_import_json_format(temp_db_path):
    """Test importing JSON format content."""
    modal = ResearchImportModal(workstream="test", db_path=temp_db_path)

    json_content = """[
        {
            "claim": "JSON test claim",
            "evidence": "JSON test evidence",
            "url": "https://json.example.com",
            "confidence": 0.95,
            "tags": ["json", "test"]
        }
    ]"""

    # Mock widgets
    text_area_mock = MagicMock(spec=TextArea)
    text_area_mock.text = json_content

    modal.query_one = MagicMock(side_effect=lambda _selector, _widget_type: text_area_mock)
    modal.update_status = MagicMock()
    modal.refresh_table = AsyncMock()

    # Initialize database
    from app.research.db import ResearchDB

    async with ResearchDB(temp_db_path):
        pass

    await modal.handle_import()

    # Verify import succeeded
    modal.update_status.assert_called()
    status_call = modal.update_status.call_args[0][0]
    assert "Import complete" in status_call
    assert "1 added" in status_call


@pytest.mark.asyncio
async def test_handle_import_invalid_content(temp_db_path):
    """Test handling invalid content that can't be parsed."""
    modal = ResearchImportModal(workstream="test", db_path=temp_db_path)

    # Mock widgets with unparseable content
    text_area_mock = MagicMock(spec=TextArea)
    text_area_mock.text = "This is not valid markdown or JSON for findings"

    modal.query_one = MagicMock(side_effect=lambda _selector, _widget_type: text_area_mock)
    modal.update_status = MagicMock()

    await modal.handle_import()

    # Verify error status
    modal.update_status.assert_called_with(
        "No valid findings found in pasted content", is_error=True
    )


@pytest.mark.asyncio
async def test_refresh_table_with_findings(temp_db_path):
    """Test refreshing table with existing findings."""
    from app.research.db import ResearchDB

    # Pre-populate database
    async with ResearchDB(temp_db_path) as db:
        await db.insert_finding(
            url="https://example1.com",
            source_type="web",
            claim="First claim that is very long and should be truncated when displayed",
            evidence="Evidence 1",
            confidence=0.8,
            tags=["tag1", "tag2", "tag3"],
            workstream="research",
        )
        await db.insert_finding(
            url="https://example2.com/very/long/url/that/should/be/truncated",
            source_type="paper",
            claim="Second claim",
            evidence="Evidence 2",
            confidence=0.95,
            tags=[],
            workstream="analysis",
        )

    modal = ResearchImportModal(workstream="test", db_path=temp_db_path)

    # Mock DataTable
    table_mock = MagicMock(spec=DataTable)
    table_mock.clear = MagicMock()
    table_mock.add_row = MagicMock()

    modal.query_one = MagicMock(return_value=table_mock)

    await modal.refresh_table()

    # Verify table was cleared and rows were added
    table_mock.clear.assert_called_once()
    assert table_mock.add_row.call_count == 2

    # The rows are ordered by retrieved_at DESC, so second finding comes first
    # Check truncation - at least one of the rows should have truncation
    all_claims = [call[0][0] for call in table_mock.add_row.call_args_list]
    all_urls = [call[0][1] for call in table_mock.add_row.call_args_list]

    # Check that long values were truncated
    has_truncated_claim = any("..." in claim for claim in all_claims)
    has_truncated_url = any("..." in url for url in all_urls)

    # At least one should be truncated (the long claim or long URL)
    assert has_truncated_claim or has_truncated_url, "Expected truncation in claims or URLs"


@pytest.mark.asyncio
async def test_refresh_table_empty_database(temp_db_path):
    """Test refreshing table when database is empty."""
    modal = ResearchImportModal(workstream="test", db_path=temp_db_path)

    # Mock DataTable
    table_mock = MagicMock(spec=DataTable)
    table_mock.clear = MagicMock()
    table_mock.add_row = MagicMock()

    modal.query_one = MagicMock(return_value=table_mock)

    await modal.refresh_table()

    # Verify table was cleared but no rows added
    table_mock.clear.assert_called_once()
    table_mock.add_row.assert_not_called()


def test_update_status_normal_message():
    """Test updating status with normal message."""
    modal = ResearchImportModal()

    # Mock Static widget
    status_widget_mock = MagicMock()
    modal.query_one = MagicMock(return_value=status_widget_mock)

    modal.update_status("Test success message")

    status_widget_mock.update.assert_called_with("[green]Test success message[/green]")


def test_update_status_error_message():
    """Test updating status with error message."""
    modal = ResearchImportModal()

    # Mock Static widget
    status_widget_mock = MagicMock()
    modal.query_one = MagicMock(return_value=status_widget_mock)

    modal.update_status("Test error message", is_error=True)

    status_widget_mock.update.assert_called_with("[red]Test error message[/red]")


def test_handle_close():
    """Test handle_close dismisses the modal."""
    modal = ResearchImportModal()
    modal.dismiss = MagicMock()

    modal.handle_close()

    modal.dismiss.assert_called_with(True)


def test_action_close():
    """Test action_close (escape key) dismisses the modal."""
    modal = ResearchImportModal()
    modal.dismiss = MagicMock()

    modal.action_close()

    modal.dismiss.assert_called_with(True)
