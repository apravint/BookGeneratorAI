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
    CharacterRelation,
    ChapterMemory
)
from generator.json_parser import generate_validated, StructuredOutputError
from prompts.system_prompts import language_directive


class StateManager:
    def __init__(self, db_path: str = "memory/book_state.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
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
        memory = None
        if llm_client:
            memory = self._extract_chapter_memory(story_state, chapter_number, chapter_title, chapter_text, llm_client, language)

        if memory:
            self._apply_chapter_memory(story_state, memory)
            recap = memory.recap
        else:
            recap = "Narrative progressed through assigned beats."
            # Track active plot thread
            thread_label = f"Ch.{chapter_number} fallout: {chapter_title}"
            if thread_label not in story_state.active_plot_threads:
                story_state.active_plot_threads.append(thread_label)

        story_state.chapter_recaps[chapter_number] = recap
        story_state.story_so_far_summary += f"\n- Chapter {chapter_number} ({chapter_title}): {recap}"
        story_state.current_chapter = chapter_number

        self.save_story_state(story_state)
        return story_state

    def _extract_chapter_memory(self, story_state, chapter_number, chapter_title, chapter_text, llm_client, language) -> Optional[ChapterMemory]:
        open_clues = [c.name for c in story_state.foreshadowing_clues if c.status in ["planted", "escalated"]]
        prompt = f"""TASK: chapter memory
Extract what must be remembered from Chapter {chapter_number}: {chapter_title}.
{language_directive(language)}
Open setups you may mark escalated or resolved, using these exact names: {open_clues}
Currently open threads: {story_state.active_plot_threads}

FULL CHAPTER:
{chapter_text}

Return ONLY JSON:
{{"recap": "3-5 sentences: what happened and what changed",
 "opened_threads": [], "closed_threads": [],
 "character_conditions": [{{"character_name": "", "physical_wounds_or_status": [], "inventory_items": [], "emotional_state": "", "current_location": ""}}],
 "relationships": [{{"source_char": "", "target_char": "", "relation_type": "", "affinity_score": 0, "dynamic_status": ""}}],
 "clues_escalated": [], "clues_resolved": [],
 "secrets": [{{"fact": "", "known_by": [], "hidden_from": []}}],
 "discoveries": []}}
"""
        system = "You are a narrative continuity engine. Record only what the text establishes. Never guess."
        validator = lambda m: None if m.recap.strip() else "The recap is empty."
        try:
            return generate_validated(llm_client, prompt, system, ChapterMemory, validator=validator, max_tokens=3000)
        except StructuredOutputError as e:
            print(f"  [Memory Engine Warning] Structured memory unavailable for Chapter {chapter_number}: {e}")
            return None

    def _apply_chapter_memory(self, story_state: StoryState, memory: ChapterMemory):
        for thread in memory.closed_threads:
            if thread in story_state.active_plot_threads:
                story_state.active_plot_threads.remove(thread)
                story_state.resolved_plot_threads.append(thread)
        for thread in memory.opened_threads:
            if thread not in story_state.active_plot_threads:
                story_state.active_plot_threads.append(thread)
        for condition in memory.character_conditions:
            story_state.character_conditions[condition.character_name] = condition
        for rel in memory.relationships:
            self._merge_relation(story_state, rel)
        for clue in story_state.foreshadowing_clues:
            if clue.name in memory.clues_resolved:
                clue.status = "resolved"
            elif clue.name in memory.clues_escalated and clue.status == "planted":
                clue.status = "escalated"
        known = {s.get("fact") for s in story_state.epistemic_secrets}
        story_state.epistemic_secrets.extend(s for s in memory.secrets if s.get("fact") and s.get("fact") not in known)
        story_state.key_discoveries.extend(d for d in memory.discoveries if d not in story_state.key_discoveries)

    @staticmethod
    def _merge_relation(story_state: StoryState, relation: CharacterRelation):
        pair = {relation.source_char.lower(), relation.target_char.lower()}
        for i, existing in enumerate(story_state.character_relationships):
            if {existing.source_char.lower(), existing.target_char.lower()} == pair:
                story_state.character_relationships[i] = relation
                return
        story_state.character_relationships.append(relation)

    def save_json(self, key: str, value) -> None:
        """Stores a checkpoint such as in-progress scenes or the book brief."""
        self._save_key(key, json.dumps(value, ensure_ascii=False))

    def load_json(self, key: str, default=None):
        data = self._get_key(key)
        return json.loads(data) if data else default

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
