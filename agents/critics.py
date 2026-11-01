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
    AntiSlopViolation,
    BookBrief,
    CraftReview,
    SceneNote
)
from generator.llm_client import LlmClient
from generator.json_parser import generate_validated, StructuredOutputError
from prompts.system_prompts import (
    FORBIDDEN_SLOP_PATTERNS,
    TAMIL_FORBIDDEN_SLOP_PATTERNS,
    DEVELOPMENTAL_EDITOR_PROMPT,
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
        # Taboo phrases only count inside dialogue; narration may legitimately use them
        dialogue = " ".join(re.findall(r'["“]([^"”]+)["”]', chapter_text)).lower()
        for char in registry.characters:
            if char.name.lower() not in chapter_text.lower():
                continue
            for taboo in char.voice_fingerprint.taboo_phrases:
                if taboo.lower() in dialogue:
                    issues.append(ContinuityIssue(
                        severity="MINOR",
                        location=f"Chapter {chapter_number}",
                        description=f"Dialogue contains '{taboo}', a phrase {char.name} never uses. Confirm another character speaks it.",
                        remedy=f"If {char.name} says it, rephrase in their voice."
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
                    line_snippet=self._snippet(chapter_text, pattern),
                    reason="Banned AI cliché / writing trope.",
                    replacement_suggestion=f"Remove or replace '{pattern}' with vivid, original prose."
                ))

        # Check for perceptual filter words in English prose
        if not is_tamil:
            for filter_pattern in PERCEPTUAL_FILTER_PATTERNS:
                if filter_pattern in text_lower:
                    violations.append(AntiSlopViolation(
                        phrase_or_pattern=filter_pattern,
                        line_snippet=self._snippet(chapter_text, filter_pattern),
                        reason="Filter language weakens Deep POV immersion.",
                        replacement_suggestion=f"Cut '{filter_pattern}' and describe the sensory action directly."
                    ))

        # Check Gary Provost Sentence Cadence & Rhythm
        violations.extend(self.audit_sentence_cadence(chapter_text, is_tamil=is_tamil))

        violations.extend(self.audit_repetition(chapter_text))

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

    @staticmethod
    def _snippet(text: str, phrase: str, radius: int = 60) -> str:
        at = text.lower().find(phrase)
        return text[max(0, at - radius):at + len(phrase) + radius].replace("\n", " ").strip()

    def audit_repetition(self, chapter_text: str) -> List[AntiSlopViolation]:
        """Measures the structural tics that phrase lists miss."""
        violations = []
        prose = "\n".join(l for l in chapter_text.split("\n") if not l.lstrip().startswith("#"))
        word_count = max(len(prose.split()), 1)

        antithesis = len(re.findall(r"\b(?:not|n't)\b[^.!?\n]{0,60}[,;:—-]\s*(?:but|it was|it is|they were)\b", prose, re.IGNORECASE))
        if word_count >= 500 and antithesis * 1000 / word_count > 2:
            violations.append(AntiSlopViolation(
                phrase_or_pattern="Overused 'not X but Y' construction",
                line_snippet=f"{antithesis} uses in {word_count} words.",
                reason="This rhetorical pattern is a strong tell of machine prose.",
                replacement_suggestion="State the thing directly; keep at most one per chapter."
            ))

        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', prose) if s.strip()]
        openers = [re.sub(r'^\W+', '', s).split(" ")[0].lower() for s in sentences]
        for i in range(len(openers) - 3):
            if openers[i] and len(set(openers[i:i + 4])) == 1:
                violations.append(AntiSlopViolation(
                    phrase_or_pattern="Repeated sentence opener",
                    line_snippet=" ".join(sentences[i:i + 4])[:120],
                    reason=f"Four consecutive sentences open with '{openers[i]}'.",
                    replacement_suggestion="Vary the sentence openings unless the repetition is a deliberate effect."
                ))
                break
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
        if not has_staccato and len(sentences) >= 20:
            violations.append(AntiSlopViolation(
                phrase_or_pattern="Lack of Staccato Rhythm",
                line_snippet="No short punchy sentences (<=5 words) found in chapter.",
                reason="Prose lacks dynamic impact punctuation.",
                replacement_suggestion="Add short, punchy sentences during moments of realization, surprise, or tension."
            ))

        return violations


class DevelopmentalEditorAgent:
    """Reads a chapter as a demanding editor would. Regex can catch cliches; only a reader can catch dullness."""

    RUBRIC = {
        "opening_hook": "Does the first paragraph make stopping hard?",
        "tension_or_curiosity": "Does each scene create a reason to read the next?",
        "depth": "Character depth in fiction; genuine insight in non-fiction.",
        "voice": "Is the voice distinct and consistent with the guide?",
        "originality": "Are details and turns specific and unpredictable?",
        "pacing": "Is anything slack, repeated or over-explained?",
        "ending_pull": "Does the ending force the next chapter open?",
    }

    def __init__(self, llm_client: LlmClient):
        self.llm = llm_client

    def review(self, chapter_beat: ChapterBeat, scenes: List[str], brief: BookBrief, story_state: StoryState) -> CraftReview:
        numbered = "\n\n".join(f"[SCENE {i}]\n{text}" for i, text in enumerate(scenes, start=1))
        rubric = "\n".join(f'- {key}: {question}' for key, question in self.RUBRIC.items())
        prompt = f"""TASK: chapter review
Book promise: {brief.reader_promise}
Target reader: {brief.target_reader}
Voice guide: {brief.voice_guide}
Chapter {chapter_beat.chapter_number}: {chapter_beat.title}
Chapter purpose: {chapter_beat.core_narrative_arc}
Established so far: {story_state.story_so_far_summary[-3000:] or "Nothing; this is the opening."}

Score 1-10 on:
{rubric}

MANUSCRIPT:
{numbered}

Return ONLY JSON:
{{"scores": {{{", ".join(f'"{key}": 0' for key in self.RUBRIC)}}},
 "strengths": ["what revision must preserve"],
 "scene_notes": [{{"scene": 1, "problem": "quote the weak line and say why", "fix": "concrete rewrite direction"}}]}}
"""
        return generate_validated(
            self.llm, prompt, DEVELOPMENTAL_EDITOR_PROMPT, CraftReview,
            validator=self._validate, max_tokens=3000
        )

    def _validate(self, review: CraftReview):
        missing = [key for key in self.RUBRIC if key not in review.scores]
        if missing:
            return f"Missing scores: {', '.join(missing)}."
        if any(not 1 <= v <= 10 for v in review.scores.values()):
            return "Scores must be between 1 and 10."
        return None


class MasterAdversarialReviewer:
    PASS_MEAN = 8.0
    PASS_FLOOR = 7.0

    def __init__(self, llm_client: LlmClient):
        self.continuity_editor = ContinuityEditorAgent(llm_client)
        self.anti_slop_editor = AntiSlopEditorAgent(llm_client)
        self.developmental_editor = DevelopmentalEditorAgent(llm_client)

    def evaluate_chapter(
        self,
        chapter_beat: ChapterBeat,
        chapter_text: str,
        world_bible: WorldBible,
        registry: CharacterRegistry,
        story_state: StoryState,
        scenes: List[str] = None,
        brief: BookBrief = None
    ) -> RevisionBrief:
        lang = getattr(world_bible, "language", "english")
        cont_issues = self.continuity_editor.audit_chapter(
            chapter_beat.chapter_number, chapter_text, world_bible, registry, story_state
        )
        slop_violations = self.anti_slop_editor.audit_slop(
            chapter_beat.chapter_number, chapter_text, language=lang
        )
        scenes = scenes or [chapter_text]
        scene_notes = self._mechanical_scene_notes(scenes, slop_violations)

        craft_scores, craft_score, strengths = {}, None, []
        unreviewed = False
        if brief:
            try:
                review = self.developmental_editor.review(chapter_beat, scenes, brief, story_state)
                craft_scores = review.scores
                craft_score = round(sum(review.scores.values()) / len(review.scores), 2)
                strengths = review.strengths
                scene_notes += [n for n in review.scene_notes if 1 <= n.scene <= len(scenes)]
            except StructuredOutputError as e:
                # Never treat a missing review as approval
                print(f"  [Developmental Editor Warning] {e}")
                unreviewed = True

        blocking = [i for i in cont_issues if i.severity != "MINOR"]
        craft_ok = not brief or (
            craft_score is not None
            and craft_score >= self.PASS_MEAN
            and min(craft_scores.values()) >= self.PASS_FLOOR
        )
        passed = not blocking and not slop_violations and craft_ok and not unreviewed

        directive = "Draft meets high editorial standards." if passed else "Raise the weakest scenes, fix continuity and purge identified AI tropes, keeping what already works."

        return RevisionBrief(
            chapter_number=chapter_beat.chapter_number,
            passed_audit=passed,
            continuity_issues=cont_issues,
            slop_violations=slop_violations,
            editor_overall_directive=directive,
            craft_scores=craft_scores,
            craft_score=craft_score,
            strengths=strengths,
            scene_notes=scene_notes
        )

    @staticmethod
    def _mechanical_scene_notes(scenes: List[str], violations: List[AntiSlopViolation]) -> List[SceneNote]:
        notes = []
        for violation in violations:
            pattern = violation.phrase_or_pattern.lower()
            located = [i for i, s in enumerate(scenes, start=1) if pattern in s.lower()]
            for scene in located:
                notes.append(SceneNote(scene=scene, problem=f"Contains '{violation.phrase_or_pattern}': {violation.reason}", fix=violation.replacement_suggestion))
            if not located:
                notes.append(SceneNote(scene=1, problem=f"{violation.phrase_or_pattern}: {violation.line_snippet}", fix=violation.replacement_suggestion))
        return notes
