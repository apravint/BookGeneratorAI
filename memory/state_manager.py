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
        conn = sqlite3.connect(self.db_path)
        try:
            with conn:
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
        finally:
            conn.close()

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
        conn = sqlite3.connect(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO chapter_revisions (chapter_number, draft_text, revision_brief_json, final_text)
                    VALUES (?, ?, ?, ?)
                """, (chapter_number, draft_text, brief_json, final_text))
        finally:
            conn.close()

    def update_dynamic_story_state(
        self,
        story_state: StoryState,
        chapter_number: int,
        chapter_title: str,
        chapter_text: str,
        llm_client = None,
        language: str = "english"
    ) -> StoryState:
        """Parses chapter events to update rolling summary, open plot loops, and character states."""
        is_tamil = language and language.lower() in ["tamil", "ta"]
        summary = f"- Chapter {chapter_number} ({chapter_title}): Narrative progressed through assigned beats."
        
        if llm_client:
            prompt = (
                f"Analyze Chapter {chapter_number}: {chapter_title}.\n"
                f"1. Provide a concise 2-sentence narrative recap.\n"
                f"2. List any newly opened plot loops or unresolved questions.\n\n"
                f"Text excerpt:\n{chapter_text[:1800]}"
            )
            system = "You are a narrative continuity engine. Keep responses concise."
            try:
                response = llm_client.generate_text(prompt, system_prompt=system, max_tokens=300)
                summary = response.strip()
            except Exception:
                pass

        # Update rolling summary
        story_state.story_so_far_summary += f"\n- Chapter {chapter_number} ({chapter_title}): {summary}"
        story_state.current_chapter = chapter_number

        # Track active plot thread
        thread_label = f"Ch.{chapter_number} fallout: {chapter_title}"
        if thread_label not in story_state.active_plot_threads:
            story_state.active_plot_threads.append(thread_label)
            # Cap active threads to avoid prompt bloat
            if len(story_state.active_plot_threads) > 6:
                retired = story_state.active_plot_threads.pop(0)
                story_state.resolved_plot_threads.append(retired)

        self.save_story_state(story_state)
        return story_state

    def _save_key(self, key: str, json_str: str):
        conn = sqlite3.connect(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO state_store (key, json_data)
                    VALUES (?, ?)
                """, (key, json_str))
        finally:
            conn.close()

    def _get_key(self, key: str) -> Optional[str]:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT json_data FROM state_store WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                return row[0]
            return None
        finally:
            conn.close()
