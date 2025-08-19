#!/usr/bin/env python3
"""Test script to verify FTS sync fix works correctly."""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from app.research.db import ResearchDB


async def test_fts_sync() -> None:
    """Test that FTS properly syncs with CRUD operations."""
    db_path = Path("/tmp/test_fts_sync.db")
    db_path.unlink(missing_ok=True)

    async with ResearchDB(db_path) as db:
        print("Testing FTS sync with CRUD operations...")

        # Insert a finding
        finding_id = await db.insert_finding(
            url="https://example.com",
            source_type="web",
            claim="Original searchable claim",
            evidence="Original evidence",
            confidence=0.7,
        )
        print(f"✓ Inserted finding with ID: {finding_id}")

        # Search for original term
        results = await db.search_fts("searchable")
        assert len(results) == 1, f"Expected 1 result for 'searchable', got {len(results)}"
        print("✓ Found 1 result for 'searchable' before update")

        # Update the claim
        success = await db.update_finding(finding_id, claim="Updated different claim")
        assert success, "Failed to update finding"
        print("✓ Updated finding claim")

        # Search for old term (should not find)
        results = await db.search_fts("searchable")
        assert (
            len(results) == 0
        ), f"Expected 0 results for 'searchable' after update, got {len(results)}"
        print("✓ Found 0 results for 'searchable' after update")

        # Search for new term (should find)
        results = await db.search_fts("different")
        assert len(results) == 1, f"Expected 1 result for 'different', got {len(results)}"
        print("✓ Found 1 result for 'different' after update")

        # Delete and verify
        success = await db.delete_finding(finding_id)
        assert success, "Failed to delete finding"
        results = await db.search_fts("different")
        assert len(results) == 0, f"Expected 0 results after delete, got {len(results)}"
        print("✓ Found 0 results after delete")

        print("\n✅ All FTS sync tests passed!")

    # Cleanup
    db_path.unlink(missing_ok=True)


if __name__ == "__main__":
    try:
        asyncio.run(test_fts_sync())
    except Exception as e:
        print(f"\n❌ Test failed: {e}", file=sys.stderr)
        sys.exit(1)
