"""
Prose Drafter Agent - Phase 2
Writes chapters scene by scene with verbatim continuity from the preceding prose,
and revises only the scenes editors flag so strong work is never thrown away.
"""

import re
from typing import Callable, List, Optional
from schemas.models import WorldBible, CharacterRegistry, ChapterBeat, StoryState, RevisionBrief, SubBeat, BookBrief, SceneNote
from generator.llm_client import LlmClient
from prompts.system_prompts import PROSE_DRAFTER_PROMPT, TAMIL_PROSE_DRAFTER_PROMPT

SCENE_BREAK = "* * *"
MIN_LENGTH_RATIO = 0.85
MAX_LENGTH_RETRIES = 2
PROSE_TAIL_CHARS = 3000
RECENT_CHAPTERS_IN_FULL = 3
OLDER_RECAP_CHARS = 200
FICTION_CRAFT = """1. **Enter late, leave early:** Start in motion. Cut throat-clearing and arrivals.
2. **Show, Don't Tell & Deep POV:** Anchor the narrative in concrete sensory details and immediate action. Ban filter words ("she saw that", "he felt", "noticed that").
3. **Sentence Rhythm:** Vary sentence lengths because the moment demands it, not on a schedule.
4. **Three-Layer Dialogue:** Characters speak in distinct voices and rarely say exactly what they mean. Use interruptions and evasions. Use action beats between lines.
5. **Specificity:** Prefer the odd, exact detail a reader could not have predicted. Do not reuse images from the preceding text.
6. **No Moralizing Conclusions:** End on action, dialogue or a turn. Never summarize the emotional meaning or hint about the future."""
NONFICTION_CRAFT = """1. **Lead with a story or a surprise:** Open on a specific moment, then earn the idea from it.
2. **Truth:** Never invent statistics, studies, quotations, named people or events. Use only what you are certain is real. If a fact needs checking, write it followed by [VERIFY: what to check]. Label hypothetical examples as hypothetical.
3. **One idea, deeply:** Prefer a single non-obvious insight, developed, over a list of tips.
4. **Direct address:** Write to one intelligent reader. Plain words. No corporate jargon.
5. **Usefulness:** Leave the reader with something they can see or do differently.
6. **No Moralizing Conclusions:** Do not end by restating the point. End on a turn that pulls the reader onward."""


class ProseDrafterAgent:
    def __init__(self, llm_client: LlmClient):
        self.llm = llm_client

    def draft_scenes(
        self,
        chapter_beat: ChapterBeat,
        world_bible: WorldBible,
        registry: CharacterRegistry,
        story_state: StoryState,
        brief: BookBrief,
        existing_scenes: Optional[List[str]] = None,
        on_scene: Optional[Callable[[List[str]], None]] = None,
        previous_chapter_tail: str = "",
        opening_candidates: int = 1,
        choose_opening: Optional[Callable[[List[str]], str]] = None,
    ) -> List[str]:
        scenes = list(existing_scenes or [])
        total = len(chapter_beat.sub_beats)
        print(f"  [Agent: Prose Drafter] Drafting Chapter {chapter_beat.chapter_number}: {chapter_beat.title} ({total} scenes)...")

        for index, sub_beat in enumerate(chapter_beat.sub_beats):
            if index < len(scenes):
                continue
            tail = scenes[-1][-PROSE_TAIL_CHARS:] if scenes else previous_chapter_tail
            prompt = self._scene_prompt(chapter_beat, sub_beat, world_bible, registry, story_state, brief, tail)
            count = opening_candidates if index == 0 and choose_opening else 1
            candidates = [self._write_scene(prompt, chapter_beat, world_bible) for _ in range(count)]
            scene = choose_opening(candidates) if count > 1 else candidates[0]
            scenes.append(scene)
            print(f"    -> Beat {sub_beat.section_number} ({len(scene.split())} words)...")
            if on_scene:
                on_scene(scenes)
        return scenes

    def revise_scene(
        self,
        chapter_beat: ChapterBeat,
        scene_index: int,
        scenes: List[str],
        notes: List[SceneNote],
        revision_brief: RevisionBrief,
        world_bible: WorldBible,
        registry: CharacterRegistry,
        story_state: StoryState,
        brief: BookBrief,
    ) -> str:
        sub_beat = chapter_beat.sub_beats[scene_index]
        note_lines = "\n".join(f"- {n.problem} -> {n.fix}" for n in notes)
        continuity = "\n".join(f"- {c.description} -> {c.remedy}" for c in revision_brief.continuity_issues)
        before = scenes[scene_index - 1][-1500:] if scene_index else ""
        after = scenes[scene_index + 1][:800] if scene_index + 1 < len(scenes) else ""
        prompt = f"""TASK: scene revision
Rewrite the scene below so a demanding editor would keep reading. Keep every plot event and fact. Keep what works; change what the notes name.

Voice guide: {brief.voice_guide}
{self._language_line(world_bible)}
Scene purpose: {sub_beat.scene_objective} / {sub_beat.key_interaction}
Must preserve: {revision_brief.strengths}

EDITOR NOTES:
{note_lines}
{("CONTINUITY FIXES:" + chr(10) + continuity) if continuity else ""}

TEXT JUST BEFORE THIS SCENE:
{before or "(chapter opening)"}

SCENE TO REWRITE:
{scenes[scene_index]}

TEXT JUST AFTER THIS SCENE (must still follow naturally):
{after or "(chapter ending)"}

Return only the rewritten scene prose. No headings, labels or commentary.
"""
        return self._write_scene(prompt, chapter_beat, world_bible)

    def assemble_chapter(self, chapter_beat: ChapterBeat, scenes: List[str], brief: BookBrief, include_part: bool = False, language: str = "english") -> str:
        is_tamil = language.lower() in ["tamil", "ta"]
        label = "அத்தியாயம்" if is_tamil else "Chapter"
        lines = []
        if include_part and chapter_beat.part_title:
            lines.append(f"# {chapter_beat.part_title}\n")
        lines.append(f"## {label} {chapter_beat.chapter_number}: {chapter_beat.title}\n")
        if brief.is_fiction:
            lines.append(f"\n\n{SCENE_BREAK}\n\n".join(scenes))
        else:
            for sub_beat, scene in zip(chapter_beat.sub_beats, scenes):
                heading = sub_beat.heading or sub_beat.scene_objective
                lines.append(f"### {heading}\n\n{scene}\n")
        return "\n".join(lines).strip() + "\n"

    def _write_scene(self, prompt: str, chapter_beat: ChapterBeat, world_bible: WorldBible) -> str:
        is_tamil = self._is_tamil(world_bible)
        system_prompt = TAMIL_PROSE_DRAFTER_PROMPT if is_tamil else PROSE_DRAFTER_PROMPT
        target = self._scene_words(chapter_beat)
        # Tamil script costs roughly twice the tokens per word
        max_tokens = max(2048, target * (6 if is_tamil else 3))
        scene = self._clean_scene(self.llm.generate_text(prompt, system_prompt=system_prompt, max_tokens=max_tokens))
        for _ in range(MAX_LENGTH_RETRIES):
            if len(scene.split()) >= target * MIN_LENGTH_RATIO:
                break
            extended = self.llm.generate_text(
                f"{prompt}\n\nYour last version ran only {len(scene.split())} words. Write the complete scene at about {target} words by deepening the conflict and detail. Do not pad.\n\nLAST VERSION:\n{scene}",
                system_prompt=system_prompt,
                max_tokens=max_tokens,
            )
            extended = self._clean_scene(extended)
            if len(extended.split()) > len(scene.split()):
                scene = extended
        return scene

    def _scene_prompt(self, chapter_beat, sub_beat: SubBeat, world_bible, registry, story_state, brief: BookBrief, tail: str) -> str:
        craft = FICTION_CRAFT if brief.is_fiction else NONFICTION_CRAFT
        return f"""TASK: scene draft
**Role:** You are writing {world_bible.title}, a {world_bible.genre} book.
{self._language_line(world_bible)}

**Book:** {brief.logline}
**Promise to the reader:** {brief.reader_promise}
**Voice guide:** {brief.voice_guide}
**Voice sample (match the voice, never reuse the words):**
{brief.voice_sample}

**Setting:** {world_bible.setting_overview} ({world_bible.time_period})
**World Rules:** {[r.rule_name + ': ' + r.narrative_consequence for r in world_bible.rules]}
**People in this scene:**
{self._cast_context(registry, sub_beat)}
**Story State:**
{self._knowledge_context(chapter_beat, story_state)}
**Story So Far:**
{self._story_so_far(story_state)}

**Prose immediately before this scene (continue seamlessly; do not repeat it):**
{tail or "Nothing yet. This is the first page of the book, the page a browsing reader decides on. Make it impossible to put down."}

**Write this scene ({sub_beat.section_number}, about {self._scene_words(chapter_beat)} words):**
Chapter {chapter_beat.chapter_number}: {chapter_beat.title}
Chapter must achieve: {chapter_beat.core_narrative_arc}
Point of view: {chapter_beat.pov_character}
Location: {chapter_beat.location}
Beat type: {sub_beat.beat_type}; tension {sub_beat.micro_tension_level}/10
Objective: {sub_beat.scene_objective}
The turn: {sub_beat.key_interaction}
Under the surface: {sub_beat.pov_internal_state}
Specific detail: {sub_beat.sensory_or_structural_detail}
End on: {sub_beat.ending_hook}
{self._clue_directive(chapter_beat, story_state)}

**Craft:**
{craft}
7. **Banish AI Slop:** Forbidden: "a tapestry of," "a testament to," "shivers down her spine," "ஒரு சான்றாக அமைந்தது", "முதுகெலும்பில் நடுக்கம்", "echoed in the silence," and the "it wasn't X, it was Y" construction.

Return only the prose. No headings, labels or commentary.
"""

    @staticmethod
    def _scene_words(chapter_beat: ChapterBeat) -> int:
        return chapter_beat.target_word_count // max(len(chapter_beat.sub_beats), 1)

    @staticmethod
    def _is_tamil(world_bible: WorldBible) -> bool:
        return getattr(world_bible, 'language', 'english').lower() in ["tamil", "ta"]

    def _language_line(self, world_bible: WorldBible) -> str:
        if self._is_tamil(world_bible):
            return "CRITICAL MANDATE: WRITE ALL MANUSCRIPT PROSE 100% IN FLUENT, ELEGANT, GRAMMATICALLY CORRECT TAMIL SCRIPT (தமிழ் எழுத்துக்கள்). DO NOT USE ENGLISH WORDS."
        return "Write in English."

    @staticmethod
    def _cast_context(registry: CharacterRegistry, sub_beat: SubBeat) -> str:
        present = {name.lower() for name in sub_beat.characters_present}
        chars = [c for c in registry.characters if c.name.lower() in present] or registry.characters
        return "\n".join(
            f"- {c.name} ({c.role}): Wants={c.core_motivation}; Flaw={c.fatal_flaw}; Tone={c.voice_fingerprint.tone}; "
            f"Rhythm={c.voice_fingerprint.sentence_structure}; Signature={c.voice_fingerprint.frequently_used_terms}; Never says={c.voice_fingerprint.taboo_phrases}"
            for c in chars
        ) or "- Real people and cases only, as named in this scene's objective."

    @staticmethod
    def _story_so_far(story_state: StoryState) -> str:
        if not story_state.chapter_recaps:
            return "This is the opening."
        ordered = sorted(story_state.chapter_recaps.items())
        recent_from = len(ordered) - RECENT_CHAPTERS_IN_FULL
        return "\n".join(
            f"Ch.{num}: {recap if i >= recent_from else recap[:OLDER_RECAP_CHARS]}"
            for i, (num, recap) in enumerate(ordered)
        )

    @staticmethod
    def _knowledge_context(chapter_beat: ChapterBeat, story_state: StoryState) -> str:
        lines = []
        if story_state.active_plot_threads:
            lines.append(f"* Open threads: {'; '.join(story_state.active_plot_threads)}")
        if story_state.character_conditions:
            conds = [
                f"{name}: status={c.physical_wounds_or_status}, holding={c.inventory_items}, feeling={c.emotional_state}, at={c.current_location}"
                for name, c in story_state.character_conditions.items()
            ]
            lines.append(f"* Character state: {'; '.join(conds)}")
        if story_state.character_relationships:
            rels = [f"{r.source_char} <-> {r.target_char} ({r.relation_type}, {r.affinity_score}/10: {r.dynamic_status})" for r in story_state.character_relationships]
            lines.append(f"* Relationships: {'; '.join(rels)}")
        if story_state.epistemic_secrets:
            secrets = [f"'{s.get('fact')}' known to {s.get('known_by')}, hidden from {s.get('hidden_from')}" for s in story_state.epistemic_secrets]
            lines.append(f"* Who knows what: {'; '.join(secrets)}")
        if story_state.key_discoveries:
            lines.append(f"* Already established (do not re-explain): {'; '.join(story_state.key_discoveries[-15:])}")
        return "\n".join(lines) or "* Nothing established yet."

    @staticmethod
    def _clue_directive(chapter_beat: ChapterBeat, story_state: StoryState) -> str:
        by_name = {c.name: c for c in story_state.foreshadowing_clues}
        plant = [f"'{n}' ({by_name[n].description})" for n in chapter_beat.foreshadowing_clues_to_plant if n in by_name]
        pay = [f"'{n}' ({by_name[n].description})" for n in chapter_beat.foreshadowing_clues_to_resolve if n in by_name]
        lines = []
        if plant:
            lines.append(f"This chapter must quietly plant, without drawing attention: {'; '.join(plant)}")
        if pay:
            lines.append(f"This chapter must pay off: {'; '.join(pay)}")
        return "\n".join(lines)

    @staticmethod
    def _clean_scene(raw_text: str) -> str:
        lines = raw_text.strip().split('\n')
        while lines and (lines[0].lstrip().startswith('#') or not lines[0].strip()):
            lines.pop(0)
        text = "\n".join(lines).strip()
        return re.sub(r'\n{3,}', '\n\n', text)
