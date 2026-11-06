"""
Book Pipeline
The single end-to-end workflow behind the CLI, web server and Streamlit studio.
Each book lives in its own directory, so books can never overwrite or resume into one another.
"""

import os
import re
import shutil
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict
from pydantic import BaseModel, Field

from generator.blueprint import BookBlueprint
from generator.json_parser import generate_validated, StructuredOutputError
from generator.llm_client import LlmClient
from memory.state_manager import StateManager
from schemas.models import BookBrief, RevisionBrief, SceneNote
from agents.book_strategist import BookStrategistAgent
from agents.book_reviewer import BookReviewer
from agents.publishing_kit import PublishingKitAgent
from agents.world_builder import WorldBuilderAgent
from agents.character_architect import CharacterArchitectAgent
from agents.master_outliner import MasterOutlinerAgent
from agents.prose_drafter import ProseDrafterAgent
from agents.critics import MasterAdversarialReviewer
from prompts.system_prompts import FACT_CHECK_PROMPT
from tools.card_manager import CardManager
from tools.file_writer import FileWriterTool

BOOKS_ROOT = "books"
BRIEF_KEY = "book_brief"


def slugify(title: str) -> str:
    # Keep letters, combining vowel signs (essential in Tamil) and digits; everything else separates words
    kept = "".join(c if unicodedata.category(c)[0] in "LMN" else "_" for c in title)
    return re.sub(r'_+', '_', kept).strip('_')[:80] or "untitled"


def book_dir_for(title: str, books_root: str = BOOKS_ROOT) -> str:
    return os.path.join(books_root, slugify(title))


@dataclass
class BookConfig:
    title: str
    author: str
    concept: str = ""
    genre: str = "auto"
    language: str = "english"
    chapters: int = 24
    scenes_per_chapter: int = 4
    target_words: int = 80000
    max_revisions: int = 2
    opening_candidates: int = 3
    output: Optional[str] = None
    epub: Optional[str] = None
    cover: Optional[str] = None
    books_root: str = BOOKS_ROOT
    reset: bool = False
    export_cards: Optional[str] = None
    import_lorebook: Optional[str] = None
    publishing: Dict = field(default_factory=dict)  # subtitle, isbn, publisher, year, dedication, author_bio


class OpeningChoice(BaseModel):
    best: int = Field(default=1, description="1-based number of the strongest opening")


class FactClaims(BaseModel):
    claims: List[str] = Field(default_factory=list)


def _rank(brief: RevisionBrief) -> tuple:
    return (brief.passed_audit, brief.craft_score or 0, -len(brief.slop_violations))


class BookPipeline:
    def __init__(self, config: BookConfig, llm_client: LlmClient, editor_llm: Optional[LlmClient] = None):
        self.config = config
        self.llm = llm_client
        # Judging is done by a separate model when given, since models grade their own prose leniently
        self.editor_llm = editor_llm or llm_client
        self.book_dir = book_dir_for(config.title, config.books_root)
        self.manuscript_dir = os.path.join(self.book_dir, "manuscript")
        self.publishing_dir = os.path.join(self.book_dir, "publishing")
        slug = slugify(config.title)
        self.docx_path = config.output or os.path.join(self.book_dir, f"{slug}.docx")
        self.epub_path = config.epub or (os.path.splitext(self.docx_path)[0] + ".epub")

    def run(self) -> dict:
        config = self.config
        if config.reset and os.path.isdir(self.book_dir):
            print(f"  [Environment Reset] Removing '{self.book_dir}'...")
            shutil.rmtree(self.book_dir)
        os.makedirs(self.publishing_dir, exist_ok=True)

        self.state = StateManager(db_path=os.path.join(self.book_dir, "state.db"))
        self.writer = FileWriterTool(output_dir=self.manuscript_dir)

        print("PHASE 1: Foundation Setup (Architect Agents)...")
        self.brief, self.world, self.registry, self.outline = self._build_foundation()

        print("\nPHASE 2 & 3: Execution & Adversarial Revision Loop...")
        self.drafter = ProseDrafterAgent(self.llm)
        self.reviewer = MasterAdversarialReviewer(self.editor_llm)
        self.story_state = self.state.get_story_state()
        if not self.story_state.foreshadowing_clues:
            self.story_state.foreshadowing_clues = list(self.outline.foreshadowing)
            self.state.save_story_state(self.story_state)

        publishing_metadata = dict(config.publishing, is_fiction=self.brief.is_fiction)
        total = len(self.outline.chapters)
        for chapter in self.outline.chapters:
            print("\n" + "-" * 80)
            print(f"CHAPTER {chapter.chapter_number}/{total}: {chapter.title}")
            print("-" * 80)
            record = self.state.get_chapter_record(chapter.chapter_number)
            if record and record.get("final_text"):
                print(f"  ✓ Chapter {chapter.chapter_number} already finalized. Skipping draft phase.")
                continue
            self._write_chapter(chapter)
            self._compile(publishing_metadata, final=False)

        print("\n" + "=" * 80)
        print("PHASE 4: Whole-Book Release Review...")
        chapters, briefs = self._load_finished_chapters()
        result = BookReviewer(self.editor_llm).review(config.title, self.brief, self.story_state, chapters, briefs, config.target_words)
        report_path = BookReviewer.write_report(result, config.title, briefs, self.publishing_dir)
        if not self.brief.is_fiction:
            self._write_fact_check(chapters)

        print("PHASE 5: Publishing Kit & Compilation...")
        kit = PublishingKitAgent(self.llm).build_kit(config.title, config.author, self.brief, self.story_state, config.language)
        PublishingKitAgent.write_kit(kit, self.publishing_dir)
        publishing_metadata["description"] = kit.blurb
        publishing_metadata.setdefault("subtitle", kit.subtitle)
        self._compile(publishing_metadata, final=True)
        self._export_cards()

        result.update(docx=os.path.abspath(self.docx_path), epub=os.path.abspath(self.epub_path), report=os.path.abspath(report_path))
        print(f"\nDOCX: {result['docx']}\nEPUB: {result['epub']}\nReport: {result['report']}")
        print(f"Words: {result['total_words']:,} | Average chapter score: {result['average_craft_score']} | Structure score: {result['arc_score']}")
        if result["ready"]:
            print("Automated checks PASSED. Complete the human steps in the report before publishing.")
        else:
            print(f"NOT READY TO PUBLISH: {len(result['blockers'])} blocker(s), listed in the report.")
            for blocker in result["blockers"]:
                print(f"  - {blocker}")
        print("=" * 80 + "\n")
        return result

    def _build_foundation(self):
        config = self.config
        concept = config.concept or config.title
        genre = BookBlueprint(title=config.title, genre=config.genre).genre if config.genre == "auto" else config.genre

        stored = self.state.load_json(BRIEF_KEY)
        if stored:
            brief = BookBrief.model_validate(stored)
        else:
            print("  [Agent: Book Strategist] Defining reader, promise, hook and voice...")
            brief = BookStrategistAgent(self.llm).build_brief(config.title, concept, genre, config.language)
            self.state.save_json(BRIEF_KEY, brief.model_dump())
        print(f"  ✓ Book Brief: {brief.logline}")

        world = self.state.get_world_bible()
        registry = self.state.get_character_registry()
        if not (world and registry) and config.import_lorebook and os.path.exists(config.import_lorebook):
            print(f"  [Lorebook Import] Loading World Bible and Characters from '{config.import_lorebook}'...")
            world, registry, relations = CardManager.import_lorebook(config.import_lorebook)
            self.state.save_world_bible(world)
            self.state.save_character_registry(registry)
            if relations:
                init_state = self.state.get_story_state()
                init_state.character_relationships.extend(relations)
                self.state.save_story_state(init_state)
        if not world:
            print("  [Agent: World Builder] Generating structured World Bible...")
            world = WorldBuilderAgent(self.llm).build_world(config.title, concept, genre, config.language, brief=brief)
            self.state.save_world_bible(world)
        print(f"  ✓ World Bible: '{world.title}' ({len(world.rules)} hard rules).")
        if not registry:
            print("  [Agent: Character Architect] Developing Character Registry & Voice Fingerprints...")
            registry = CharacterArchitectAgent(self.llm).build_characters(world, config.author, config.language, brief=brief)
            self.state.save_character_registry(registry)
        print(f"  ✓ Character Registry: {len(registry.characters)} characters.")

        outline = self.state.get_master_outline()
        if not outline:
            print("  [Agent: Master Outliner] Generating book plan and scene beats...")
            outline = MasterOutlinerAgent(self.llm).build_outline(
                world, registry, brief, language=config.language, num_chapters=config.chapters,
                scenes_per_chapter=config.scenes_per_chapter, target_words=config.target_words,
            )
            self.state.save_master_outline(outline)
        print(f"  ✓ Master Outline: {len(outline.chapters)} chapters, {len(outline.foreshadowing)} planned setups.")
        return brief, world, registry, outline

    def _write_chapter(self, chapter):
        config = self.config
        num = chapter.chapter_number
        checkpoint = f"scenes_ch_{num}"
        scenes = self.drafter.draft_scenes(
            chapter, self.world, self.registry, self.story_state, self.brief,
            existing_scenes=self.state.load_json(checkpoint, []),
            on_scene=lambda s: self.state.save_json(checkpoint, s),
            previous_chapter_tail=self._previous_tail(num),
            opening_candidates=config.opening_candidates if num == 1 else 1,
            choose_opening=self._choose_opening if num == 1 else None,
        )

        best_scenes, best_brief = list(scenes), None
        for revision in range(config.max_revisions + 1):
            print(f"  [Agent: Adversarial Critics] Auditing Chapter {num} (pass {revision + 1})...")
            text = self._assemble(chapter, scenes)
            brief = self.reviewer.evaluate_chapter(chapter, text, self.world, self.registry, self.story_state, scenes=scenes, brief=self.brief)
            print(f"  Score: {brief.craft_score} | continuity issues: {len(brief.continuity_issues)} | slop: {len(brief.slop_violations)}")
            if best_brief is None or _rank(brief) > _rank(best_brief):
                best_scenes, best_brief = list(scenes), brief
            if brief.passed_audit:
                print(f"  ✓ [Critics Approval] Chapter {num} passed.")
                break
            if revision < config.max_revisions:
                scenes = self._revise(chapter, scenes, brief)
                self.state.save_json(checkpoint, scenes)

        if not best_brief.passed_audit:
            print(f"  ⚠️  Chapter {num} did not pass; keeping its strongest version and flagging it in the release report.")

        final_text = self._assemble(chapter, best_scenes)
        self.writer.write_markdown_chapter(num, final_text)
        self.state.save_chapter_record(num, self._assemble(chapter, scenes), best_brief, final_text)
        self.state.save_json(checkpoint, [])
        print(f"  ✓ Chapter {num} Finalized: {len(final_text.split())} words.")

        print(f"  [Memory Engine] Updating story memory for Chapter {num}...")
        self.story_state = self.state.update_dynamic_story_state(
            self.story_state, num, chapter.title, final_text, llm_client=self.llm, language=config.language
        )

    def _revise(self, chapter, scenes, brief: RevisionBrief) -> List[str]:
        by_scene: Dict[int, List[SceneNote]] = {}
        for note in brief.scene_notes:
            by_scene.setdefault(note.scene, []).append(note)
        if not by_scene:
            # Continuity problems or low scores without located notes: rework the weakest link, the ending
            by_scene[len(scenes)] = [SceneNote(scene=len(scenes), problem=brief.editor_overall_directive, fix="Raise tension and specificity.")]
        revised = list(scenes)
        for scene_number, notes in sorted(by_scene.items()):
            print(f"  [Agent: Prose Drafter] Revising scene {chapter.chapter_number}.{scene_number} ({len(notes)} note(s))...")
            revised[scene_number - 1] = self.drafter.revise_scene(
                chapter, scene_number - 1, revised, notes, brief, self.world, self.registry, self.story_state, self.brief
            )
        return revised

    def _assemble(self, chapter, scenes) -> str:
        chapters = self.outline.chapters
        index = chapters.index(chapter)
        include_part = bool(chapter.part_title) and (index == 0 or chapters[index - 1].part_title != chapter.part_title)
        return self.drafter.assemble_chapter(chapter, scenes, self.brief, include_part=include_part, language=self.config.language)

    def _previous_tail(self, chapter_number: int) -> str:
        record = self.state.get_chapter_record(chapter_number - 1)
        return record["final_text"][-3000:] if record else ""

    def _choose_opening(self, candidates: List[str]) -> str:
        """The opening decides whether a browsing reader buys, so it competes for its place."""
        numbered = "\n\n".join(f"[OPENING {i}]\n{text[:2500]}" for i, text in enumerate(candidates, start=1))
        prompt = f"""TASK: choose opening
Target reader: {self.brief.target_reader}
Promise: {self.brief.reader_promise}
A reader browsing a bookstore reads only these openings. Which makes them buy?

{numbered}

Return ONLY JSON: {{"best": 1}}
"""
        system = "You are an acquiring editor choosing the opening most likely to make a stranger keep reading."
        validator = lambda choice: None if 1 <= choice.best <= len(candidates) else "'best' is out of range."
        try:
            choice = generate_validated(self.editor_llm, prompt, system, OpeningChoice, validator=validator, max_tokens=300)
            print(f"    -> Opening {choice.best} of {len(candidates)} selected.")
            return candidates[choice.best - 1]
        except StructuredOutputError as e:
            print(f"  [Opening Selection Warning] {e}")
            return candidates[0]

    def _load_finished_chapters(self):
        chapters, briefs = {}, {}
        for chapter in self.outline.chapters:
            record = self.state.get_chapter_record(chapter.chapter_number)
            if record:
                chapters[chapter.chapter_number] = record["final_text"]
                briefs[chapter.chapter_number] = RevisionBrief.model_validate_json(record["revision_brief_json"])
        return chapters, briefs

    def _write_fact_check(self, chapters: Dict[int, str]):
        lines = ["# Fact-Check Ledger", "", "AI models invent convincing facts. Verify each claim against a primary source before publishing.", ""]
        for num, text in sorted(chapters.items()):
            prompt = f'TASK: fact check\nList every checkable claim in this chapter.\n\n{text}\n\nReturn ONLY JSON: {{"claims": ["..."]}}'
            lines.append(f"## Chapter {num}\n")
            try:
                claims = generate_validated(self.llm, prompt, FACT_CHECK_PROMPT, FactClaims, max_tokens=3000).claims
                lines += [f"- [ ] {c}" for c in claims] or ["- No checkable claims listed."]
            except StructuredOutputError as e:
                lines.append(f"- [ ] Claim extraction failed; check this chapter by hand. ({e})")
            lines.append("")
        with open(os.path.join(self.publishing_dir, "fact_check.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _compile(self, metadata: dict, final: bool):
        config = self.config
        self.writer.compile_docx(config.title, config.concept, config.author, self.docx_path, config.language, metadata=metadata)
        if final:
            self.writer.compile_epub(config.title, config.author, self.epub_path, config.language, cover_image_path=config.cover, metadata=metadata)

    def _export_cards(self):
        target = self.config.export_cards
        if not target:
            return
        cards_dir = Path(target)
        cards_dir.mkdir(parents=True, exist_ok=True)
        for char in self.registry.characters:
            CardManager.export_character_card(char, cards_dir / f"{char.character_id}_{char.name.replace(' ', '_')}.json")
        CardManager.export_lorebook(
            bible=self.world,
            registry=self.registry,
            relationships=self.story_state.character_relationships,
            output_path=cards_dir / "lorebook.json",
        )
        print(f"  ✓ Exported {len(self.registry.characters)} character cards & lorebook.json to '{target}'.")
