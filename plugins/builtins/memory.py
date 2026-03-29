from __future__ import annotations

from typing import Dict, List
import sqlite3

from sweetiebot.memory.models import MemoryQuery, MemoryRecord
from sweetiebot.plugins.base import MemoryStorePlugin


class InMemoryStorePlugin(MemoryStorePlugin):
    plugin_id = "sweetiebot.memory.inmemory"

    def __init__(self) -> None:
        self.records: List[MemoryRecord] = []
        self.config = {}

    def manifest(self) -> Dict[str, object]:
        base = super().manifest()
        base.capabilities = ["put", "query", "recent"]
        return base

    def put(self, record: MemoryRecord) -> MemoryRecord:
        self.records.append(record)
        return record

    def query(self, query: MemoryQuery) -> List[MemoryRecord]:
        items = list(self.records)
        if query.kind:
            items = [r for r in items if r.kind == query.kind]
        if query.scope:
            items = [r for r in items if r.scope == query.scope]
        if query.text:
            needle = query.text.lower()
            items = [r for r in items if needle in r.content.lower()]
        items.sort(key=lambda r: r.created_at, reverse=True)
        return items[: query.limit]

    def healthcheck(self) -> Dict[str, object]:
        return {"healthy": True, "records": len(self.records), "plugin_id": self.plugin_id}


class SQLiteMemoryStorePlugin(MemoryStorePlugin):
    plugin_id = "sweetiebot.memory.sqlite"

    def __init__(self) -> None:
        self.config = {"path": ":memory:"}
        self._conn: sqlite3.Connection | None = None

    def configure(self, config=None) -> None:
        super().configure(config)
        path = self.config.get("path", ":memory:")
        self._conn = sqlite3.connect(path)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        assert self._conn is not None
        self._conn.execute(
            '''
            CREATE TABLE IF NOT EXISTS memory_records (
                record_id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT NOT NULL,
                tags TEXT NOT NULL,
                scope TEXT NOT NULL,
                importance REAL NOT NULL,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            '''
        )
        self._conn.commit()

    def manifest(self) -> Dict[str, object]:
        base = super().manifest()
        base.capabilities = ["put", "query", "recent", "persistence"]
        return base

    def put(self, record: MemoryRecord) -> MemoryRecord:
        assert self._conn is not None, "SQLite memory store not configured"
        self._conn.execute(
            '''
            INSERT OR REPLACE INTO memory_records
            (record_id, kind, content, source, tags, scope, importance, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                record.record_id,
                record.kind,
                record.content,
                record.source,
                ",".join(record.tags),
                record.scope,
                record.importance,
                __import__("json").dumps(record.metadata),
                record.created_at,
            ),
        )
        self._conn.commit()
        return record

    def query(self, query: MemoryQuery) -> List[MemoryRecord]:
        assert self._conn is not None, "SQLite memory store not configured"
        clauses = []
        params = []
        if query.kind:
            clauses.append("kind = ?")
            params.append(query.kind)
        if query.scope:
            clauses.append("scope = ?")
            params.append(query.scope)
        if query.text:
            clauses.append("LOWER(content) LIKE ?")
            params.append(f"%{query.text.lower()}%")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(query.limit)
        rows = self._conn.execute(
            f'''
            SELECT * FROM memory_records
            {where}
            ORDER BY created_at DESC
            LIMIT ?
            ''',
            params,
        ).fetchall()
        return [
            MemoryRecord(
                record_id=row["record_id"],
                kind=row["kind"],
                content=row["content"],
                source=row["source"],
                tags=[tag for tag in row["tags"].split(",") if tag],
                scope=row["scope"],
                importance=row["importance"],
                metadata=__import__("json").loads(row["metadata_json"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def healthcheck(self) -> Dict[str, object]:
        if self._conn is None:
            return {"healthy": False, "plugin_id": self.plugin_id, "reason": "not_configured"}
        count = self._conn.execute("SELECT COUNT(*) FROM memory_records").fetchone()[0]
        return {"healthy": True, "plugin_id": self.plugin_id, "records": count}

    def shutdown(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
