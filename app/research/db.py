"""SQLite database with FTS for research findings."""

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Self

import aiosqlite


class ResearchDB:
    """Async SQLite database for research findings with FTS support."""

    def __init__(self, db_path: Path | str) -> None:
        """Initialize database with path."""
        self.db_path = Path(db_path) if isinstance(db_path, str) else db_path
        self.conn: aiosqlite.Connection | None = None

    async def __aenter__(self) -> Self:
        """Enter async context manager."""
        self.conn = await aiosqlite.connect(str(self.db_path))
        await self.init_db()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context manager."""
        if self.conn:
            await self.conn.close()
            self.conn = None

    async def init_db(self) -> None:
        """Initialize database schema and FTS index."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        # Create schema version table for migrations
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TEXT DEFAULT (datetime('now'))
            )
        """)

        # Check current schema version
        async with self.conn.execute("SELECT MAX(version) FROM schema_version") as cursor:
            row = await cursor.fetchone()
            current_version = row[0] if row and row[0] is not None else 0

        # If no schema version exists (new database), create v2 directly
        if current_version == 0:
            # Create main findings table with CHECK constraint
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS findings (
                    id TEXT PRIMARY KEY,
                    url TEXT,
                    source_type TEXT,
                    claim TEXT,
                    evidence TEXT,
                    confidence REAL CHECK (confidence BETWEEN 0.0 AND 1.0),
                    tags TEXT,
                    workstream TEXT,
                    retrieved_at TEXT
                )
            """)
            # Set schema version to 2
            await self.conn.execute("""
                INSERT INTO schema_version (version) VALUES (2)
            """)
        elif current_version == 1:
            # Check if findings table exists
            async with self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='findings'"
            ) as cursor:
                table_exists = await cursor.fetchone() is not None

            if table_exists:
                # Migrate from v1 to v2: Add CHECK constraint
                # SQLite doesn't support ALTER TABLE ADD CONSTRAINT directly,
                # so we need to recreate the table

                # Check for any invalid data first
                async with self.conn.execute(
                    "SELECT COUNT(*) FROM findings WHERE confidence < 0.0 OR confidence > 1.0"
                ) as cursor:
                    invalid_row = await cursor.fetchone()
                    invalid_count = invalid_row[0] if invalid_row else 0

                if invalid_count > 0:
                    # Fix invalid data by clamping to valid range
                    await self.conn.execute("""
                        UPDATE findings
                        SET confidence = MAX(0.0, MIN(1.0, confidence))
                        WHERE confidence < 0.0 OR confidence > 1.0
                    """)

                # Create new table with constraint
                await self.conn.execute("""
                    CREATE TABLE findings_v2 (
                        id TEXT PRIMARY KEY,
                        url TEXT,
                        source_type TEXT,
                        claim TEXT,
                        evidence TEXT,
                        confidence REAL CHECK (confidence BETWEEN 0.0 AND 1.0),
                        tags TEXT,
                        workstream TEXT,
                        retrieved_at TEXT
                    )
                """)

                # Copy data from old table to new
                await self.conn.execute("""
                    INSERT INTO findings_v2
                    SELECT id, url, source_type, claim, evidence,
                           confidence, tags, workstream, retrieved_at
                    FROM findings
                """)

                # Drop old table and rename new one
                await self.conn.execute("DROP TABLE findings")
                await self.conn.execute("ALTER TABLE findings_v2 RENAME TO findings")

                # Update schema version to 2
                await self.conn.execute("""
                    INSERT INTO schema_version (version) VALUES (2)
                """)
            else:
                # No findings table yet, create with constraint
                await self.conn.execute("""
                    CREATE TABLE findings (
                        id TEXT PRIMARY KEY,
                        url TEXT,
                        source_type TEXT,
                        claim TEXT,
                        evidence TEXT,
                        confidence REAL CHECK (confidence BETWEEN 0.0 AND 1.0),
                        tags TEXT,
                        workstream TEXT,
                        retrieved_at TEXT
                    )
                """)
                # Update schema version to 2
                await self.conn.execute("""
                    INSERT INTO schema_version (version) VALUES (2)
                """)
        else:
            # For v2 or higher, just ensure table exists (idempotent)
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS findings (
                    id TEXT PRIMARY KEY,
                    url TEXT,
                    source_type TEXT,
                    claim TEXT,
                    evidence TEXT,
                    confidence REAL CHECK (confidence BETWEEN 0.0 AND 1.0),
                    tags TEXT,
                    workstream TEXT,
                    retrieved_at TEXT
                )
            """)

        # Create indexes for better query performance
        await self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_workstream ON findings(workstream)
        """)
        await self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_source_type ON findings(source_type)
        """)
        await self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_confidence ON findings(confidence)
        """)
        await self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_retrieved_at ON findings(retrieved_at)
        """)

        # Create FTS5 virtual table for full-text search
        # Note: We don't use content=findings because it causes FTS5 to read
        # directly from the findings table, bypassing our trigger updates
        await self.conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS findings_fts USING fts5(
                id UNINDEXED,
                claim,
                evidence
            )
        """)

        # Create triggers to keep FTS in sync
        # Drop old triggers first to ensure clean state
        await self.conn.execute("DROP TRIGGER IF EXISTS findings_ai")
        await self.conn.execute("DROP TRIGGER IF EXISTS findings_ad")
        await self.conn.execute("DROP TRIGGER IF EXISTS findings_au")

        await self.conn.execute("""
            CREATE TRIGGER findings_ai
            AFTER INSERT ON findings BEGIN
                INSERT INTO findings_fts(id, claim, evidence)
                VALUES (new.id, new.claim, new.evidence);
            END
        """)

        await self.conn.execute("""
            CREATE TRIGGER findings_ad
            AFTER DELETE ON findings BEGIN
                DELETE FROM findings_fts WHERE id = old.id;
            END
        """)

        await self.conn.execute("""
            CREATE TRIGGER findings_au
            AFTER UPDATE ON findings BEGIN
                DELETE FROM findings_fts WHERE id = old.id;
                INSERT INTO findings_fts(id, claim, evidence)
                VALUES (new.id, new.claim, new.evidence);
            END
        """)

        await self.conn.commit()

    async def insert_finding(
        self,
        url: str,
        source_type: str,
        claim: str,
        evidence: str,
        confidence: float,
        tags: list[str] | None = None,
        workstream: str | None = None,
    ) -> str:
        """Insert a new finding and return its ID."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        finding_id = str(uuid.uuid4())
        tags_json = json.dumps(tags or [])
        retrieved_at = datetime.now(UTC).isoformat()

        await self.conn.execute(
            """
            INSERT INTO findings (id, url, source_type, claim, evidence,
                                confidence, tags, workstream, retrieved_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                finding_id,
                url,
                source_type,
                claim,
                evidence,
                confidence,
                tags_json,
                workstream,
                retrieved_at,
            ),
        )
        await self.conn.commit()
        return finding_id

    async def update_finding(
        self,
        finding_id: str,
        url: str | None = None,
        source_type: str | None = None,
        claim: str | None = None,
        evidence: str | None = None,
        confidence: float | None = None,
        tags: list[str] | None = None,
        workstream: str | None = None,
    ) -> bool:
        """Update an existing finding. Returns True if found and updated."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        # Get current values
        async with self.conn.execute(
            "SELECT * FROM findings WHERE id = ?", (finding_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return False

        # Build update query dynamically
        updates = []
        params: list[Any] = []

        if url is not None:
            updates.append("url = ?")
            params.append(url)
        if source_type is not None:
            updates.append("source_type = ?")
            params.append(source_type)
        if claim is not None:
            updates.append("claim = ?")
            params.append(claim)
        if evidence is not None:
            updates.append("evidence = ?")
            params.append(evidence)
        if confidence is not None:
            updates.append("confidence = ?")
            params.append(confidence)
        if tags is not None:
            updates.append("tags = ?")
            params.append(json.dumps(tags))
        if workstream is not None:
            updates.append("workstream = ?")
            params.append(workstream)

        if not updates:
            return True  # Nothing to update

        params.append(finding_id)
        query = f"UPDATE findings SET {', '.join(updates)} WHERE id = ?"  # nosec B608

        await self.conn.execute(query, params)
        await self.conn.commit()
        return True

    async def delete_finding(self, finding_id: str) -> bool:
        """Delete a finding. Returns True if found and deleted."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        cursor = await self.conn.execute("DELETE FROM findings WHERE id = ?", (finding_id,))
        await self.conn.commit()
        return cursor.rowcount > 0

    async def get_finding(self, finding_id: str) -> dict[str, Any] | None:
        """Get a finding by ID."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        async with self.conn.execute(
            "SELECT * FROM findings WHERE id = ?", (finding_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None

            return {
                "id": row[0],
                "url": row[1],
                "source_type": row[2],
                "claim": row[3],
                "evidence": row[4],
                "confidence": row[5],
                "tags": json.loads(row[6]) if row[6] else [],
                "workstream": row[7],
                "retrieved_at": row[8],
            }

    async def search_fts(
        self,
        query: str,
        workstream: str | None = None,
        source_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Search findings using full-text search on claim and evidence.

        Returns results with rank (bm25 score) where lower values indicate better matches.
        Optional filters for workstream and source_type can be applied.
        """
        if not self.conn:
            raise RuntimeError("Database not connected")

        # Build WHERE clause with optional filters
        conditions = ["findings_fts MATCH ?"]
        params: list[Any] = [query]

        if workstream:
            conditions.append("f.workstream = ?")
            params.append(workstream)
        if source_type:
            conditions.append("f.source_type = ?")
            params.append(source_type)

        where_clause = " AND ".join(conditions)
        params.append(limit)

        results = []
        async with self.conn.execute(
            f"""
            SELECT f.id, f.url, f.source_type, f.claim, f.evidence,
                   f.confidence, f.tags, f.workstream, f.retrieved_at,
                   bm25(findings_fts) AS rank
            FROM findings_fts fts
            JOIN findings f ON fts.id = f.id
            WHERE {where_clause}
            ORDER BY bm25(findings_fts)
            LIMIT ?
            """,  # nosec B608
            params,
        ) as cursor:
            async for row in cursor:
                results.append(
                    {
                        "id": row[0],
                        "url": row[1],
                        "source_type": row[2],
                        "claim": row[3],
                        "evidence": row[4],
                        "confidence": row[5],
                        "tags": json.loads(row[6]) if row[6] else [],
                        "workstream": row[7],
                        "retrieved_at": row[8],
                        "rank": row[9],
                    }
                )

        return results

    async def list_findings(
        self,
        workstream: str | None = None,
        source_type: str | None = None,
        min_confidence: float | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List findings with optional filters."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        conditions = []
        params: list[Any] = []

        if workstream:
            conditions.append("workstream = ?")
            params.append(workstream)
        if source_type:
            conditions.append("source_type = ?")
            params.append(source_type)
        if min_confidence is not None:
            conditions.append("confidence >= ?")
            params.append(min_confidence)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.append(limit)

        query = f"""
            SELECT * FROM findings
            {where_clause}
            ORDER BY retrieved_at DESC
            LIMIT ?
        """  # nosec B608

        results = []
        async with self.conn.execute(query, params) as cursor:
            async for row in cursor:
                results.append(
                    {
                        "id": row[0],
                        "url": row[1],
                        "source_type": row[2],
                        "claim": row[3],
                        "evidence": row[4],
                        "confidence": row[5],
                        "tags": json.loads(row[6]) if row[6] else [],
                        "workstream": row[7],
                        "retrieved_at": row[8],
                    }
                )

        return results
