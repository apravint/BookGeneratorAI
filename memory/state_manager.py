"""
State Manager Module - Local SQLite & JSON State Persistence
Maintains World Bible, Character Registries, Master Outline, and Story State across agent executions.
"""

import json
import sqlite3
import os
from typing import Optional
from schemas.models import (
    WorldBible,
    CharacterRegistry,
    MasterOutline,
    StoryState,
    RevisionBrief
)


class StateManager:
    def __init__(self, db_path: str = "memory/book_state.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS state_store (
                    key TEXT PRIMARY KEY,
                    json_data TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chapter_revisions (
                    chapter_number INTEGER PRIMARY KEY,
                    draft_text TEXT NOT NULL,
                    revision_brief_json TEXT,
                    final_text TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def save_world_bible(self, bible: WorldBible):
        self._save_key("world_bible", bible.model_dump_json())

    def get_world_bible(self) -> Optional[WorldBible]:
        data = self._get_key("world_bible")
        if data:
            return WorldBible.model_validate_json(data)
        return None

    def save_character_registry(self, registry: CharacterRegistry):
        self._save_key("character_registry", registry.model_dump_json())

    def get_character_registry(self) -> Optional[CharacterRegistry]:
        data = self._get_key("character_registry")
        if data:
            return CharacterRegistry.model_validate_json(data)
        return None

    def save_master_outline(self, outline: MasterOutline):
        self._save_key("master_outline", outline.model_dump_json())

    def get_master_outline(self) -> Optional[MasterOutline]:
        data = self._get_key("master_outline")
        if data:
            return MasterOutline.model_validate_json(data)
        return None

    def save_story_state(self, state: StoryState):
        self._save_key("story_state", state.model_dump_json())

    def get_story_state(self) -> Optional[StoryState]:
        data = self._get_key("story_state")
        if data:
            return StoryState.model_validate_json(data)
        return StoryState()

    def save_chapter_record(self, chapter_number: int, draft_text: str, brief: Optional[RevisionBrief], final_text: str):
        brief_json = brief.model_dump_json() if brief else None
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO chapter_revisions (chapter_number, draft_text, revision_brief_json, final_text)
                VALUES (?, ?, ?, ?)
            """, (chapter_number, draft_text, brief_json, final_text))
            conn.commit()

    def _save_key(self, key: str, json_str: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO state_store (key, json_data)
                VALUES (?, ?)
            """, (key, json_str))
            conn.commit()

    def _get_key(self, key: str) -> Optional[str]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT json_data FROM state_store WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                return row[0]
        return None
