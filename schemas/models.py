"""
Pydantic Data Models for Production-Grade Multi-Agent Book Generation Pipeline.
Defines strict schemas for World Bible, Character Registries, Chapter Beats, Revision Briefs, and Story State.
Includes flexible field alias choices (e.g. consequence/impact) and default fallbacks for LLM outputs.
"""

from typing import List, Dict, Optional, Any
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


class CharacterCondition(BaseModel):
    character_name: str = Field(default="Protagonist", description="Character name")
    physical_wounds_or_status: List[str] = Field(default_factory=list, description="Injuries or physical status")
    inventory_items: List[str] = Field(default_factory=list, description="Items / documents / weapons currently held")
    emotional_state: str = Field(default="Determined", description="Current emotional valence")
    current_location: str = Field(default="Unknown", description="Current whereabouts")


class CharacterRelation(BaseModel):
    source_char: str = Field(..., description="Source character name or ID")
    target_char: str = Field(..., description="Target character name or ID")
    relation_type: str = Field(default="acquaintance", description="Type of relationship: ally, rival, confidant, debtor, betrayer, secret_ally, kin")
    affinity_score: int = Field(default=0, ge=-10, le=10, description="Affinity score: -10 (hostile) to +10 (devoted)")
    dynamic_status: str = Field(default="Neutral dynamic", description="Contextual narrative dynamic description")


class ForeshadowingClue(BaseModel):
    clue_id: str = Field(default="clue_01", description="Unique identifier for clue or suspense hook")
    name: str = Field(default="Unresolved Hook", description="Brief name or label for the clue")
    description: str = Field(default="", description="Detailed explanation of the planted clue")
    planted_chapter: int = Field(default=1, description="Chapter where clue is introduced")
    planted_beat: str = Field(default="1.1", description="Sub-beat section where clue was dropped")
    target_payoff_chapter: int = Field(default=5, description="Scheduled chapter of revelation or climax")
    status: str = Field(default="planted", description="Status: 'planted', 'escalated', 'resolved', 'abandoned'")
    involved_characters: List[str] = Field(default_factory=list, description="Characters aware of or affected by clue")
    payoff_notes: str = Field(default="", description="Resolution details when resolved")


class BookBrief(BaseModel):
    """Commercial concept every downstream agent writes toward."""
    is_fiction: bool = Field(default=True, description="True for narrative fiction, False for non-fiction")
    logline: str = Field(default="", description="One-sentence hook a reader would repeat to a friend")
    target_reader: str = Field(default="", description="Specific reader this book is for")
    reader_promise: str = Field(default="", description="The experience or transformation the book guarantees")
    central_question: str = Field(default="", description="The question that keeps pages turning")
    what_makes_it_different: str = Field(default="", description="Why this is not like other books on the shelf")
    genre_conventions: List[str] = Field(default_factory=list, description="Conventions readers of this genre expect")
    ending: str = Field(default="", description="How the book ends or what final insight it lands on")
    voice_guide: str = Field(default="", description="Concrete traits of the narrative voice")
    voice_sample: str = Field(default="", description="Short paragraph demonstrating the voice")


class SubBeat(BaseModel):
    section_number: str = Field(default="1.1", description="Section number")
    heading: str = Field(default="", description="Reader-facing section heading (non-fiction only)")
    scene_objective: str = Field(default="Execute core scene goal", description="Scene goal")
    beat_type: str = Field(default="SCENE_GOAL", description="Dramatic beat type (SCENE_GOAL, CONFLICT_ESCALATION, DISASTER_REVERSAL, EMOTIONAL_REACTION, DILEMMA_CALCULATION, PIVOTAL_DECISION)")
    micro_tension_level: int = Field(default=5, ge=1, le=10, description="Micro-tension index (1=calm, 10=maximum crisis)")
    pov_internal_state: str = Field(default="Focused on scene goal with unspoken subtext.", description="Internal psychological subtext")
    characters_present: List[str] = Field(default_factory=list, description="Characters present")
    key_interaction: str = Field(default="Pivotal dialogue and tension turning point", description="Interaction")
    sensory_or_structural_detail: str = Field(default="Vivid grounding detail and environment anchor", description="Sensory detail")
    ending_hook: str = Field(default="Transition hook into next section", description="Hook")


class ChapterBeat(BaseModel):
    chapter_number: int = Field(default=1, description="Chapter number")
    part_title: str = Field(default="", description="Title of the book part this chapter opens or belongs to")
    title: str = Field(default="Chapter Title", description="Chapter title")
    pov_character: str = Field(default="Protagonist", description="POV perspective")
    location: str = Field(default="Primary Setting", description="Location")
    core_narrative_arc: str = Field(default="Chapter narrative trajectory", description="Narrative arc")
    sub_beats: List[SubBeat] = Field(default_factory=list, description="6 sub-section beats")
    target_word_count: int = Field(default=3500, description="Target word count")
    prerequisite_chapters: List[int] = Field(default_factory=list, description="IDs of chapters that causally precede or influence this chapter")
    foreshadowing_clues_to_plant: List[str] = Field(default_factory=list, description="Clue labels scheduled to be dropped in this chapter")
    foreshadowing_clues_to_resolve: List[str] = Field(default_factory=list, description="Clue labels scheduled to pay off in this chapter")


class MasterOutline(BaseModel):
    title: str = Field(default="Master Outline", description="Book title")
    total_parts: int = Field(default=4, description="Parts count")
    chapters: List[ChapterBeat] = Field(default_factory=list, description="Chapter beats")
    pacing_notes: str = Field(default="4-Part escalating pacing curve", description="Pacing notes")
    foreshadowing: List[ForeshadowingClue] = Field(default_factory=list, description="Setups and payoffs planned across the book")


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


class SceneNote(BaseModel):
    scene: int = Field(default=1, description="1-based scene number the note applies to")
    problem: str = Field(default="", description="Specific weakness, quoting the text where possible")
    fix: str = Field(default="", description="Concrete rewrite direction")


class CraftReview(BaseModel):
    scores: Dict[str, float] = Field(default_factory=dict, description="Rubric scores from 1 to 10")
    strengths: List[str] = Field(default_factory=list, description="What must survive revision")
    scene_notes: List[SceneNote] = Field(default_factory=list, description="Scene-level revision notes")


class RevisionBrief(BaseModel):
    chapter_number: int = Field(default=1, description="Target chapter number")
    passed_audit: bool = Field(default=True, description="Audit passed status")
    continuity_issues: List[ContinuityIssue] = Field(default_factory=list, description="Continuity issues")
    slop_violations: List[AntiSlopViolation] = Field(default_factory=list, description="Slop violations")
    editor_overall_directive: str = Field(default="Draft meets editorial standards.", description="Overall directive")
    craft_scores: Dict[str, float] = Field(default_factory=dict, description="Developmental editor rubric scores")
    craft_score: Optional[float] = Field(default=None, description="Mean rubric score; None when unreviewed")
    strengths: List[str] = Field(default_factory=list, description="What revision must preserve")
    scene_notes: List[SceneNote] = Field(default_factory=list, description="Scene-level revision notes")


class StoryState(BaseModel):
    current_chapter: int = Field(default=0, description="Current chapter number")
    story_so_far_summary: str = Field(default="", description="Running story memory summary")
    chapter_recaps: Dict[int, str] = Field(default_factory=dict, description="Recap of each finished chapter")
    active_plot_threads: List[str] = Field(default_factory=list, description="Unresolved plot points")
    resolved_plot_threads: List[str] = Field(default_factory=list, description="Resolved plot points")
    character_states: Dict[str, str] = Field(default_factory=dict, description="Character state tracker")
    character_conditions: Dict[str, CharacterCondition] = Field(default_factory=dict, description="Detailed physical/emotional inventory tracker")
    epistemic_secrets: List[Dict[str, Any]] = Field(default_factory=list, description="Secrets known vs hidden among characters")
    key_discoveries: List[str] = Field(default_factory=list, description="Key discoveries")
    foreshadowing_clues: List[ForeshadowingClue] = Field(default_factory=list, description="Master foreshadowing, suspense and clue tracker")
    character_relationships: List[CharacterRelation] = Field(default_factory=list, description="Dynamic character relationship network")


class ChapterMemory(BaseModel):
    """Structured facts extracted from a finished chapter."""
    recap: str = Field(default="", description="What happened and what changed")
    opened_threads: List[str] = Field(default_factory=list)
    closed_threads: List[str] = Field(default_factory=list)
    character_conditions: List[CharacterCondition] = Field(default_factory=list)
    relationships: List[CharacterRelation] = Field(default_factory=list)
    clues_escalated: List[str] = Field(default_factory=list)
    clues_resolved: List[str] = Field(default_factory=list)
    secrets: List[Dict[str, Any]] = Field(default_factory=list)
    discoveries: List[str] = Field(default_factory=list)


class PublishingKit(BaseModel):
    subtitle: str = Field(default="", description="Optional subtitle")
    tagline: str = Field(default="", description="One line for the cover or ads")
    blurb: str = Field(default="", description="Back-cover and store description")
    kdp_keywords: List[str] = Field(default_factory=list, description="Seven search phrases")
    bisac_categories: List[str] = Field(default_factory=list, description="Suggested retail categories")
    comparable_titles: List[str] = Field(default_factory=list, description="Comparable titles for positioning; must be verified by a human")
    cover_brief: str = Field(default="", description="Direction for a cover designer")
    launch_plan: List[str] = Field(default_factory=list, description="Concrete launch actions")
