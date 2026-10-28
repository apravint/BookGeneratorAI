"""
Prose Drafter Agent - Phase 2
Writes high-pacing chapter manuscript prose using iterative Beat-by-Beat (Scene) generation.
Prevents context token overflow and produces deep, multi-thousand word chapters per beat schedule.
"""

import re
from schemas.models import WorldBible, CharacterRegistry, ChapterBeat, StoryState, RevisionBrief, SubBeat
from generator.llm_client import LlmClient
from prompts.system_prompts import PROSE_DRAFTER_PROMPT, TAMIL_PROSE_DRAFTER_PROMPT


class ProseDrafterAgent:
    def __init__(self, llm_client: LlmClient):
        self.llm = llm_client

    def draft_chapter(
        self,
        chapter_beat: ChapterBeat,
        world_bible: WorldBible,
        registry: CharacterRegistry,
        story_state: StoryState,
        revision_brief: RevisionBrief = None
    ) -> str:
        is_tamil = getattr(world_bible, 'language', 'english').lower() in ["tamil", "ta"]
        system_prompt = TAMIL_PROSE_DRAFTER_PROMPT if is_tamil else PROSE_DRAFTER_PROMPT
        lang_constraint = "CRITICAL MANDATE: WRITE ALL MANUSCRIPT PROSE 100% IN FLUENT, ELEGANT, GRAMMATICALLY CORRECT TAMIL SCRIPT (தமிழ் எழுத்துக்கள்). DO NOT USE ENGLISH WORDS." if is_tamil else "Write in English."

        # Construct Character Voices Context
        char_voices = "\n".join([
            f"- {c.name} ({c.role}): Tone={c.voice_fingerprint.tone}, Sentence Rhythm={c.voice_fingerprint.sentence_structure}, Taboo Words={c.voice_fingerprint.taboo_phrases}"
            for c in registry.characters
        ])

        # Dynamic Knowledge Graph, Relationships & Foreshadowing Context
        kg_lines = []
        if story_state:
            if story_state.active_plot_threads:
                kg_lines.append(f"* Active Plot Loops: {', '.join(story_state.active_plot_threads[:4])}")
            if getattr(story_state, "character_conditions", None):
                conds = [
                    f"{name}: [Status={cond.physical_wounds_or_status}, Items={cond.inventory_items}, Emotion={cond.emotional_state}]"
                    for name, cond in story_state.character_conditions.items()
                ]
                if conds:
                    kg_lines.append(f"* Character Living State: {'; '.join(conds[:3])}")
            if getattr(story_state, "character_relationships", None):
                rels = [
                    f"{r.source_char} <-> {r.target_char} ({r.relation_type}, Affinity={r.affinity_score}/10, Dynamic='{r.dynamic_status}')"
                    for r in story_state.character_relationships[:4]
                ]
                if rels:
                    kg_lines.append(f"* Active Relationships & Social Dynamics: {'; '.join(rels)}")
            if getattr(story_state, "foreshadowing_clues", None):
                curr_num = chapter_beat.chapter_number
                due = [c for c in story_state.foreshadowing_clues if c.status in ["planted", "escalated"] and c.target_payoff_chapter == curr_num]
                active = [c for c in story_state.foreshadowing_clues if c.status in ["planted", "escalated"] and c.target_payoff_chapter != curr_num]
                if due:
                    due_desc = "; ".join([f"'{d.name}' ({d.description})" for d in due])
                    kg_lines.append(f"* MANDATORY CLUE PAYOFFS FOR THIS CHAPTER: Resolve or expose: {due_desc}")
                if active:
                    active_desc = "; ".join([f"'{a.name}' (Planted Ch.{a.planted_chapter}, due Ch.{a.target_payoff_chapter})" for a in active[:3]])
                    kg_lines.append(f"* Active Background Suspense Hooks: {active_desc}")
            if getattr(story_state, "epistemic_secrets", None):
                secr = [
                    f"'{s.get('fact')}': known to {s.get('known_by')}, HIDDEN from {s.get('hidden_from')}"
                    for s in story_state.epistemic_secrets[:2]
                ]
                if secr:
                    kg_lines.append(f"* Secret/Epistemic Rules: {'; '.join(secr)}")
        knowledge_graph_context = "\n".join(kg_lines) if kg_lines else "* All initial plot threads unfolding normally."

        revision_context = ""
        if revision_brief and not revision_brief.passed_audit:
            revision_context = f"""
=== CRITICS' MANDATORY REVISION DIRECTIVES ===
Overall Directive: {revision_brief.editor_overall_directive}
Continuity Issues to Fix: {[f'{c.location}: {c.description} -> Fix: {c.remedy}' for c in revision_brief.continuity_issues]}
Slop Violations to Remove: {[f'{s.phrase_or_pattern}: {s.reason}' for s in revision_brief.slop_violations]}
"""

        chapter_sections = []
        running_chapter_context = ""
        total_sub_beats = len(chapter_beat.sub_beats)

        genre_voice_guide = ""
        if world_bible.genre in ["psychology_of_money", "money_psychology", "behavioral_finance"] or "psychology" in world_bible.genre.lower() or "psychology" in world_bible.title.lower():
            genre_voice_guide = """
* **Narrative Non-Fiction Voice (Morgan Housel Style):**
  - Channel the masterly, story-driven, observational voice of Morgan Housel (*The Psychology of Money*).
  - Open with or center upon a vivid historical parable, character contrast, or real-world case study.
  - Emphasize human behavior over spreadsheet math: ego, envy, patience, compounding, and sovereignty over time.
  - Deliver timeless, counter-intuitive psychological insights with crisp, punchy prose.
"""

        print(f"  [Agent: Prose Drafter] Drafting Chapter {chapter_beat.chapter_number}: {chapter_beat.title} ({total_sub_beats} sub-beats)...")

        for idx, sub_beat in enumerate(chapter_beat.sub_beats, start=1):
            beat_label = f"{chapter_beat.chapter_number}.{idx}"
            btype = getattr(sub_beat, 'beat_type', 'SCENE_GOAL')
            tension = getattr(sub_beat, 'micro_tension_level', 5)
            subtext = getattr(sub_beat, 'pov_internal_state', 'Focused on scene goal with suppressed doubts.')

            user_prompt = f"""**Role:** You are an elite, award-winning author specializing in {world_bible.genre} genre. Your prose is immersive, realistic, and character-driven.
{lang_constraint}

**Task:** Write Scene Beat {beat_label} (approx. 600-900 words) fulfilling the narrative beats provided below. Do NOT write conversational preambles or meta commentary; write only the specified manuscript prose.

**Context Guidelines (The Codex):**
* **Genre Style Guide:** Genre={world_bible.genre.upper()}. Setting={world_bible.setting_overview}. World Rules={[r.rule_name + ': ' + r.narrative_consequence for r in world_bible.rules[:3]]}
{genre_voice_guide}
* **Active Characters:**
{char_voices}
* **Dynamic Knowledge Graph & State:**
{knowledge_graph_context}
* **Story So Far (Preceding Chapters):**
{story_state.story_so_far_summary[-1200:] if story_state.story_so_far_summary else "This is Chapter 1 - Opening chapter."}

**Scene Continuity So Far (Current Chapter):**
{running_chapter_context[-1500:] if running_chapter_context else "Beginning of Chapter " + str(chapter_beat.chapter_number) + "."}

**Current Scene Micro-Beat to Execute ({beat_label}):**
Chapter {chapter_beat.chapter_number}: {chapter_beat.title}
POV Character: {chapter_beat.pov_character}
Location: {chapter_beat.location}
Dramatic Beat Type: {btype}
Micro-Tension Level: {tension}/10
POV Internal Subtext: {subtext}
Scene Section: {sub_beat.section_number}
Scene Objective: {sub_beat.scene_objective}
Key Interaction / Conflict: {sub_beat.key_interaction}
Sensory & Structural Detail: {sub_beat.sensory_or_structural_detail}
Ending Transition Hook: {sub_beat.ending_hook}
{revision_context}

**Strict Execution Constraints:**
1. **Show, Don't Tell & Deep POV:** Anchor the narrative in concrete sensory details and immediate character action. Ban filter words ("she saw that", "he felt", "noticed that").
2. **Gary Provost Sentence Rhythm:** Relentlessly vary sentence lengths. Mix punchy 2-5 word statements with expansive 25+ word rhythmic sentences. Avoid monotonous mid-length phrasing.
3. **Three-Layer Dialogue:** Characters must speak with distinct voices based on their profiles. Layer spoken lines with unspoken subtext and physical action beats between dialogue.
4. **Dramatic Beat Adherence:** Fulfill the assigned dramatic beat type ({btype}) at tension level {tension}/10.
5. **Language Integrity:** {lang_constraint}
6. **Banish AI Slop:** Strictly forbidden from using generic LLM clichés: "a tapestry of," "a testament to," "shivers down her spine," "ஒரு சான்றாக அமைந்தது", "முதுகெலும்பில் நடுக்கம்", "echoed in the silence".
7. **No Moralizing Conclusions:** End the scene precisely on the final beat provided. Do not append a concluding paragraph that summarizes the scene's emotional weight or hints at the future.
8. **Section Heading:** Start the section with a clean markdown heading: `### {sub_beat.section_number} {sub_beat.scene_objective}`.
"""
            scene_raw = self.llm.generate_text(user_prompt, system_prompt=system_prompt, max_tokens=2048)
            clean_scene = self._post_process_scene(scene_raw, sub_beat)

            words_count = len(clean_scene.split())
            print(f"    -> Drafting Chapter {chapter_beat.chapter_number}/{12} -> Beat {beat_label}/{chapter_beat.chapter_number}.{total_sub_beats} ({words_count} words)...")

            chapter_sections.append(clean_scene)
            running_chapter_context += f"\n\n{clean_scene}"

        full_chapter_text = f"## Chapter {chapter_beat.chapter_number}: {chapter_beat.title}\n\n" + "\n\n".join(chapter_sections)
        return full_chapter_text

    def _post_process_scene(self, raw_text: str, sub_beat: SubBeat) -> str:
        lines = raw_text.split('\n')
        clean_lines = []
        skip_intro = True

        for line in lines:
            s = line.strip()
            if skip_intro:
                if re.match(r'^(okay|here is|i have|based on|sure|certainly|let\'s|below is|in this chapter|i will proceed|i am ready)', s, re.IGNORECASE):
                    continue
                if s.startswith('---'):
                    continue
                if not s:
                    continue
                skip_intro = False

            # Clean meta-prompt leakage
            cleaned = re.sub(r'Sub-section \d+\.\d+:\s*(Execute core objective|Interaction:|Detail:)[^\n]*', '', line, flags=re.IGNORECASE)
            cleaned = re.sub(r'(Core Objective:|Interaction:|Detail:)\s*[^\n]*', '', cleaned, flags=re.IGNORECASE)
            clean_lines.append(cleaned)

        scene_text = "\n".join(clean_lines).strip()
        
        # Ensure section heading is present
        heading_prefix = f"### {sub_beat.section_number}"
        if not scene_text.startswith("###"):
            scene_text = f"{heading_prefix} {sub_beat.scene_objective}\n\n" + scene_text

        return scene_text