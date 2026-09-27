"""
Writer Engine Module - World-Class Bestseller Edition
Drafts markdown manuscript chapters, epigraphs, praise pages, preface, foreword, glossary, and appendices tailored to ANY book genre with viral engagement hooks.
"""

import os
from .blueprint import BookBlueprint
from .llm_client import LlmClient
from .editor import DevelopmentalEditor

class ChapterWriter:
    def __init__(self, blueprint: BookBlueprint, llm_client: LlmClient, output_dir: str, enable_editor: bool = True, incremental_callback = None):
        self.blueprint = blueprint
        self.llm = llm_client
        self.output_dir = output_dir
        self.enable_editor = enable_editor
        self.incremental_callback = incremental_callback
        self.editor = DevelopmentalEditor(llm_client) if enable_editor else None
        self.preceding_summary = ""
        self.master_outline_summary = self._build_master_outline_summary()
        self.character_and_setting_sheet = self._build_character_and_setting_sheet()
        os.makedirs(self.output_dir, exist_ok=True)

    def _build_master_outline_summary(self) -> str:
        lines = [f"BOOK TITLE: {self.blueprint.title}", f"GENRE: {self.blueprint.genre.upper()}", "MASTER OUTLINE:"]
        for part in self.blueprint.parts:
            lines.append(f"  {part['part']}:")
            for chap in part["chapters"]:
                lines.append(f"    - Chapter {chap['number']}: {chap['title']} ({chap['focus']})")
        return "\n".join(lines)

    def _build_character_and_setting_sheet(self) -> str:
        genre = self.blueprint.genre
        if genre == "fiction":
            return f"""CHARACTER & WORLD MATRIX:
- Protagonist: Reluctant visionary driven by core values, navigating {self.blueprint.domain}.
- Antagonist: Systemic opposing force / formidable adversary challenging the protagonist.
- Setting: Immersive, high-stakes environment centered around {self.blueprint.domain}.
- Key Motifs: Sacrifice, destiny, transformation, unyielding resolve."""
        elif genre == "business":
            return f"""EXECUTIVE STRATEGY MATRIX:
- Subject: {self.blueprint.title} ({self.blueprint.domain}).
- Core Frameworks: Unit economics, competitive moats, leadership mental models, data intelligence.
- Case Studies: Fortune 500 turnarounds, unicorn scaling, operational failure post-mortems."""
        elif genre == "self-help":
            return f"""TRANSFORMATION MATRIX:
- Target Mindset: From limiting beliefs to unshakeable self-mastery in {self.blueprint.domain}.
- Core Pillars: Habit design, emotional resilience, deep focus, long-term vitality."""
        else:
            return f"""ARCHITECTURAL & SYSTEM MATRIX:
- Core Domain: {self.blueprint.domain}.
- Core Principles: Concurrency, scalability, resilience, zero trust governance, native tool integration.
- Target Metric: Sub-millisecond latency, zero downtime, modular extensibility."""

    def _summarize_chapter(self, chap_num: int, chap_title: str, content: str) -> str:
        prompt = f"""Provide a concise 3-bullet summary of Chapter {chap_num}: {chap_title}.
Focus on key plot shifts, major decisions, character arc developments, or technical breakthroughs that happened in this chapter.
Keep total summary under 120 words.

Chapter Text (Excerpt):
{content[:2000]}
"""
        return self.llm.generate_text(prompt, system_prompt="You are a narrative continuity editor creating rolling context summaries.")

    def generate_all_chapters(self):
        generated_files = []

        # 0. Praise & Endorsements Page
        praise_file = os.path.join(self.output_dir, "praise.md")
        print("Drafting Praise & Critical Acclaim Page...")
        with open(praise_file, "w", encoding="utf-8") as f:
            f.write(self._draft_praise())
        generated_files.append(praise_file)

        # 1. Epigraph Page
        epigraph_file = os.path.join(self.output_dir, "epigraph.md")
        print("Drafting Epigraph & Dedication Page...")
        with open(epigraph_file, "w", encoding="utf-8") as f:
            f.write(self._draft_epigraph())
        generated_files.append(epigraph_file)

        # 2. Preface
        preface_file = os.path.join(self.output_dir, "preface.md")
        print("Drafting Preface & Readers' Guide...")
        with open(preface_file, "w", encoding="utf-8") as f:
            f.write(self._draft_preface())
        generated_files.append(preface_file)

        # 3. Foreword
        foreword_file = os.path.join(self.output_dir, "foreword.md")
        print("Drafting Foreword...")
        with open(foreword_file, "w", encoding="utf-8") as f:
            f.write(self._draft_foreword())
        generated_files.append(foreword_file)

        # 4. Chapters 1-12 with Iterative Rolling Context Memory & Local Disk Persistence
        for part_info in self.blueprint.parts:
            part_title = part_info["part"]
            for chap_info in part_info["chapters"]:
                chap_num = chap_info["number"]
                chap_title = chap_info["title"]
                chap_focus = chap_info["focus"]

                filename = f"chapter_{chap_num:02d}.md"
                filepath = os.path.join(self.output_dir, filename)

                print(f"\n[Iterative Generation] Drafting Chapter {chap_num}: {chap_title}...")

                raw_content = self._draft_chapter(part_title, chap_num, chap_title, chap_focus)
                
                # Apply Developmental Editor Pass if enabled
                if self.enable_editor and self.editor:
                    print(f"  [Editorial Pass] Refining prose, hooks, and pacing for Chapter {chap_num}...")
                    final_content = self.editor.edit_chapter(chap_title, raw_content, self.blueprint.genre)
                else:
                    final_content = raw_content

                # Local Disk File Writer Tool Integration
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(final_content)
                print(f"  ✓ [Local File Writer] Persisted {filename} directly to hard drive.")

                generated_files.append(filepath)

                # Summarize Chapter for Preceding Rolling Context Payload for Chapter N+1
                print(f"  [Context Memory] Summarizing Chapter {chap_num} for rolling context window...")
                self.preceding_summary = self._summarize_chapter(chap_num, chap_title, final_content)

                # Trigger Incremental Compilation Callback if provided
                if self.incremental_callback:
                    try:
                        self.incremental_callback(chap_num)
                    except Exception as ex:
                        print(f"  [Incremental Sync Warning] Callback failed: {ex}")

        # 5. Appendices
        appendices = [
            ("appendix_a.md", f"Appendix A: Comprehensive Master Reference Guide for {self.blueprint.title}"),
            ("appendix_b.md", f"Appendix B: Deep Case Studies & Structural Playbooks"),
            ("appendix_c.md", f"Appendix C: Executive Framework Checklists & Resources")
        ]

        for app_file, app_title in appendices:
            filepath = os.path.join(self.output_dir, app_file)
            print(f"Drafting {app_title}...")
            content = f"# {app_title}\n\n" + self.llm.generate_text(f"Generate exhaustive reference content for {app_title} in the context of {self.blueprint.title}.")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            generated_files.append(filepath)

        # 6. Technical Glossary
        glossary_file = os.path.join(self.output_dir, "glossary.md")
        print("Drafting Technical Glossary & Terminology Guide...")
        with open(glossary_file, "w", encoding="utf-8") as f:
            f.write(self._draft_glossary())
        generated_files.append(glossary_file)

        return generated_files

    def _draft_praise(self) -> str:
        return f"""# Praise for {self.blueprint.title}

> “A masterwork of extraordinary vision and clarity. Pravin Tamilan has written what will undoubtedly be remembered as the definitive guide on {self.blueprint.domain}. Unputdownable from page one.”
> 
> — **The Global Architecture & Literary Review**

> “Required reading for every executive, engineer, and strategic thinker. Pravin synthesizes complex concepts into an unforgettable, transformative narrative.”
> 
> — **Dr. Marcus Vance**, Principal Fellow, Enterprise Systems Institute

> “An absolute tour de force. Equal parts gripping, intellectually rigorous, and profoundly practical. This book sets a new standard for excellence.”
> 
> — **Elena Rostova**, Managing Director, Global Technology Strategy
"""

    def _draft_epigraph(self) -> str:
        return f"""# Epigraph & Dedication

## Dedication
*To curious minds, leaders, and readers everywhere who dare to explore new horizons, challenge legacy paradigms, and master the art of {self.blueprint.domain}.*

---

> “The difficulty lies, not in the new ideas, but in escaping from the old ones, which ramify, for those brought up as most of us have been, into every corner of our minds.”
> 
> — **John Maynard Keynes**
"""

    def _draft_preface(self) -> str:
        return f"""# Preface & Readers' Guide

> “The secret to extraordinary impact is not discovering something new, but seeing what everyone else has missed.”

## Preface
Every great story, framework, or paradigm shift begins with a single realization. **{self.blueprint.title}** was written to explore the deepest dimensions of {self.blueprint.domain}.

Whether you are reading this as a practitioner, a strategic thinker, or an avid reader seeking an immersive narrative, this book is crafted to deliver profound insights, actionable knowledge, and lasting impact.

---

## How to Read This Book
This manuscript is organized into four distinct parts designed to guide your journey:

- **Part I: Foundations and Origins (Chapters 1–3)**
- **Part II: Deep Explorations & Core Dynamics (Chapters 4–6)**
- **Part III: Transformation, Applications & Pivotal Moments (Chapters 7–9)**
- **Part IV: Horizons, Legacy & Future Mastery (Chapters 10–12)**

---

## Target Audience
Designed for readers, leaders, and thinkers seeking comprehensive mastery over {self.blueprint.domain}.
"""

    def _draft_foreword(self) -> str:
        return f"""# Foreword

> “True innovation happens at the intersection of deep mastery and unyielding curiosity.”

**{self.blueprint.title}** represents a landmark achievement. Grounded in deep expertise and vivid storytelling, this volume establishes a definitive blueprint for understanding {self.blueprint.domain}.

*— Executive Editorial & Review Board*
"""

    def _draft_glossary(self) -> str:
        return f"""# Key Concepts & Glossary

## Terminology Guide for {self.blueprint.title}

### Core Catalyst
The initial event or fundamental principle that sets the primary trajectory of {self.blueprint.domain} in motion.

### Strategic Leverage
The key mechanisms or habits that amplify impact while minimizing friction.

### Resilience Vector
The capacity of a system, character, or organization to recover, adapt, and thrive in the face of disruption.

### Paradigm Shift
A fundamental change in the basic concepts and experimental practices of a discipline or narrative.
"""

    def _draft_chapter(self, part_title: str, chap_num: int, chap_title: str, chap_focus: str) -> str:
        genre = self.blueprint.genre

        context_payload = f"""=== MASTER BOOK OUTLINE ===
{self.master_outline_summary}

=== GLOBAL CHARACTER & CONCEPT MATRIX ===
{self.character_and_setting_sheet}

=== PRECEDING CHAPTER SUMMARY (CHAPTER {chap_num - 1}) ===
{self.preceding_summary if self.preceding_summary else "This is Chapter 1 - The opening chapter."}
"""

        if genre == "fiction":
            system_prompt = f"You are a #1 New York Times Bestselling Fiction Author writing an unforgettable epic novel titled '{self.blueprint.title}'. Write with gripping hooks, sensory descriptions, unforgettable character dialogue, high-stakes tension, and memorable quotes."
            user_prompt = f"""{context_payload}

=== TARGET INSTRUCTION ===
Write Chapter {chap_num}: {chap_title}
Part: {part_title}
Focus: {chap_focus}

Requirements:
1. Maintain strict continuity with the Preceding Chapter Summary above.
2. Start with an irresistible, high-stakes opening sentence hook.
3. Write 6 complete sub-sections (### {chap_num}.1, ### {chap_num}.2, ### {chap_num}.3, ### {chap_num}.4, ### {chap_num}.5, ### {chap_num}.6).
4. Include 2 viral quote blockquotes (> "Quote") that readers will share on social media.
5. Write realistic dialogue blocks between key characters.
6. Conclude with a page-turning cliffhanger.
"""
        elif genre == "business":
            system_prompt = f"You are a #1 Wall Street Journal Bestselling Business Author writing an unputdownable book titled '{self.blueprint.title}'."
            user_prompt = f"""{context_payload}

=== TARGET INSTRUCTION ===
Write Chapter {chap_num}: {chap_title}
Part: {part_title}
Focus: {chap_focus}

Requirements:
1. Maintain strict continuity with the Preceding Chapter Summary above.
2. Start with a captivating business question or story hook.
3. Write 6 complete sub-sections (### {chap_num}.1, ### {chap_num}.2, ### {chap_num}.3, ### {chap_num}.4, ### {chap_num}.5, ### {chap_num}.6).
4. Include 2 viral leadership quote blockquotes (> "Quote").
5. Include corporate case studies and structured strategy tables.
"""
        elif genre == "self-help":
            system_prompt = f"You are a world-renowned #1 Bestselling Self-Help Author writing a life-changing book titled '{self.blueprint.title}'."
            user_prompt = f"""{context_payload}

=== TARGET INSTRUCTION ===
Write Chapter {chap_num}: {chap_title}
Part: {part_title}
Focus: {chap_focus}

Requirements:
1. Maintain strict continuity with the Preceding Chapter Summary above.
2. Start with a deeply resonant opening hook.
3. Write 6 complete sub-sections (### {chap_num}.1, ### {chap_num}.2, ### {chap_num}.3, ### {chap_num}.4, ### {chap_num}.5, ### {chap_num}.6).
4. Include 2 powerful quote blockquotes (> "Quote").
5. Include habit design frameworks and reflection prompts.
"""
        else:
            system_prompt = f"You are a #1 Bestselling Author writing a masterwork titled '{self.blueprint.title}'."
            user_prompt = f"""{context_payload}

=== TARGET INSTRUCTION ===
Write Chapter {chap_num}: {chap_title}
Part: {part_title}
Focus: {chap_focus}

Requirements:
1. Maintain strict continuity with the Preceding Chapter Summary above.
2. Start with an arresting opening sentence.
3. Write 6 complete sub-sections (### {chap_num}.1, ### {chap_num}.2, ### {chap_num}.3, ### {chap_num}.4, ### {chap_num}.5, ### {chap_num}.6).
4. Include 2 viral takeaway blockquotes (> "Quote").
5. Include detailed diagrams or data tables.
"""

        content = self.llm.generate_text(user_prompt, system_prompt)
        return f"# {part_title}\n\n## Chapter {chap_num}: {chap_title}\n\n" + content
