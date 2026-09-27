"""
Master Outliner Agent - Phase 1
Constructs 4-Part, 12-Chapter MasterOutline with detailed 6-subsection beat sheets per chapter.
"""

import json
from schemas.models import WorldBible, CharacterRegistry, MasterOutline, ChapterBeat, SubBeat
from generator.llm_client import LlmClient
from generator.blueprint import BookBlueprint
from prompts.system_prompts import MASTER_OUTLINER_PROMPT


class MasterOutlinerAgent:
    def __init__(self, llm_client: LlmClient):
        self.llm = llm_client

    def build_outline(self, world_bible: WorldBible, registry: CharacterRegistry) -> MasterOutline:
        # Utilize generator.blueprint as structural foundation
        bp = BookBlueprint(title=world_bible.title, genre=world_bible.genre)
        chapters = []

        for part in bp.parts:
            part_name = part["part"]
            for chap in part["chapters"]:
                num = chap["number"]
                title = chap["title"]
                focus = chap["focus"]

                sub_beats = []
                section_titles = [
                    "The Inciting Spark",
                    "Rising Tension & Discovery",
                    "Pivotal Turning Point",
                    "Uncovering Hidden Realities",
                    "Escalating Stakes",
                    "Climactic Transition"
                ] if world_bible.genre == "fiction" else [
                    "Strategic Foundations",
                    "Core Execution Mechanics",
                    "Operational Deep-Dive",
                    "Real-World Case Analysis",
                    "Resilience & Risk Mitigation",
                    "Key Executive Takeaways"
                ]

                for sub_idx in range(1, 7):
                    stitle = section_titles[sub_idx - 1]
                    sub_beats.append(SubBeat(
                        section_number=f"{num}.{sub_idx}",
                        scene_objective=f"{stitle} in {title}",
                        characters_present=[c.name for c in registry.characters[:2]],
                        key_interaction=f"Pivotal narrative turning point for {stitle}",
                        sensory_or_structural_detail=f"Atmospheric detail anchored in {world_bible.setting_overview[:40]}",
                        ending_hook=f"Transition hook into section {num}.{sub_idx+1 if sub_idx < 6 else 1}"
                    ))

                chapters.append(ChapterBeat(
                    chapter_number=num,
                    title=title,
                    pov_character=registry.characters[0].name if registry.characters else "Narrator",
                    location=world_bible.setting_overview[:50],
                    core_narrative_arc=focus,
                    sub_beats=sub_beats,
                    target_word_count=3500
                ))

        return MasterOutline(
            title=world_bible.title,
            total_parts=4,
            chapters=chapters,
            pacing_notes="4-Part structure with rising tension, midpoint twist in Chapter 6, all-is-lost in Chapter 8, and resolution in Chapter 12."
        )
