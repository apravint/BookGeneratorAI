"""
Adversarial Critic Agents - Phase 3
Includes ContinuityEditorAgent and AntiSlopEditorAgent.
Scrutinizes chapter drafts against WorldBible, CharacterRegistry, and Anti-Slop Tropes.
"""

import json
import re
from typing import List
from schemas.models import (
    WorldBible,
    CharacterRegistry,
    StoryState,
    ChapterBeat,
    RevisionBrief,
    ContinuityIssue,
    AntiSlopViolation
)
from generator.llm_client import LlmClient
from prompts.system_prompts import (
    CONTINUITY_EDITOR_PROMPT,
    ANTI_SLOP_EDITOR_PROMPT,
    FORBIDDEN_SLOP_PATTERNS,
    TAMIL_FORBIDDEN_SLOP_PATTERNS,
    TAMIL_ANTI_SLOP_EDITOR_PROMPT,
    PERCEPTUAL_FILTER_PATTERNS
)


class ContinuityEditorAgent:
    def __init__(self, llm_client: LlmClient):
        self.llm = llm_client

    def audit_chapter(
        self,
        chapter_number: int,
        chapter_text: str,
        world_bible: WorldBible,
        registry: CharacterRegistry,
        story_state: StoryState
    ) -> List[ContinuityIssue]:
        issues = []
        # Local rule checks: check character voice taboo words
        for char in registry.characters:
            for taboo in char.voice_fingerprint.taboo_phrases:
                if taboo.lower() in chapter_text.lower():
                    issues.append(ContinuityIssue(
                        severity="MAJOR",
                        location=f"Chapter {chapter_number}",
                        description=f"Character {char.name} used taboo phrase '{taboo}' which breaks voice fingerprint.",
                        remedy=f"Replace or rephrase '{taboo}' in {char.name}'s dialogue."
                    ))

        # World rule checks
        for rule in world_bible.rules:
            if rule.rule_name.lower() in chapter_text.lower() and "broken" in chapter_text.lower():
                issues.append(ContinuityIssue(
                    severity="CRITICAL",
                    location=f"Chapter {chapter_number}",
                    description=f"World rule '{rule.rule_name}' broken without applying consequence: {rule.narrative_consequence}",
                    remedy=f"Incorporate consequence: {rule.narrative_consequence}"
                ))

        # Epistemic state & secret leaks check
        if story_state and hasattr(story_state, "epistemic_secrets"):
            for secret in story_state.epistemic_secrets:
                fact = secret.get("fact", "")
                known_by = [k.lower() for k in secret.get("known_by", [])]
                hidden_from = [h.lower() for h in secret.get("hidden_from", [])]
                if fact and fact.lower() in chapter_text.lower():
                    for unaware_char in hidden_from:
                        pattern = rf"{unaware_char}.*?said.*?{re.escape(fact)}"
                        if re.search(pattern, chapter_text, re.IGNORECASE):
                            issues.append(ContinuityIssue(
                                severity="CRITICAL",
                                location=f"Chapter {chapter_number}",
                                description=f"Character '{unaware_char}' revealed secret '{fact}' before learning it.",
                                remedy=f"Ensure '{unaware_char}' does not possess or speak of '{fact}' until revealed."
                            ))

        # Foreshadowing payoff audit (MuMuAINovel inspired)
        if story_state and hasattr(story_state, "foreshadowing_clues"):
            text_lower = chapter_text.lower()
            for clue in story_state.foreshadowing_clues:
                if clue.status in ["planted", "escalated"] and clue.target_payoff_chapter == chapter_number:
                    # Check if clue name or description keywords are addressed
                    keywords = [w.lower() for w in clue.name.split() if len(w) > 3]
                    addressed = any(kw in text_lower for kw in keywords) or (clue.name.lower() in text_lower)
                    if not addressed:
                        issues.append(ContinuityIssue(
                            severity="MAJOR",
                            location=f"Chapter {chapter_number}",
                            description=f"Scheduled foreshadowing payoff omitted: Clue '{clue.name}' was due in Chapter {chapter_number}.",
                            remedy=f"Incorporate the revelation or escalation of '{clue.name}': {clue.description}"
                        ))

        # Relationship dynamic consistency check
        if story_state and hasattr(story_state, "character_relationships"):
            for rel in story_state.character_relationships:
                # If characters have intense enmity (-7 or lower)
                if rel.affinity_score <= -7:
                    c1, c2 = rel.source_char.lower(), rel.target_char.lower()
                    if c1 in chapter_text.lower() and c2 in chapter_text.lower():
                        # Look for inappropriate casual terms of endearment between mortal enemies
                        sweet_terms = ["darling", "sweetheart", "my beloved", "best friend", "my dearest"]
                        for term in sweet_terms:
                            if term in chapter_text.lower():
                                issues.append(ContinuityIssue(
                                    severity="MAJOR",
                                    location=f"Chapter {chapter_number}",
                                    description=f"Hostile relationship contradiction: {rel.source_char} and {rel.target_char} have affinity {rel.affinity_score}/10 ('{rel.dynamic_status}'), but text includes unearned affectionate term '{term}'.",
                                    remedy="Maintain hostile tension or explain the deceptive pretense."
                                ))
                                break
        return issues


class AntiSlopEditorAgent:
    def __init__(self, llm_client: LlmClient):
        self.llm = llm_client

    def audit_slop(self, chapter_number: int, chapter_text: str, language: str = "english") -> List[AntiSlopViolation]:
        violations = []
        text_lower = chapter_text.lower()
        is_tamil = language and language.lower() in ["tamil", "ta"]

        patterns = FORBIDDEN_SLOP_PATTERNS
        if is_tamil:
            patterns = patterns + TAMIL_FORBIDDEN_SLOP_PATTERNS

        for pattern in patterns:
            if pattern in text_lower:
                violations.append(AntiSlopViolation(
                    phrase_or_pattern=pattern,
                    line_snippet=f"Detected '{pattern}' in draft text.",
                    reason="Banned AI cliché / writing trope.",
                    replacement_suggestion=f"Remove or replace '{pattern}' with vivid, original prose."
                ))

        # Check for perceptual filter words in English prose
        if not is_tamil:
            for filter_pattern in PERCEPTUAL_FILTER_PATTERNS:
                if filter_pattern in text_lower:
                    violations.append(AntiSlopViolation(
                        phrase_or_pattern=filter_pattern,
                        line_snippet=f"Detected perceptual filter '{filter_pattern}'.",
                        reason="Filter language weakens Deep POV immersion.",
                        replacement_suggestion=f"Cut '{filter_pattern}' and describe the sensory action directly."
                    ))

        # Check Gary Provost Sentence Cadence & Rhythm
        violations.extend(self.audit_sentence_cadence(chapter_text, is_tamil=is_tamil))

        # Check for preachy conclusion at end of chapter text
        lines = [l.strip() for l in chapter_text.split("\n") if l.strip()]
        if lines:
            last_line = lines[-1].lower()
            moral_phrases = ["in conclusion", "testament", "reminder that", "chapter in their lives", "journey had just begun", "முடிவாக", "ஒரு பாடமாக", "நினைவூட்டலாக", "தொடங்கியது மட்டுமே"]
            if any(w in last_line for w in moral_phrases):
                violations.append(AntiSlopViolation(
                    phrase_or_pattern="Moralizing Chapter Conclusion",
                    line_snippet=lines[-1][:100],
                    reason="Artificial moralizing summary paragraph at chapter end.",
                    replacement_suggestion="Strip final summary paragraph. End on concrete scene action or cliffhanger."
                ))

        return violations

    def audit_sentence_cadence(self, chapter_text: str, is_tamil: bool = False) -> List[AntiSlopViolation]:
        violations = []
        raw_sentences = re.split(r'(?<=[.!?])\s+', chapter_text)
        # Filter out markdown headings, empty items, and short non-sentence fragments
        sentences = [
            s.strip() for s in raw_sentences
            if s.strip() and not s.strip().startswith('#') and len(s.split()) >= 2
        ]

        if len(sentences) < 5:
            return violations

        word_counts = [len(s.split()) for s in sentences]

        # 1. Check for 5+ consecutive monotonous mid-length sentences (12-22 words)
        monotone_streak = 0
        for wc in word_counts:
            if 12 <= wc <= 22:
                monotone_streak += 1
                if monotone_streak >= 5:
                    violations.append(AntiSlopViolation(
                        phrase_or_pattern="Monotonous Sentence Cadence",
                        line_snippet="Detected 5+ consecutive sentences with monotonous mid-length (12-22 words).",
                        reason="Monotonous sentence rhythm causes reader fatigue (violates Gary Provost rule).",
                        replacement_suggestion="Vary sentence length: intercut punchy 2-5 word statements with sweeping 25+ word sensory sentences."
                    ))
                    break
            else:
                monotone_streak = 0

        # 2. Check for presence of dynamic extremes (staccato vs sweeping sentences)
        has_staccato = any(wc <= 5 for wc in word_counts)
        has_sweeping = any(wc >= 26 for wc in word_counts)
        if not has_staccato and len(sentences) >= 20:
            violations.append(AntiSlopViolation(
                phrase_or_pattern="Lack of Staccato Rhythm",
                line_snippet="No short punchy sentences (<=5 words) found in chapter.",
                reason="Prose lacks dynamic impact punctuation.",
                replacement_suggestion="Add short, punchy sentences during moments of realization, surprise, or tension."
            ))

        return violations


class MasterAdversarialReviewer:
    def __init__(self, llm_client: LlmClient):
        self.continuity_editor = ContinuityEditorAgent(llm_client)
        self.anti_slop_editor = AntiSlopEditorAgent(llm_client)

    def evaluate_chapter(
        self,
        chapter_beat: ChapterBeat,
        chapter_text: str,
        world_bible: WorldBible,
        registry: CharacterRegistry,
        story_state: StoryState
    ) -> RevisionBrief:
        lang = getattr(world_bible, "language", "english")
        cont_issues = self.continuity_editor.audit_chapter(
            chapter_beat.chapter_number, chapter_text, world_bible, registry, story_state
        )
        slop_violations = self.anti_slop_editor.audit_slop(
            chapter_beat.chapter_number, chapter_text, language=lang
        )

        passed = len(cont_issues) == 0 and len(slop_violations) == 0

        directive = "Draft meets high editorial standards." if passed else "Refine prose: fix continuity inconsistencies and purge identified AI tropes."

        return RevisionBrief(
            chapter_number=chapter_beat.chapter_number,
            passed_audit=passed,
            continuity_issues=cont_issues,
            slop_violations=slop_violations,
            editor_overall_directive=directive
        )
