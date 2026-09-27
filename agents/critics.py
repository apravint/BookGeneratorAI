"""
Adversarial Critic Agents - Phase 3
Includes ContinuityEditorAgent and AntiSlopEditorAgent.
Scrutinizes chapter drafts against WorldBible, CharacterRegistry, and Anti-Slop Tropes.
"""

import json
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
    FORBIDDEN_SLOP_PATTERNS
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
        return issues


class AntiSlopEditorAgent:
    def __init__(self, llm_client: LlmClient):
        self.llm = llm_client

    def audit_slop(self, chapter_number: int, chapter_text: str) -> List[AntiSlopViolation]:
        violations = []
        text_lower = chapter_text.lower()

        for pattern in FORBIDDEN_SLOP_PATTERNS:
            if pattern in text_lower:
                violations.append(AntiSlopViolation(
                    phrase_or_pattern=pattern,
                    line_snippet=f"Detected '{pattern}' in draft text.",
                    reason="Banned AI cliché / writing trope.",
                    replacement_suggestion=f"Remove or replace '{pattern}' with vivid, original prose."
                ))

        # Check for preachy conclusion at end of chapter text
        lines = [l.strip() for l in chapter_text.split("\n") if l.strip()]
        if lines:
            last_line = lines[-1].lower()
            if any(w in last_line for w in ["in conclusion", "testament", "reminder that", "chapter in their lives", "journey had just begun"]):
                violations.append(AntiSlopViolation(
                    phrase_or_pattern="Moralizing Chapter Conclusion",
                    line_snippet=lines[-1][:100],
                    reason="Artificial moralizing summary paragraph at chapter end.",
                    replacement_suggestion="Strip final summary paragraph. End on concrete scene action or cliffhanger."
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
        cont_issues = self.continuity_editor.audit_chapter(
            chapter_beat.chapter_number, chapter_text, world_bible, registry, story_state
        )
        slop_violations = self.anti_slop_editor.audit_slop(
            chapter_beat.chapter_number, chapter_text
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
