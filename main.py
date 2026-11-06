#!/usr/bin/env python3
"""
BookGenerator AI Engine - Command Line Interface
Runs the multi-agent pipeline: brief, world, cast, outline, scene drafting, editorial revision,
whole-book release review, publishing kit and DOCX/EPUB compilation.
"""

import argparse
import os
from generator.llm_client import LlmClient
from pipeline import BookConfig, BookPipeline, book_dir_for


def main():
    parser = argparse.ArgumentParser(description="BookGenerator AI: multi-agent manuscript generation engine.")
    parser.add_argument("--title", "-t", required=True, help="Title of the book")
    parser.add_argument("--concept", "-c", default="", help="Seed concept. The more specific and original, the better the book")
    parser.add_argument("--genre", "-g", default="auto", help="Genre: fiction, romance, thriller, business, self-help, technical, non-fiction, tamil_historical, tamil_kavithai, tamil_thirukkural, tamil_fiction")
    parser.add_argument("--author", "-a", default="Pravin Tamilan", help="Author name (default: 'Pravin Tamilan')")
    parser.add_argument("--language", "-l", default="english", choices=["english", "tamil"], help="Target language (default: english)")
    parser.add_argument("--tamil", action="store_true", help="Shortcut for --language tamil")
    parser.add_argument("--provider", "-p", default=None, choices=["auto", "ollama", "jev", "openai", "gemini", "anthropic"], help="LLM provider (default: auto-detected from environment)")
    parser.add_argument("--model", "-m", default=None, help="Model name")
    parser.add_argument("--editor-provider", default=None, choices=["ollama", "openai", "gemini", "anthropic"], help="Provider for the editor that scores chapters (default: same as --provider)")
    parser.add_argument("--editor-model", default=None, help="Model for the editor that scores chapters. A different, stronger model judges more honestly")
    parser.add_argument("--ollama-url", default="http://localhost:11434", help="Ollama server URL")
    parser.add_argument("--chapters", "-n", type=int, default=24, help="Number of chapters (default: 24)")
    parser.add_argument("--scenes-per-chapter", type=int, default=4, help="Scenes in each chapter (default: 4)")
    parser.add_argument("--target-words", type=int, default=80000, help="Whole-book word target (default: 80000)")
    parser.add_argument("--max-revisions", type=int, default=2, help="Max revision passes per chapter (default: 2)")
    parser.add_argument("--opening-candidates", type=int, default=3, help="Competing drafts of the book's first scene (default: 3)")
    parser.add_argument("--output", "-o", default=None, help="Output .docx path (default: inside the book's directory)")
    parser.add_argument("--epub", default=None, help="Output .epub path (default: next to the .docx)")
    parser.add_argument("--cover", default=None, help="Cover image (.jpg) for the EPUB")
    parser.add_argument("--subtitle", default=None, help="Subtitle for the title page")
    parser.add_argument("--isbn", default=None, help="Your ISBN. Omitted when not provided")
    parser.add_argument("--publisher", default=None, help="Publisher or imprint name. Omitted when not provided")
    parser.add_argument("--year", default=None, help="Copyright year (default: current year)")
    parser.add_argument("--dedication", default=None, help="Dedication text. Omitted when not provided")
    parser.add_argument("--author-bio", default=None, help="About the Author text. Omitted when not provided")
    parser.add_argument("--reset", "-r", action="store_true", help="Delete this book's saved progress and start it over. Other books are untouched")
    parser.add_argument("--export-cards", default=None, help="Directory to export portable character cards and lorebook JSON")
    parser.add_argument("--import-lorebook", default=None, help="Lorebook JSON pack to import World Bible & Characters from")
    args = parser.parse_args()

    language = "tamil" if args.tamil else args.language

    resolved_provider = args.provider
    if not resolved_provider or resolved_provider == "auto":
        resolved_provider = "gemini" if (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")) else "ollama"

    llm_client = LlmClient(provider=resolved_provider, model=args.model, ollama_url=args.ollama_url)
    editor_llm = None
    if args.editor_provider or args.editor_model:
        editor_llm = LlmClient(provider=args.editor_provider or resolved_provider, model=args.editor_model, ollama_url=args.ollama_url)

    print("\n" + "=" * 80)
    print("  BOOKGENERATOR AI - MULTI-AGENT PIPELINE")
    print("=" * 80)
    print(f" Title:        {args.title}")
    print(f" Author:       {args.author}")
    print(f" Genre:        {args.genre.upper()}")
    print(f" Language:     {language.upper()}")
    print(f" Provider:     {llm_client.provider.upper()}")
    print(f" Model:        {llm_client.model}")
    if editor_llm:
        print(f" Editor:       {editor_llm.provider.upper()} / {editor_llm.model}")
    print(f" Plan:         {args.chapters} chapters, {args.scenes_per_chapter} scenes each, {args.target_words:,} words")
    print(f" Book Folder:  {book_dir_for(args.title)}")
    print("=" * 80 + "\n")

    publishing = {
        key: value for key, value in {
            "subtitle": args.subtitle, "isbn": args.isbn, "publisher": args.publisher,
            "year": args.year, "dedication": args.dedication, "author_bio": args.author_bio,
        }.items() if value
    }
    config = BookConfig(
        title=args.title, author=args.author, concept=args.concept, genre=args.genre, language=language,
        chapters=args.chapters, scenes_per_chapter=args.scenes_per_chapter, target_words=args.target_words,
        max_revisions=args.max_revisions, opening_candidates=args.opening_candidates,
        output=args.output, epub=args.epub, cover=args.cover, reset=args.reset,
        export_cards=args.export_cards, import_lorebook=args.import_lorebook, publishing=publishing,
    )
    BookPipeline(config, llm_client, editor_llm=editor_llm).run()


if __name__ == "__main__":
    main()
