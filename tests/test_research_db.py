"""Tests for research database with FTS."""

from pathlib import Path

import aiosqlite
import pytest

from app.research.db import ResearchDB


@pytest.mark.asyncio
async def test_init_db_creates_schema(tmp_path: Path) -> None:
    """Test that init_db creates proper schema with FTS."""
    db_path = tmp_path / "test.db"

    async with ResearchDB(db_path) as db:
        # Verify tables exist
        assert db.conn is not None
        async with db.conn.execute("SELECT name FROM sqlite_master WHERE type='table'") as cursor:
            tables = [row[0] for row in await cursor.fetchall()]
            assert "findings" in tables
            assert "findings_fts" in tables
            assert "findings_fts_data" in tables  # FTS5 internal table

        # Verify triggers exist
        assert db.conn is not None
        async with db.conn.execute("SELECT name FROM sqlite_master WHERE type='trigger'") as cursor:
            triggers = [row[0] for row in await cursor.fetchall()]
            assert "findings_ai" in triggers
            assert "findings_ad" in triggers
            assert "findings_au" in triggers


@pytest.mark.asyncio
async def test_insert_finding(tmp_path: Path) -> None:
    """Test inserting a finding."""
    db_path = tmp_path / "test.db"

    async with ResearchDB(db_path) as db:
        finding_id = await db.insert_finding(
            url="https://example.com",
            source_type="web",
            claim="Test claim",
            evidence="Test evidence",
            confidence=0.85,
            tags=["test", "example"],
            workstream="research",
        )

        assert finding_id  # Should be a UUID
        assert len(finding_id) == 36  # UUID format

        # Verify it was inserted
        finding = await db.get_finding(finding_id)
        assert finding is not None
        assert finding["url"] == "https://example.com"
        assert finding["claim"] == "Test claim"
        assert finding["evidence"] == "Test evidence"
        assert finding["confidence"] == 0.85
        assert finding["tags"] == ["test", "example"]
        assert finding["workstream"] == "research"


@pytest.mark.asyncio
async def test_update_finding(tmp_path: Path) -> None:
    """Test updating a finding."""
    db_path = tmp_path / "test.db"

    async with ResearchDB(db_path) as db:
        # Insert initial finding
        finding_id = await db.insert_finding(
            url="https://example.com",
            source_type="web",
            claim="Original claim",
            evidence="Original evidence",
            confidence=0.5,
        )

        # Update some fields
        updated = await db.update_finding(
            finding_id,
            claim="Updated claim",
            confidence=0.9,
            tags=["updated"],
        )
        assert updated is True

        # Verify updates
        finding = await db.get_finding(finding_id)
        assert finding is not None
        assert finding["claim"] == "Updated claim"
        assert finding["confidence"] == 0.9
        assert finding["tags"] == ["updated"]
        # Unchanged fields
        assert finding["url"] == "https://example.com"
        assert finding["evidence"] == "Original evidence"

        # Test updating non-existent finding
        updated = await db.update_finding("non-existent-id", claim="New")
        assert updated is False


@pytest.mark.asyncio
async def test_delete_finding(tmp_path: Path) -> None:
    """Test deleting a finding."""
    db_path = tmp_path / "test.db"

    async with ResearchDB(db_path) as db:
        # Insert finding
        finding_id = await db.insert_finding(
            url="https://example.com",
            source_type="web",
            claim="To be deleted",
            evidence="Evidence",
            confidence=0.7,
        )

        # Delete it
        deleted = await db.delete_finding(finding_id)
        assert deleted is True

        # Verify it's gone
        finding = await db.get_finding(finding_id)
        assert finding is None

        # Test deleting non-existent finding
        deleted = await db.delete_finding("non-existent-id")
        assert deleted is False


@pytest.mark.asyncio
async def test_get_finding(tmp_path: Path) -> None:
    """Test getting a finding by ID."""
    db_path = tmp_path / "test.db"

    async with ResearchDB(db_path) as db:
        # Test non-existent finding
        finding = await db.get_finding("non-existent")
        assert finding is None

        # Insert and retrieve
        finding_id = await db.insert_finding(
            url="https://example.com",
            source_type="paper",
            claim="Test claim",
            evidence="Test evidence",
            confidence=0.95,
            tags=["ai", "ml"],
            workstream="design",
        )

        finding = await db.get_finding(finding_id)
        assert finding is not None
        assert finding["id"] == finding_id
        assert finding["source_type"] == "paper"
        assert finding["tags"] == ["ai", "ml"]


@pytest.mark.asyncio
async def test_search_fts(tmp_path: Path) -> None:
    """Test full-text search functionality."""
    db_path = tmp_path / "test.db"

    async with ResearchDB(db_path) as db:
        # Insert test data
        await db.insert_finding(
            url="https://example1.com",
            source_type="web",
            claim="Machine learning improves performance",
            evidence="Studies show ML models achieve 95% accuracy",
            confidence=0.9,
        )

        await db.insert_finding(
            url="https://example2.com",
            source_type="paper",
            claim="Deep learning requires large datasets",
            evidence="Neural networks need millions of examples",
            confidence=0.85,
        )

        await db.insert_finding(
            url="https://example3.com",
            source_type="web",
            claim="Python is popular for data science",
            evidence="Python has extensive ML libraries",
            confidence=0.95,
        )

        # Search for "learning"
        results = await db.search_fts("learning")
        assert len(results) == 2
        claims = [r["claim"] for r in results]
        assert "Machine learning improves performance" in claims
        assert "Deep learning requires large datasets" in claims

        # Search for "Python"
        results = await db.search_fts("Python")
        assert len(results) == 1
        assert results[0]["claim"] == "Python is popular for data science"

        # Search in evidence
        results = await db.search_fts("accuracy")
        assert len(results) == 1
        assert "95% accuracy" in results[0]["evidence"]

        # Search with no matches
        results = await db.search_fts("nonexistent")
        assert len(results) == 0

        # Test limit
        results = await db.search_fts("learning", limit=1)
        assert len(results) == 1


@pytest.mark.asyncio
async def test_list_findings(tmp_path: Path) -> None:
    """Test listing findings with filters."""
    db_path = tmp_path / "test.db"

    async with ResearchDB(db_path) as db:
        # Insert test data
        await db.insert_finding(
            url="https://1.com",
            source_type="web",
            claim="Claim 1",
            evidence="Evidence 1",
            confidence=0.6,
            workstream="research",
        )

        await db.insert_finding(
            url="https://2.com",
            source_type="paper",
            claim="Claim 2",
            evidence="Evidence 2",
            confidence=0.8,
            workstream="research",
        )

        await db.insert_finding(
            url="https://3.com",
            source_type="web",
            claim="Claim 3",
            evidence="Evidence 3",
            confidence=0.9,
            workstream="design",
        )

        # List all
        results = await db.list_findings()
        assert len(results) == 3

        # Filter by workstream
        results = await db.list_findings(workstream="research")
        assert len(results) == 2
        assert all(r["workstream"] == "research" for r in results)

        # Filter by source_type
        results = await db.list_findings(source_type="web")
        assert len(results) == 2
        assert all(r["source_type"] == "web" for r in results)

        # Filter by confidence
        results = await db.list_findings(min_confidence=0.8)
        assert len(results) == 2
        assert all(r["confidence"] >= 0.8 for r in results)

        # Combined filters
        results = await db.list_findings(workstream="research", min_confidence=0.7)
        assert len(results) == 1
        assert results[0]["claim"] == "Claim 2"

        # Test limit
        results = await db.list_findings(limit=2)
        assert len(results) == 2


@pytest.mark.asyncio
async def test_fts_sync_with_crud(tmp_path: Path) -> None:
    """Test that FTS stays in sync with CRUD operations."""
    db_path = tmp_path / "test.db"

    async with ResearchDB(db_path) as db:
        # Insert and search
        finding_id = await db.insert_finding(
            url="https://example.com",
            source_type="web",
            claim="Original searchable claim",
            evidence="Original evidence",
            confidence=0.7,
        )

        results = await db.search_fts("searchable")
        assert len(results) == 1
        assert results[0]["id"] == finding_id

        # Update and search with new term
        await db.update_finding(finding_id, claim="Updated different claim")

        results = await db.search_fts("searchable")
        assert len(results) == 0  # Old term not found

        results = await db.search_fts("different")
        assert len(results) == 1  # New term found
        assert results[0]["id"] == finding_id

        # Delete and search
        await db.delete_finding(finding_id)
        results = await db.search_fts("different")
        assert len(results) == 0  # Deleted entry not found


@pytest.mark.asyncio
async def test_special_characters_in_data(tmp_path: Path) -> None:
    """Test handling of special characters and edge cases."""
    db_path = tmp_path / "test.db"

    async with ResearchDB(db_path) as db:
        # Test with quotes and special chars
        finding_id = await db.insert_finding(
            url="https://example.com/path?query=1&test='value'",
            source_type="web",
            claim='Claim with "quotes" and special chars: @#$%',
            evidence="Evidence with\nnewlines\tand\ttabs",
            confidence=0.5,
            tags=["tag-with-dash", "tag_with_underscore"],
        )

        finding = await db.get_finding(finding_id)
        assert finding is not None
        assert finding["claim"] == 'Claim with "quotes" and special chars: @#$%'
        assert "\n" in finding["evidence"]
        assert "\t" in finding["evidence"]

        # Search should still work
        results = await db.search_fts("quotes")
        assert len(results) == 1


@pytest.mark.asyncio
async def test_empty_optional_fields(tmp_path: Path) -> None:
    """Test inserting findings with minimal data."""
    db_path = tmp_path / "test.db"

    async with ResearchDB(db_path) as db:
        # Insert with only required fields
        finding_id = await db.insert_finding(
            url="https://example.com",
            source_type="web",
            claim="Minimal claim",
            evidence="Minimal evidence",
            confidence=0.5,
            # tags, workstream are optional
        )

        finding = await db.get_finding(finding_id)
        assert finding is not None
        assert finding["tags"] == []
        assert finding["workstream"] is None


@pytest.mark.asyncio
async def test_idempotent_init(tmp_path: Path) -> None:
    """Test that init_db is idempotent."""
    db_path = tmp_path / "test.db"

    # First initialization
    async with ResearchDB(db_path) as db:
        finding_id = await db.insert_finding(
            url="https://example.com",
            source_type="web",
            claim="Test claim",
            evidence="Test evidence",
            confidence=0.7,
        )

    # Second initialization should not lose data
    async with ResearchDB(db_path) as db:
        finding = await db.get_finding(finding_id)
        assert finding is not None
        assert finding["claim"] == "Test claim"

        # FTS should still work
        results = await db.search_fts("Test")
        assert len(results) == 1


@pytest.mark.asyncio
async def test_context_manager_cleanup(tmp_path: Path) -> None:
    """Test that context manager properly cleans up."""
    db_path = tmp_path / "test.db"

    db = ResearchDB(db_path)
    assert db.conn is None

    async with db:
        assert db.conn is not None
        # Connection should be open
        await db.insert_finding(
            url="https://example.com",
            source_type="web",
            claim="Test",
            evidence="Test",
            confidence=0.5,
        )

    # After context, connection should be closed
    assert db.conn is None


@pytest.mark.asyncio
async def test_runtime_errors_without_connection() -> None:
    """Test that methods raise errors when not connected."""
    db = ResearchDB(":memory:")  # Not connected yet

    with pytest.raises(RuntimeError, match="Database not connected"):
        await db.insert_finding(
            url="test", source_type="test", claim="test", evidence="test", confidence=0.5
        )

    with pytest.raises(RuntimeError, match="Database not connected"):
        await db.get_finding("test-id")

    with pytest.raises(RuntimeError, match="Database not connected"):
        await db.search_fts("test")


@pytest.mark.asyncio
async def test_tags_json_handling(tmp_path: Path) -> None:
    """Test proper JSON handling for tags field."""
    db_path = tmp_path / "test.db"

    async with ResearchDB(db_path) as db:
        # Test with various tag formats
        finding_id = await db.insert_finding(
            url="https://example.com",
            source_type="web",
            claim="Test",
            evidence="Test",
            confidence=0.5,
            tags=["tag1", "tag-2", "tag_3", "TAG4"],
        )

        finding = await db.get_finding(finding_id)
        assert finding is not None
        assert finding["tags"] == ["tag1", "tag-2", "tag_3", "TAG4"]

        # Update with new tags
        await db.update_finding(finding_id, tags=["new", "tags"])
        finding = await db.get_finding(finding_id)
        assert finding is not None
        assert finding["tags"] == ["new", "tags"]

        # Clear tags
        await db.update_finding(finding_id, tags=[])
        finding = await db.get_finding(finding_id)
        assert finding is not None
        assert finding["tags"] == []


@pytest.mark.asyncio
async def test_confidence_constraint(tmp_path: Path) -> None:
    """Test that confidence CHECK constraint rejects out-of-range values."""
    db_path = tmp_path / "test.db"

    async with ResearchDB(db_path) as db:
        # Test valid confidence values at boundaries
        finding_id_min = await db.insert_finding(
            url="https://example.com",
            source_type="web",
            claim="Min confidence",
            evidence="Test",
            confidence=0.0,
        )
        assert finding_id_min is not None

        finding_id_max = await db.insert_finding(
            url="https://example.com",
            source_type="web",
            claim="Max confidence",
            evidence="Test",
            confidence=1.0,
        )
        assert finding_id_max is not None

        # Test confidence > 1.0 should raise
        with pytest.raises(aiosqlite.IntegrityError):
            await db.insert_finding(
                url="https://example.com",
                source_type="web",
                claim="Invalid high confidence",
                evidence="Test",
                confidence=1.5,
            )

        # Test confidence < 0.0 should raise
        with pytest.raises(aiosqlite.IntegrityError):
            await db.insert_finding(
                url="https://example.com",
                source_type="web",
                claim="Invalid negative confidence",
                evidence="Test",
                confidence=-0.5,
            )

        # Test update with invalid confidence
        with pytest.raises(aiosqlite.IntegrityError):
            await db.update_finding(finding_id_min, confidence=1.1)

        # Verify the valid findings are still there
        finding_min = await db.get_finding(finding_id_min)
        assert finding_min is not None
        assert finding_min["confidence"] == 0.0

        finding_max = await db.get_finding(finding_id_max)
        assert finding_max is not None
        assert finding_max["confidence"] == 1.0


@pytest.mark.asyncio
async def test_migration_idempotency(tmp_path: Path) -> None:
    """Test that migration from v1 to v2 is idempotent and preserves data."""
    db_path = tmp_path / "test.db"

    # First, create a v1 database (without CHECK constraint)
    async with aiosqlite.connect(str(db_path)) as conn:
        # Create v1 schema manually (without CHECK constraint)
        await conn.execute("""
            CREATE TABLE schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TEXT DEFAULT (datetime('now'))
            )
        """)
        await conn.execute("INSERT INTO schema_version (version) VALUES (1)")

        await conn.execute("""
            CREATE TABLE findings (
                id TEXT PRIMARY KEY,
                url TEXT,
                source_type TEXT,
                claim TEXT,
                evidence TEXT,
                confidence REAL,
                tags TEXT,
                workstream TEXT,
                retrieved_at TEXT
            )
        """)

        # Insert some test data, including edge-case confidence values
        await conn.execute("""
            INSERT INTO findings (id, url, source_type, claim, evidence, confidence, tags, workstream, retrieved_at)
            VALUES ('test-1', 'https://example.com', 'web', 'Test claim', 'Test evidence', 0.5, '[]', 'research', '2024-01-01')
        """)
        await conn.execute("""
            INSERT INTO findings (id, url, source_type, claim, evidence, confidence, tags, workstream, retrieved_at)
            VALUES ('test-2', 'https://example.com', 'paper', 'Another claim', 'More evidence', 0.99, '["test"]', 'design', '2024-01-02')
        """)
        await conn.commit()

    # Now open with ResearchDB, which should trigger migration to v2
    async with ResearchDB(db_path) as db:
        # Check that data is preserved
        finding1 = await db.get_finding("test-1")
        assert finding1 is not None
        assert finding1["claim"] == "Test claim"
        assert finding1["confidence"] == 0.5

        finding2 = await db.get_finding("test-2")
        assert finding2 is not None
        assert finding2["claim"] == "Another claim"
        assert finding2["confidence"] == 0.99

        # Verify schema version is now 2
        assert db.conn is not None
        async with db.conn.execute("SELECT MAX(version) FROM schema_version") as cursor:
            row = await cursor.fetchone()
            assert row is not None and row[0] == 2

        # Try to insert invalid confidence (should fail now)
        with pytest.raises(aiosqlite.IntegrityError):
            await db.insert_finding(
                url="https://example.com",
                source_type="web",
                claim="Invalid",
                evidence="Test",
                confidence=1.5,
            )

    # Open again to test idempotency (should not break or lose data)
    async with ResearchDB(db_path) as db:
        # Check that data is still preserved
        finding1 = await db.get_finding("test-1")
        assert finding1 is not None
        assert finding1["claim"] == "Test claim"

        finding2 = await db.get_finding("test-2")
        assert finding2 is not None
        assert finding2["claim"] == "Another claim"

        # Verify schema version is still 2
        assert db.conn is not None
        async with db.conn.execute("SELECT MAX(version) FROM schema_version") as cursor:
            row = await cursor.fetchone()
            assert row is not None and row[0] == 2

        # Should still be able to insert valid findings
        new_id = await db.insert_finding(
            url="https://example.com",
            source_type="web",
            claim="New finding after migration",
            evidence="Test",
            confidence=0.75,
        )
        assert new_id is not None
