"""Tests for findings table filters in research import view."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from textual.widgets import DataTable, Input

from app.research.db import ResearchDB
from app.tui.views.research import ResearchImportModal


@pytest.fixture
def populated_db(tmp_path: Path) -> Path:
    """Create a database with test findings."""
    import asyncio

    db_path = tmp_path / "test_research.db"

    async def setup_db() -> None:
        async with ResearchDB(db_path) as db:
            # Add diverse test findings
            await db.insert_finding(
                url="https://example.com/1",
                source_type="web",
                claim="Finding 1",
                evidence="Evidence 1",
                confidence=0.9,
                tags=["ai", "ml"],
                workstream="research",
            )
            await db.insert_finding(
                url="https://example.com/2",
                source_type="paper",
                claim="Finding 2",
                evidence="Evidence 2",
                confidence=0.7,
                tags=["security"],
                workstream="design",
            )
            await db.insert_finding(
                url="https://example.com/3",
                source_type="web",
                claim="Finding 3",
                evidence="Evidence 3",
                confidence=0.5,
                tags=["ai", "security"],
                workstream="research",
            )
            await db.insert_finding(
                url="https://example.com/4",
                source_type="paper",
                claim="Finding 4",
                evidence="Evidence 4",
                confidence=0.3,
                tags=["ml"],
                workstream="testing",
            )

    asyncio.run(setup_db())
    return db_path


class TestFilterState:
    """Test filter state management."""

    def test_initial_filter_state(self, tmp_path: Path) -> None:
        """Test that filter state is initialized correctly."""
        modal = ResearchImportModal(db_path=tmp_path / "test.db")

        assert modal.filter_workstream == ""
        assert modal.filter_tags == []
        assert modal.filter_min_confidence is None

    @pytest.mark.asyncio
    async def test_filter_state_persistence(self, populated_db: Path) -> None:
        """Test that filter state persists during modal session."""
        modal = ResearchImportModal(db_path=populated_db)

        # Set filter state
        modal.filter_workstream = "research"
        modal.filter_tags = ["ai", "ml"]
        modal.filter_min_confidence = 0.7

        # State should persist
        assert modal.filter_workstream == "research"
        assert modal.filter_tags == ["ai", "ml"]
        assert modal.filter_min_confidence == 0.7


class TestFilterApplication:
    """Test filter application to database queries."""

    @pytest.mark.asyncio
    async def test_workstream_filter(self, populated_db: Path) -> None:
        """Test filtering by workstream."""
        modal = ResearchImportModal(db_path=populated_db)

        # Mock the DataTable
        table_mock = MagicMock(spec=DataTable)
        table_mock.clear = MagicMock()
        table_mock.add_row = MagicMock()

        with patch.object(modal, "query_one", MagicMock(return_value=table_mock)):
            # Apply workstream filter
            modal.filter_workstream = "research"
            await modal.refresh_table()

            # Should have 2 findings with workstream="research"
            assert table_mock.add_row.call_count == 2

    @pytest.mark.asyncio
    async def test_confidence_filter(self, populated_db: Path) -> None:
        """Test filtering by minimum confidence."""
        modal = ResearchImportModal(db_path=populated_db)

        # Mock the DataTable
        table_mock = MagicMock(spec=DataTable)
        table_mock.clear = MagicMock()
        table_mock.add_row = MagicMock()

        with patch.object(modal, "query_one", MagicMock(return_value=table_mock)):
            # Apply confidence filter
            modal.filter_min_confidence = 0.6
            await modal.refresh_table()

            # Should have 2 findings with confidence >= 0.6
            assert table_mock.add_row.call_count == 2

    @pytest.mark.asyncio
    async def test_tag_filter_single(self, populated_db: Path) -> None:
        """Test filtering by a single tag."""
        modal = ResearchImportModal(db_path=populated_db)

        # Mock the DataTable
        table_mock = MagicMock(spec=DataTable)
        table_mock.clear = MagicMock()
        table_mock.add_row = MagicMock()

        with patch.object(modal, "query_one", MagicMock(return_value=table_mock)):
            # Apply tag filter
            modal.filter_tags = ["security"]
            await modal.refresh_table()

            # Should have 2 findings with "security" tag
            assert table_mock.add_row.call_count == 2

    @pytest.mark.asyncio
    async def test_tag_filter_multiple(self, populated_db: Path) -> None:
        """Test filtering by multiple tags (OR logic)."""
        modal = ResearchImportModal(db_path=populated_db)

        # Mock the DataTable
        table_mock = MagicMock(spec=DataTable)
        table_mock.clear = MagicMock()
        table_mock.add_row = MagicMock()

        with patch.object(modal, "query_one", MagicMock(return_value=table_mock)):
            # Apply multiple tag filter
            modal.filter_tags = ["ai", "ml"]
            await modal.refresh_table()

            # Should have 3 findings with either "ai" or "ml" tag
            assert table_mock.add_row.call_count == 3

    @pytest.mark.asyncio
    async def test_combined_filters(self, populated_db: Path) -> None:
        """Test combining multiple filters."""
        modal = ResearchImportModal(db_path=populated_db)

        # Mock the DataTable
        table_mock = MagicMock(spec=DataTable)
        table_mock.clear = MagicMock()
        table_mock.add_row = MagicMock()

        with patch.object(modal, "query_one", MagicMock(return_value=table_mock)):
            # Apply combined filters
            modal.filter_workstream = "research"
            modal.filter_tags = ["ai"]
            modal.filter_min_confidence = 0.5
            await modal.refresh_table()

            # Should have 2 findings matching all criteria
            assert table_mock.add_row.call_count == 2


class TestFilterButtons:
    """Test filter button handlers."""

    @pytest.mark.asyncio
    async def test_apply_filters_button(self, populated_db: Path) -> None:
        """Test applying filters via button handler."""
        modal = ResearchImportModal(db_path=populated_db)

        # Mock UI components
        workstream_input = MagicMock(spec=Input)
        workstream_input.value = "research"

        tags_input = MagicMock(spec=Input)
        tags_input.value = "ai, ml"

        confidence_input = MagicMock(spec=Input)
        confidence_input.value = "0.7"

        table_mock = MagicMock(spec=DataTable)
        table_mock.clear = MagicMock()
        table_mock.add_row = MagicMock()

        with patch.object(
            modal,
            "query_one",
            MagicMock(
                side_effect=lambda selector, _widget_type: {
                    "#filter-workstream": workstream_input,
                    "#filter-tags": tags_input,
                    "#filter-confidence": confidence_input,
                    "#findings-table": table_mock,
                }.get(selector)
            ),
        ):
            with patch.object(modal, "update_status", MagicMock()) as update_status_mock:
                # Apply filters
                await modal.handle_apply_filters()

                # Check filter state was updated
                assert modal.filter_workstream == "research"
                assert modal.filter_tags == ["ai", "ml"]
                assert modal.filter_min_confidence == 0.7

                # Check status was updated
                update_status_mock.assert_called_with("Filters applied", is_error=False)

    @pytest.mark.asyncio
    async def test_clear_filters_button(self, populated_db: Path) -> None:
        """Test clearing filters via button handler."""
        modal = ResearchImportModal(db_path=populated_db)

        # Set initial filter state
        modal.filter_workstream = "research"
        modal.filter_tags = ["ai", "ml"]
        modal.filter_min_confidence = 0.7

        # Mock UI components
        workstream_input = MagicMock(spec=Input)
        tags_input = MagicMock(spec=Input)
        confidence_input = MagicMock(spec=Input)

        table_mock = MagicMock(spec=DataTable)
        table_mock.clear = MagicMock()
        table_mock.add_row = MagicMock()

        with patch.object(
            modal,
            "query_one",
            MagicMock(
                side_effect=lambda selector, _widget_type: {
                    "#filter-workstream": workstream_input,
                    "#filter-tags": tags_input,
                    "#filter-confidence": confidence_input,
                    "#findings-table": table_mock,
                }.get(selector)
            ),
        ):
            with patch.object(modal, "update_status", MagicMock()) as update_status_mock:
                # Clear filters
                await modal.handle_clear_filters()

                # Check filter state was cleared
                assert modal.filter_workstream == ""
                assert modal.filter_tags == []
                assert modal.filter_min_confidence is None

                # Check input fields were cleared
                assert workstream_input.value == ""
                assert tags_input.value == ""
                assert confidence_input.value == ""

                # Check status was updated
                update_status_mock.assert_called_with("Filters cleared", is_error=False)


class TestInputValidation:
    """Test input validation for filters."""

    @pytest.mark.asyncio
    async def test_invalid_confidence_value(self, populated_db: Path) -> None:
        """Test handling of invalid confidence values."""
        modal = ResearchImportModal(db_path=populated_db)

        # Mock UI components
        workstream_input = MagicMock(spec=Input)
        workstream_input.value = ""

        tags_input = MagicMock(spec=Input)
        tags_input.value = ""

        confidence_input = MagicMock(spec=Input)
        confidence_input.value = "not_a_number"

        with patch.object(
            modal,
            "query_one",
            MagicMock(
                side_effect=lambda selector, _widget_type: {
                    "#filter-workstream": workstream_input,
                    "#filter-tags": tags_input,
                    "#filter-confidence": confidence_input,
                }.get(selector)
            ),
        ):
            with (
                patch.object(modal, "update_status", MagicMock()) as update_status_mock,
                patch.object(modal, "refresh_table", AsyncMock()) as refresh_table_mock,
            ):
                # Try to apply filters with invalid confidence
                await modal.handle_apply_filters()

                # Should show error status
                update_status_mock.assert_called_with("Invalid confidence value", is_error=True)

                # Should not refresh table
                refresh_table_mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_confidence_out_of_range(self, populated_db: Path) -> None:
        """Test handling of confidence values outside 0.0-1.0 range."""
        modal = ResearchImportModal(db_path=populated_db)

        # Mock UI components
        workstream_input = MagicMock(spec=Input)
        workstream_input.value = ""

        tags_input = MagicMock(spec=Input)
        tags_input.value = ""

        confidence_input = MagicMock(spec=Input)
        confidence_input.value = "1.5"

        with patch.object(
            modal,
            "query_one",
            MagicMock(
                side_effect=lambda selector, _widget_type: {
                    "#filter-workstream": workstream_input,
                    "#filter-tags": tags_input,
                    "#filter-confidence": confidence_input,
                }.get(selector)
            ),
        ):
            with (
                patch.object(modal, "update_status", MagicMock()) as update_status_mock,
                patch.object(modal, "refresh_table", AsyncMock()) as refresh_table_mock,
            ):
                # Try to apply filters with out-of-range confidence
                await modal.handle_apply_filters()

                # Should show error status
                update_status_mock.assert_called_with(
                    "Confidence must be between 0.0 and 1.0", is_error=True
                )

                # Should not refresh table
                refresh_table_mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_valid_confidence_boundaries(self, populated_db: Path) -> None:
        """Test that boundary values 0.0 and 1.0 are accepted."""
        modal = ResearchImportModal(db_path=populated_db)

        # Mock UI components and table
        workstream_input = MagicMock(spec=Input)
        workstream_input.value = ""

        tags_input = MagicMock(spec=Input)
        tags_input.value = ""

        confidence_input = MagicMock(spec=Input)

        table_mock = MagicMock(spec=DataTable)
        table_mock.clear = MagicMock()
        table_mock.add_row = MagicMock()

        with patch.object(
            modal,
            "query_one",
            MagicMock(
                side_effect=lambda selector, _widget_type: {
                    "#filter-workstream": workstream_input,
                    "#filter-tags": tags_input,
                    "#filter-confidence": confidence_input,
                    "#findings-table": table_mock,
                }.get(selector)
            ),
        ):
            with patch.object(modal, "update_status", MagicMock()):
                # Test 0.0
                confidence_input.value = "0.0"
                await modal.handle_apply_filters()
                assert modal.filter_min_confidence == 0.0

                # Test 1.0
                confidence_input.value = "1.0"
                await modal.handle_apply_filters()
                assert modal.filter_min_confidence == 1.0


class TestEmptyFilters:
    """Test behavior with empty filters."""

    @pytest.mark.asyncio
    async def test_empty_filters_show_all(self, populated_db: Path) -> None:
        """Test that empty filters show all findings."""
        modal = ResearchImportModal(db_path=populated_db)

        # Mock the DataTable
        table_mock = MagicMock(spec=DataTable)
        table_mock.clear = MagicMock()
        table_mock.add_row = MagicMock()

        with patch.object(modal, "query_one", MagicMock(return_value=table_mock)):
            # No filters applied
            await modal.refresh_table()

            # Should show all 4 findings
            assert table_mock.add_row.call_count == 4

    @pytest.mark.asyncio
    async def test_whitespace_only_filters(self, populated_db: Path) -> None:
        """Test that whitespace-only input is treated as empty."""
        modal = ResearchImportModal(db_path=populated_db)

        # Mock UI components
        workstream_input = MagicMock(spec=Input)
        workstream_input.value = "   "

        tags_input = MagicMock(spec=Input)
        tags_input.value = "   "

        confidence_input = MagicMock(spec=Input)
        confidence_input.value = "   "

        table_mock = MagicMock(spec=DataTable)
        table_mock.clear = MagicMock()
        table_mock.add_row = MagicMock()

        with patch.object(
            modal,
            "query_one",
            MagicMock(
                side_effect=lambda selector, _widget_type: {
                    "#filter-workstream": workstream_input,
                    "#filter-tags": tags_input,
                    "#filter-confidence": confidence_input,
                    "#findings-table": table_mock,
                }.get(selector)
            ),
        ):
            with patch.object(modal, "update_status", MagicMock()):
                # Apply filters with whitespace-only values
                await modal.handle_apply_filters()

                # Should treat as empty filters
                assert modal.filter_workstream == ""
                assert modal.filter_tags == []
                assert modal.filter_min_confidence is None
