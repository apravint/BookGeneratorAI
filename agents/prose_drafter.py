"""
Prose Drafter Agent - Phase 2
Writes high-pacing chapter manuscript prose using iterative Beat-by-Beat (Scene) generation.
Prevents context token overflow and produces deep, multi-thousand word chapters per beat schedule.
"""

import re
from schemas.models import WorldBible, CharacterRegistry, ChapterBeat, StoryState, RevisionBrief, SubBeat
from generator.llm_client import LlmClient
from prompts.system_prompts import PROSE_DRAFTER_PROMPT


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
        # Construct Character Voices Context
        char_voices = "\n".join([
            f"- {c.name} ({c.role}): Tone={c.voice_fingerprint.tone}, Sentence Rhythm={c.voice_fingerprint.sentence_structure}, Taboo Words={c.voice_fingerprint.taboo_phrases}"
            for c in registry.characters
        ])

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

        print(f"  [Agent: Prose Drafter] Drafting Chapter {chapter_beat.chapter_number}: {chapter_beat.title} ({total_sub_beats} sub-beats)...")

        for idx, sub_beat in enumerate(chapter_beat.sub_beats, start=1):
            beat_label = f"{chapter_beat.chapter_number}.{idx}"

            user_prompt = f"""**Role:** You are an elite, award-winning author specializing in the {world_bible.genre} genre. Your prose is immersive, realistic, and character-driven.

**Task:** Write Scene Beat {beat_label} (approx. 600-900 words) fulfilling the narrative beats provided below. Do NOT write conversational preambles or meta commentary; write only the specified manuscript prose.

**Context Guidelines (The Codex):**
* **Genre Style Guide:** Genre={world_bible.genre.upper()}. Setting={world_bible.setting_overview}. World Rules={[r.rule_name + ': ' + r.narrative_consequence for r in world_bible.rules[:3]]}
* **Active Characters:**
{char_voices}
* **Story So Far (Preceding Chapters):**
{story_state.story_so_far_summary[-1200:] if story_state.story_so_far_summary else "This is Chapter 1 - Opening chapter."}

**Scene Continuity So Far (Current Chapter):**
{running_chapter_context[-1500:] if running_chapter_context else "Beginning of Chapter " + str(chapter_beat.chapter_number) + "."}

**Current Scene Micro-Beat to Execute ({beat_label}):**
Chapter {chapter_beat.chapter_number}: {chapter_beat.title}
POV Character: {chapter_beat.pov_character}
Location: {chapter_beat.location}
Scene Section: {sub_beat.section_number}
Scene Objective: {sub_beat.scene_objective}
Key Interaction / Conflict: {sub_beat.key_interaction}
Sensory & Structural Detail: {sub_beat.sensory_or_structural_detail}
Ending Transition Hook: {sub_beat.ending_hook}
{revision_context}

**Strict Execution Constraints:**
1. **Show, Don't Tell:** Anchor the narrative in concrete sensory details and immediate character action. Do not summarize elapsed time or off-screen events unless explicitly instructed.
2. **Banish AI Slop:** You are strictly forbidden from using generic LLM tropes, including but not limited to: "a tapestry of," "a testament to," "shivers down her spine," "a palpable tension," or "little did they know."
3. **No Moralizing Conclusions:** End the scene precisely on the final beat provided. Do not append a concluding paragraph that summarizes the scene's emotional weight or hints at the future.
4. **Dialogue Realism:** Characters must speak with distinct voices based on their profiles. Include interruptions, unspoken subtext, and physical actions (beats) between dialogue lines.
5. **Section Heading:** Start the section with a clean markdown heading: `### {sub_beat.section_number} {sub_beat.scene_objective}`.
"""
            scene_raw = self.llm.generate_text(user_prompt, system_prompt=PROSE_DRAFTER_PROMPT, max_tokens=2048)
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