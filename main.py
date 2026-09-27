#!/usr/bin/env python3
"""
BookGenerator AI Engine v4.0 - Multi-Agent Adversarial Pipeline
Hierarchical Multi-Agent Architecture with Context Isolation, Iterative Beat-by-Beat Drafting,
Adversarial Anti-Slop Critics, Database Reset Flag, and Local Ollama Integration.
"""

import argparse
import os
import sys
import glob
from generator.llm_client import LlmClient
from memory.state_manager import StateManager
from schemas.models import StoryState
from agents.world_builder import WorldBuilderAgent
from agents.character_architect import CharacterArchitectAgent
from agents.master_outliner import MasterOutlinerAgent
from agents.prose_drafter import ProseDrafterAgent
from agents.critics import MasterAdversarialReviewer
from tools.file_writer import FileWriterTool


def reset_environment(db_path: str = "memory/book_state.db", output_dir: str = "output"):
    """Wipes state database and cleans output directory to prevent state corruption."""
    print("  [Environment Reset] Wiping state database and cleaning output files...")
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"  ✓ Database file '{db_path}' removed.")
        except Exception as e:
            print(f"  ⚠️ Warning removing database: {e}")

    if os.path.exists(output_dir):
        for f in glob.glob(os.path.join(output_dir, "*.md")) + glob.glob(os.path.join(output_dir, "*.docx")):
            try:
                os.remove(f)
                print(f"  ✓ Output file '{os.path.basename(f)}' cleaned.")
            except Exception as e:
                print(f"  ⚠️ Warning cleaning file '{f}': {e}")


def main():
    parser = argparse.ArgumentParser(
        description="BookGenerator AI v4.0: Production-Grade Multi-Agent Manuscript Generation Engine."
    )
    parser.add_argument("--title", "-t", required=True, help="Title of the book")
    parser.add_argument("--concept", "-c", default="", help="Seed concept or prompt for the book")
    parser.add_argument("--genre", "-g", default="auto", help="Genre: fiction, romance, business, self-help, technical, non-fiction")
    parser.add_argument("--author", "-a", default="Pravin Tamilan", help="Author Name (default: 'Pravin Tamilan')")
    parser.add_argument("--provider", "-p", default="ollama", choices=["ollama", "openai", "gemini", "anthropic"])
    parser.add_argument("--model", "-m", default="deepseek-r1:latest", help="Model name (e.g. deepseek-r1:latest, gpt-4o)")
    parser.add_argument("--ollama-url", default="http://localhost:11434", help="Ollama server URL")
    parser.add_argument("--max-revisions", type=int, default=1, help="Max adversarial critic revision loops per chapter")
    parser.add_argument("--output", "-o", default="Generated_Book.docx", help="Output .docx file path")
    parser.add_argument("--reset", "-r", action="store_true", help="Reset state database and output directory before run")

    args = parser.parse_args()

    concept = args.concept or args.title

    if args.reset:
        reset_environment(db_path="memory/book_state.db", output_dir="output")

    print("\n" + "=" * 80)
    print("  BOOKGENERATOR AI v4.0 - PRODUCTION-GRADE MULTI-AGENT PIPELINE")
    print("=" * 80)
    print(f" Title:        {args.title}")
    print(f" Author:       {args.author}")
    print(f" Genre:        {args.genre.upper()}")
    print(f" Provider:     {args.provider.upper()}")
    print(f" Ollama URL:   {args.ollama_url}")
    print(f" Model:        {args.model}")
    print(f" Output File:  {args.output}")
    print(f" Reset Flag:   {args.reset}")
    print("=" * 80 + "\n")

    # 1. Initialize Clients & State Manager
    llm_client = LlmClient(
        provider=args.provider,
        model=args.model,
        ollama_url=args.ollama_url
    )
    state_mgr = StateManager(db_path="memory/book_state.db")
    file_writer = FileWriterTool(output_dir="output")

    # 2. PHASE 1: Foundation (Architect Agents)
    print("PHASE 1: Foundation Setup (Architect Agents)...")
    
    world_builder = WorldBuilderAgent(llm_client)
    print("  [Agent: World Builder] Generating structured World Bible...")
    world_bible = world_builder.build_world(seed_title=args.title, seed_concept=concept, genre=args.genre)
    state_mgr.save_world_bible(world_bible)
    print(f"  ✓ World Bible Created: '{world_bible.title}' ({len(world_bible.rules)} hard rules defined).")

    char_architect = CharacterArchitectAgent(llm_client)
    print("  [Agent: Character Architect] Developing Character Registry & Voice Fingerprints...")
    character_registry = char_architect.build_characters(world_bible, author_name=args.author)
    state_mgr.save_character_registry(character_registry)
    print(f"  ✓ Character Registry Created: {len(character_registry.characters)} characters initialized.")

    outliner = MasterOutlinerAgent(llm_client)
    print("  [Agent: Master Outliner] Generating 4-Part, 12-Chapter Beat Sheets...")
    master_outline = outliner.build_outline(world_bible, character_registry)
    state_mgr.save_master_outline(master_outline)
    print(f"  ✓ Master Outline Created: {len(master_outline.chapters)} chapter beat sheets scaffolded.")

    # 3. PHASE 2 & 3: Execution & Adversarial Revision Loop
    print("\nPHASE 2 & 3: Execution & Adversarial Revision Loop...")
    drafter = ProseDrafterAgent(llm_client)
    reviewer = MasterAdversarialReviewer(llm_client)
    story_state = state_mgr.get_story_state()

    total_chapters = len(master_outline.chapters)

    for chapter_beat in master_outline.chapters:
        chap_num = chapter_beat.chapter_number
        print(f"\n--------------------------------------------------------------------------------")
        print(f"CHAPTER {chap_num}/{total_chapters}: {chapter_beat.title}")
        print(f"--------------------------------------------------------------------------------")

        revision_brief = None
        final_chapter_text = ""

        for rev in range(args.max_revisions + 1):
            if rev > 0:
                print(f"  [Agent: Prose Drafter] Executing Revision Loop {rev}/{args.max_revisions} based on Critics' Brief...")

            draft_text = drafter.draft_chapter(
                chapter_beat=chapter_beat,
                world_bible=world_bible,
                registry=character_registry,
                story_state=story_state,
                revision_brief=revision_brief
            )

            # Adversarial Critic Loop
            print(f"  [Agent: Adversarial Critics] Auditing Chapter {chap_num} for Continuity & Anti-Slop Tropes...")
            revision_brief = reviewer.evaluate_chapter(
                chapter_beat=chapter_beat,
                chapter_text=draft_text,
                world_bible=world_bible,
                registry=character_registry,
                story_state=story_state
            )

            if revision_brief.passed_audit:
                print(f"  ✓ [Critics Approval] Chapter {chap_num} passed adversarial audit clean!")
                final_chapter_text = draft_text
                break
            else:
                print(f"  ⚠️  [Critics Feedback] Found {len(revision_brief.continuity_issues)} continuity issue(s) & {len(revision_brief.slop_violations)} slop violation(s).")
                final_chapter_text = draft_text

        chap_words = len(final_chapter_text.split())
        print(f"  ✓ Chapter {chap_num} Finalized: Total Word Count = {chap_words} words.")

        # Persist Finalized Chapter to Disk
        md_file = file_writer.write_markdown_chapter(chap_num, final_chapter_text)
        print(f"  ✓ [Local File Writer] Chapter {chap_num} saved to: {md_file}")

        state_mgr.save_chapter_record(chap_num, draft_text, revision_brief, final_chapter_text)

        # Dynamic Story State Summarization for Rolling Context Window
        print(f"  [Memory Engine] Updating Story So Far memory block for Chapter {chap_num}...")
        summary_prompt = f"Provide a concise 3-bullet narrative recap of Chapter {chap_num}: {chapter_beat.title}.\nText snippet:\n{final_chapter_text[:1500]}"
        try:
            chap_summary = llm_client.generate_text(summary_prompt, system_prompt="You are a narrative continuity summarizer.")
        except Exception:
            chap_summary = f"- Chapter {chap_num} ({chapter_beat.title}): Key events unfolded as planned."

        story_state.story_so_far_summary += f"\n- Chapter {chap_num} ({chapter_beat.title}): {chap_summary.strip()}"
        story_state.current_chapter = chap_num
        state_mgr.save_story_state(story_state)

        # Live Incremental Disk Compilation Bridge
        print(f"  [Disk Sync] Updating live .docx output on hard drive...")
        try:
            file_writer.compile_docx(
                title=args.title,
                domain=concept,
                author=args.author,
                docx_path=args.output
            )
            print(f"  ✓ [Disk Sync] Live document '{os.path.basename(args.output)}' updated.")
        except Exception as ex:
            print(f"  [Disk Sync Warning] Document update skipped: {ex}")

    # 4. Final Master Export
    print("\n" + "=" * 80)
    print("PHASE 4: Finalizing Commercial Publication Compilation...")
    file_writer.compile_docx(
        title=args.title,
        domain=concept,
        author=args.author,
        docx_path=args.output
    )
    print(f"🎉 SUCCESS: Multi-Agent Commercial Book successfully generated: {os.path.abspath(args.output)}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
