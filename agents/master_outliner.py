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

    def build_outline(self, world_bible: WorldBible, registry: CharacterRegistry, language: str = "english") -> MasterOutline:
        # Utilize generator.blueprint as structural foundation
        bp = BookBlueprint(title=world_bible.title, genre=world_bible.genre)
        chapters = []
        is_tamil = (language or getattr(world_bible, 'language', 'english')).lower() in ["tamil", "ta"]

        for part in bp.parts:
            part_name = part["part"]
            for chap in part["chapters"]:
                num = chap["number"]
                title = chap["title"]
                focus = chap["focus"]

                sub_beats = []
                if is_tamil:
                    section_titles = [
                        "தொடக்கத் தீப்பொறி (The Inciting Spark)",
                        "எழுச்சி & கண்டுபிடிப்பு (Rising Tension & Discovery)",
                        "முக்கிய திருப்புமுனை (Pivotal Turning Point)",
                        "மறைக்கப்பட்ட உண்மைகள் (Uncovering Hidden Realities)",
                        "உச்சக்கட்டப் பதற்றம் (Escalating Stakes)",
                        "நிறைவுக் களம் (Climactic Transition)"
                    ]
                elif world_bible.genre == "fiction":
                    section_titles = [
                        "The Inciting Spark",
                        "Rising Tension & Discovery",
                        "Pivotal Turning Point",
                        "Uncovering Hidden Realities",
                        "Escalating Stakes",
                        "Climactic Transition"
                    ]
                else:
                    section_titles = [
                        "Strategic Foundations",
                        "Core Execution Mechanics",
                        "Operational Deep-Dive",
                        "Real-World Case Analysis",
                        "Resilience & Risk Mitigation",
                        "Key Executive Takeaways"
                    ]

                for sub_idx in range(1, 7):
                    stitle = section_titles[sub_idx - 1]
                    scene_obj = f"{title} - {stitle}" if is_tamil else f"{stitle} in {title}"
                    key_inter = f"{stitle} - முக்கிய திருப்பம்" if is_tamil else f"Pivotal narrative turning point for {stitle}"
                    sensory = f"சூழல் வர்ணனை: {world_bible.setting_overview[:40]}" if is_tamil else f"Atmospheric detail anchored in {world_bible.setting_overview[:40]}"
                    ending = f"அடுத்த பகுதி {num}.{sub_idx+1 if sub_idx < 6 else 1}-க்கான இணைப்பு" if is_tamil else f"Transition hook into section {num}.{sub_idx+1 if sub_idx < 6 else 1}"

                    sub_beats.append(SubBeat(
                        section_number=f"{num}.{sub_idx}",
                        scene_objective=scene_obj,
                        characters_present=[c.name for c in registry.characters[:2]],
                        key_interaction=key_inter,
                        sensory_or_structural_detail=sensory,
                        ending_hook=ending
                    ))

                chapters.append(ChapterBeat(
                    chapter_number=num,
                    title=title,
                    pov_character=registry.characters[0].name if registry.characters else ("கதைசொல்லி" if is_tamil else "Narrator"),
                    location=world_bible.setting_overview[:50],
                    core_narrative_arc=focus,
                    sub_beats=sub_beats,
                    target_word_count=3500
                ))

        pacing = (
            "4 பாகங்கள் கொண்ட எழுச்சிப் பாதை: 6-ஆம் அத்தியாயத்தில் பெரும் திருப்பம், 8-ஆம் அத்தியாயத்தில் உச்சக்கட்ட சோதனை, 12-ஆம் அத்தியாயத்தில் காவிய முடிவு."
            if is_tamil
            else "4-Part structure with rising tension, midpoint twist in Chapter 6, all-is-lost in Chapter 8, and resolution in Chapter 12."
        )

        return MasterOutline(
            title=world_bible.title,
            total_parts=4,
            chapters=chapters,
            pacing_notes=pacing
        )
