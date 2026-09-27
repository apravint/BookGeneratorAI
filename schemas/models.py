"""
Pydantic Data Models for Production-Grade Multi-Agent Book Generation Pipeline.
Defines strict schemas for World Bible, Character Registries, Chapter Beats, Revision Briefs, and Story State.
Includes flexible field alias choices (e.g. consequence/impact) and default fallbacks for LLM outputs.
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field

try:
    from pydantic import AliasChoices
    def get_rule_name_field():
        return Field(
            default="Core World Constraint",
            validation_alias=AliasChoices("rule_name", "name", "rule", "title"),
            description="Name or title of the world rule"
        )
    def get_narrative_consequence_field():
        return Field(
            default="Creates tension and cascading fallout when broken.",
            validation_alias=AliasChoices("narrative_consequence", "consequence", "impact", "result"),
            description="What happens when characters break or interact with this rule"
        )
except ImportError:
    def get_rule_name_field():
        return Field(
            default="Core World Constraint",
            description="Name or title of the world rule"
        )
    def get_narrative_consequence_field():
        return Field(
            default="Creates tension and cascading fallout when broken.",
            description="What happens when characters break or interact with this rule"
        )


class WorldRule(BaseModel):
    category: str = Field(default="Systemic Rule", description="Category of rule")
    rule_name: str = get_rule_name_field()
    description: str = Field(default="Operational constraint governing the setting.", description="Detailed explanation")
    narrative_consequence: str = get_narrative_consequence_field()



class WorldBible(BaseModel):
    title: str = Field(default="Untitled Masterwork", description="Book title")
    genre: str = Field(default="general", description="Primary genre")
    language: str = Field(default="english", description="Manuscript language: 'english' or 'tamil'")
    setting_overview: str = Field(default="Immersive, high-stakes setting environment.", description="Setting description")
    time_period: str = Field(default="Contemporary / Modern Era", description="Temporal setting")
    core_thematic_conflict: str = Field(default="Transformation vs Legacy Resistance", description="Central conflict")
    rules: List[WorldRule] = Field(default_factory=list, description="Explicit hard rules governing setting")
    forbidden_tropes: List[str] = Field(default_factory=list, description="Forbidden clichés")


class CharacterVoice(BaseModel):
    tone: str = Field(default="Pragmatic and focused", description="Vocal tone")
    sentence_structure: str = Field(default="Direct and articulate", description="Sentence rhythm")
    frequently_used_terms: List[str] = Field(default_factory=list, description="Signature vocabulary")
    taboo_phrases: List[str] = Field(default_factory=list, description="Taboo expressions")


class CharacterProfile(BaseModel):
    character_id: str = Field(default="char_01", description="Unique ID")
    name: str = Field(default="Protagonist", description="Character name")
    role: str = Field(default="Protagonist", description="Role in story")
    core_motivation: str = Field(default="Achieving mastery and protecting the core mission", description="Drive")
    fatal_flaw: str = Field(default="Hesitancy to trust allies prematurely", description="Fatal flaw")
    backstory_summary: str = Field(default="Experienced specialist who witnessed prior systemic failures.", description="Backstory")
    voice_fingerprint: CharacterVoice = Field(default_factory=CharacterVoice, description="Voice pattern")
    relationships: Dict[str, str] = Field(default_factory=dict, description="Relationships mapping")
    arc_trajectory: str = Field(default="From cautious practitioner to visionary leader", description="Arc trajectory")


class CharacterRegistry(BaseModel):
    characters: List[CharacterProfile] = Field(default_factory=list, description="Master character list")

    def get_character(self, character_id: str) -> Optional[CharacterProfile]:
        for c in self.characters:
            if c.character_id == character_id or c.name.lower() == character_id.lower():
                return c
        return None


class SubBeat(BaseModel):
    section_number: str = Field(default="1.1", description="Section number")
    scene_objective: str = Field(default="Execute core scene goal", description="Scene goal")
    characters_present: List[str] = Field(default_factory=list, description="Characters present")
    key_interaction: str = Field(default="Pivotal dialogue and tension turning point", description="Interaction")
    sensory_or_structural_detail: str = Field(default="Vivid grounding detail and environment anchor", description="Sensory detail")
    ending_hook: str = Field(default="Transition hook into next section", description="Hook")


class ChapterBeat(BaseModel):
    chapter_number: int = Field(default=1, description="Chapter number")
    title: str = Field(default="Chapter Title", description="Chapter title")
    pov_character: str = Field(default="Protagonist", description="POV perspective")
    location: str = Field(default="Primary Setting", description="Location")
    core_narrative_arc: str = Field(default="Chapter narrative trajectory", description="Narrative arc")
    sub_beats: List[SubBeat] = Field(default_factory=list, description="6 sub-section beats")
    target_word_count: int = Field(default=3500, description="Target word count")


class MasterOutline(BaseModel):
    title: str = Field(default="Master Outline", description="Book title")
    total_parts: int = Field(default=4, description="Parts count")
    chapters: List[ChapterBeat] = Field(default_factory=list, description="Chapter beats")
    pacing_notes: str = Field(default="4-Part escalating pacing curve", description="Pacing notes")


class ContinuityIssue(BaseModel):
    severity: str = Field(default="MAJOR", description="Severity: CRITICAL, MAJOR, MINOR")
    location: str = Field(default="Chapter Draft", description="Location reference")
    description: str = Field(default="Continuity contradiction detected", description="Issue description")
    remedy: str = Field(default="Rephrase or adjust context to maintain consistency", description="Remedy")


class AntiSlopViolation(BaseModel):
    phrase_or_pattern: str = Field(..., description="Offending cliché phrase")
    line_snippet: str = Field(default="", description="Snippet context")
    reason: str = Field(default="Banned AI trope", description="Reason")
    replacement_suggestion: str = Field(default="Replace with original vivid prose", description="Suggestion")


class RevisionBrief(BaseModel):
    chapter_number: int = Field(default=1, description="Target chapter number")
    passed_audit: bool = Field(default=True, description="Audit passed status")
    continuity_issues: List[ContinuityIssue] = Field(default_factory=list, description="Continuity issues")
    slop_violations: List[AntiSlopViolation] = Field(default_factory=list, description="Slop violations")
    editor_overall_directive: str = Field(default="Draft meets editorial standards.", description="Overall directive")


class StoryState(BaseModel):
    current_chapter: int = Field(default=0, description="Current chapter number")
    story_so_far_summary: str = Field(default="", description="Running story memory summary")
    active_plot_threads: List[str] = Field(default_factory=list, description="Unresolved plot points")
    resolved_plot_threads: List[str] = Field(default_factory=list, description="Resolved plot points")
    character_states: Dict[str, str] = Field(default_factory=dict, description="Character state tracker")
    key_discoveries: List[str] = Field(default_factory=list, description="Key discoveries")
