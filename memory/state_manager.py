"""
State Manager Module - Local SQLite & JSON State Persistence
Maintains World Bible, Character Registries, Master Outline, and Story State across agent executions.
"""

import json
import sqlite3
import os
from typing import Optional, List, Dict
from schemas.models import (
    WorldBible,
    CharacterRegistry,
    MasterOutline,
    StoryState,
    RevisionBrief,
    ForeshadowingClue,
    CharacterRelation
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

    def get_chapter_record(self, chapter_number: int) -> Optional[dict]:
        """Retrieves an existing chapter record from the database."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT chapter_number, draft_text, revision_brief_json, final_text, updated_at
                FROM chapter_revisions WHERE chapter_number = ?
            """, (chapter_number,))
            row = cursor.fetchone()
            if row:
                return {
                    "chapter_number": row[0],
                    "draft_text": row[1],
                    "revision_brief_json": row[2],
                    "final_text": row[3],
                    "updated_at": row[4]
                }
            return None
        finally:
            conn.close()

    def get_completed_chapter_numbers(self) -> List[int]:
        """Returns a sorted list of chapter numbers already finalized in the database."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT chapter_number FROM chapter_revisions ORDER BY chapter_number ASC")
            rows = cursor.fetchall()
            return [r[0] for r in rows]
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

    # ---------------------------------------------------------
    # Foreshadowing & Clue Tracking (MuMuAINovel inspired)
    # ---------------------------------------------------------
    def add_foreshadowing_clue(self, story_state: StoryState, clue: ForeshadowingClue) -> StoryState:
        """Adds or updates a foreshadowing clue in the story state."""
        existing = next((c for c in story_state.foreshadowing_clues if c.clue_id == clue.clue_id), None)
        if existing:
            story_state.foreshadowing_clues = [
                clue if c.clue_id == clue.clue_id else c for c in story_state.foreshadowing_clues
            ]
        else:
            story_state.foreshadowing_clues.append(clue)
        self.save_story_state(story_state)
        return story_state

    def get_active_clues(self, story_state: StoryState) -> List[ForeshadowingClue]:
        """Returns all clues that are currently planted or escalated (unresolved)."""
        return [c for c in story_state.foreshadowing_clues if c.status in ["planted", "escalated"]]

    def get_due_clues(self, story_state: StoryState, current_chapter: int) -> List[ForeshadowingClue]:
        """Returns clues scheduled for payoff or climax in or before the current chapter."""
        return [
            c for c in story_state.foreshadowing_clues
            if c.status in ["planted", "escalated"] and c.target_payoff_chapter <= current_chapter
        ]

    def resolve_foreshadowing_clue(
        self,
        story_state: StoryState,
        clue_id: str,
        resolution_notes: str = ""
    ) -> StoryState:
        """Marks a clue as resolved with payoff notes."""
        for clue in story_state.foreshadowing_clues:
            if clue.clue_id == clue_id or clue.name.lower() == clue_id.lower():
                clue.status = "resolved"
                if resolution_notes:
                    clue.payoff_notes = resolution_notes
        self.save_story_state(story_state)
        return story_state

    # ---------------------------------------------------------
    # Dynamic Character & Entity Relationships
    # ---------------------------------------------------------
    def update_character_relation(
        self,
        story_state: StoryState,
        source_char: str,
        target_char: str,
        relation_type: str = "acquaintance",
        affinity_score: int = 0,
        dynamic_status: str = "Neutral dynamic"
    ) -> StoryState:
        """Records or updates dynamic affinity and social tension between two characters."""
        updated = False
        for rel in story_state.character_relationships:
            if (rel.source_char.lower() == source_char.lower() and rel.target_char.lower() == target_char.lower()) or \
               (rel.source_char.lower() == target_char.lower() and rel.target_char.lower() == source_char.lower()):
                rel.relation_type = relation_type
                rel.affinity_score = max(-10, min(10, affinity_score))
                rel.dynamic_status = dynamic_status
                updated = True
                break
        if not updated:
            story_state.character_relationships.append(
                CharacterRelation(
                    source_char=source_char,
                    target_char=target_char,
                    relation_type=relation_type,
                    affinity_score=max(-10, min(10, affinity_score)),
                    dynamic_status=dynamic_status
                )
            )
        self.save_story_state(story_state)
        return story_state

    def get_character_relationships(
        self,
        story_state: StoryState,
        char_name: str
    ) -> List[CharacterRelation]:
        """Returns all relationships involving a specific character."""
        name_lower = char_name.lower()
        return [
            rel for rel in story_state.character_relationships
            if rel.source_char.lower() == name_lower or rel.target_char.lower() == name_lower
        ]

    # ---------------------------------------------------------
    # Non-Linear Chapter DAG & Invalidation
    # ---------------------------------------------------------
    def get_downstream_chapters(self, outline: MasterOutline, modified_chapter: int) -> List[int]:
        """Identifies all chapters that depend on or follow the modified chapter in the causal DAG."""
        downstream = set()
        queue = [modified_chapter]
        while queue:
            curr = queue.pop(0)
            for chap in outline.chapters:
                if curr in getattr(chap, "prerequisite_chapters", []) and chap.chapter_number not in downstream:
                    downstream.add(chap.chapter_number)
                    queue.append(chap.chapter_number)
        return sorted(list(downstream))

    def invalidate_chapter(self, chapter_number: int) -> bool:
        """Deletes a chapter revision record to allow clean regeneration."""
        conn = sqlite3.connect(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM chapter_revisions WHERE chapter_number = ?", (chapter_number,))
                return cursor.rowcount > 0
        finally:
            conn.close()

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
