"""Scripted stand-in for a model, routed on each prompt's TASK line, for fully offline pipeline tests."""

import json
import re


class FakeLlm:
    provider = "fake"
    model = "fake"

    def __init__(self, chapters=2, scenes=2, is_fiction=True, scores=None, scene_words=120):
        self.chapters = chapters
        self.scenes = scenes
        self.is_fiction = is_fiction
        self.scores = list(scores or [])
        self.scene_words = scene_words
        self.tasks = []
        self.scene_count = 0

    def generate_text(self, prompt, system_prompt="", max_tokens=4096):
        match = re.search(r"TASK: ([a-z ]+)", prompt)
        task = match.group(1).strip() if match else "world or cast"
        self.tasks.append(task)
        handler = getattr(self, "_" + task.replace(" ", "_"), None)
        if handler:
            return handler(prompt)
        if '"characters"' in prompt:
            return json.dumps({"characters": [{"name": "Ilan Roth", "role": "Protagonist"}]})
        return json.dumps({"title": "T", "genre": "thriller", "rules": [{"rule_name": "No debts", "narrative_consequence": "Ruin"}]})

    def _book_brief(self, prompt):
        return json.dumps({
            "is_fiction": self.is_fiction, "logline": "A ferryman finds a ledger of the drowned.",
            "target_reader": "Thriller readers", "reader_promise": "Dread that pays off",
            "central_question": "Who wrote the ledger?", "ending": "He wrote it.",
            "voice_guide": "Dry, close, wary", "voice_sample": "The river kept its accounts."
        })

    def _book_plan(self, prompt):
        return json.dumps({
            "pacing_notes": "Escalate",
            "chapters": [
                {"chapter_number": n, "part_title": f"Part {1 + (n - 1) // 2}", "title": f"Unique Title {n}", "core_narrative_arc": f"Change {n}"}
                for n in range(1, self.chapters + 1)
            ],
            "setups_and_payoffs": [{"name": "The Ledger", "description": "A wet ledger", "planted_chapter": 1, "target_payoff_chapter": self.chapters}]
        })

    def _scene_plan(self, prompt):
        return json.dumps({"scenes": [{"scene_objective": f"Objective {i} {len(self.tasks)}", "heading": f"Heading {i}"} for i in range(self.scenes)]})

    def _prose(self, tag):
        self.scene_count += 1
        words = [f"word{tag}{self.scene_count}x{i}" for i in range(self.scene_words)]
        return "He ran. The Ledger waited. " + " ".join(words) + "."

    def _scene_draft(self, prompt):
        return self._prose("d")

    def _scene_revision(self, prompt):
        return self._prose("r")

    def _chapter_review(self, prompt):
        score = self.scores.pop(0) if self.scores else 9
        keys = ["opening_hook", "tension_or_curiosity", "depth", "voice", "originality", "pacing", "ending_pull"]
        notes = [] if score >= 8 else [{"scene": 1, "problem": "Slack", "fix": "Tighten"}]
        return json.dumps({"scores": {k: score for k in keys}, "strengths": ["Voice"], "scene_notes": notes})

    def _chapter_memory(self, prompt):
        resolved = ["The Ledger"] if f"Chapter {self.chapters}:" in prompt else []
        return json.dumps({"recap": "Things changed.", "clues_resolved": resolved, "opened_threads": ["Who pays?"]})

    def _book_review(self, prompt):
        return json.dumps({"arc_score": 9, "problems": []})

    def _choose_opening(self, prompt):
        return json.dumps({"best": 2})

    def _fact_check(self, prompt):
        return json.dumps({"claims": ["A claim"]})

    def _publishing_kit(self, prompt):
        return json.dumps({"tagline": "Pay up.", "blurb": "A ferryman finds a ledger.", "kdp_keywords": ["river thriller"]})
