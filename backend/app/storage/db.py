"""Storage layer for investigation sessions, timeline replays, and audit logs."""

import json
import sqlite3
from typing import Dict, List, Optional, Any
from datetime import datetime
from backend.app.config import settings
from backend.app.models.state import InvestigationState


class InvestigationStore:
    """Provides memory and SQLite-backed storage for investigations."""

    _instances: Dict[str, InvestigationState] = {}

    @classmethod
    def save(cls, state: InvestigationState) -> None:
        cls._instances[state.id] = state
        # Optionally write snapshot to SQLite
        try:
            with sqlite3.connect(settings.DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS investigations (
                        id TEXT PRIMARY KEY,
                        incident TEXT,
                        namespace TEXT,
                        status TEXT,
                        confidence REAL,
                        start_time TEXT,
                        end_time TEXT,
                        payload JSON
                    )
                """)
                cursor.execute("""
                    INSERT OR REPLACE INTO investigations 
                    (id, incident, namespace, status, confidence, start_time, end_time, payload)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    state.id,
                    state.incident,
                    state.namespace,
                    state.status.value,
                    state.confidence,
                    state.start_time.isoformat(),
                    state.end_time.isoformat() if state.end_time else None,
                    state.model_dump_json()
                ))
                conn.commit()
        except Exception:
            pass

    @classmethod
    def get(cls, investigation_id: str) -> Optional[InvestigationState]:
        if investigation_id in cls._instances:
            return cls._instances[investigation_id]

        try:
            with sqlite3.connect(settings.DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT payload FROM investigations WHERE id = ?", (investigation_id,))
                row = cursor.fetchone()
                if row:
                    state_dict = json.loads(row[0])
                    state = InvestigationState.model_validate(state_dict)
                    cls._instances[investigation_id] = state
                    return state
        except Exception:
            pass

        return None

    @classmethod
    def list_all(cls) -> List[Dict[str, Any]]:
        # Check SQLite first, or memory
        results = []
        try:
            with sqlite3.connect(settings.DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS investigations (
                        id TEXT PRIMARY KEY,
                        incident TEXT,
                        namespace TEXT,
                        status TEXT,
                        confidence REAL,
                        start_time TEXT,
                        end_time TEXT,
                        payload JSON
                    )
                """)
                cursor.execute("SELECT id, incident, namespace, status, confidence, start_time, end_time FROM investigations ORDER BY start_time DESC")
                for row in cursor.fetchall():
                    results.append({
                        "id": row[0],
                        "incident": row[1],
                        "namespace": row[2],
                        "status": row[3],
                        "confidence": row[4],
                        "start_time": row[5],
                        "end_time": row[6],
                    })
        except Exception:
            pass

        if not results:
            for s in sorted(cls._instances.values(), key=lambda x: x.start_time, reverse=True):
                results.append({
                    "id": s.id,
                    "incident": s.incident,
                    "namespace": s.namespace,
                    "status": s.status.value,
                    "confidence": s.confidence,
                    "start_time": s.start_time.isoformat(),
                    "end_time": s.end_time.isoformat() if s.end_time else None,
                })

        return results
