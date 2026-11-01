# AGENTS.md - Operational Instructions for AI Assistants 🤖

This file serves as the definitive instruction manual for autonomous AI coding assistants (e.g., Gemini, Claude, Cursor, Antigravity) operating within the `BookGeneratorAI` repository.

---

## 🎯 Repository Core Architecture

`BookGeneratorAI` is a production-grade multi-agent engine designed to orchestrate long-form manuscript generation (300+ pages / 80,000+ words). It enforces:
1. **Context Isolation**: No single LLM prompt receives the full manuscript history.
2. **Iterative Scene Drafting**: Chapters are split into model-planned scenes sized from `--target-words`.
3. **Adversarial Critic Loop**: `DevelopmentalEditorAgent` scores chapters on a strict rubric and `AntiSlopEditorAgent` audits banned tropes; only flagged scenes are revised.
4. **Resilient Local Execution**: Direct Ollama REST integration with zero silent mock fallbacks.

---

## ⚙️ Executable Verification Commands

Before declaring any coding task complete, run the following verification pipeline:

### 1. Fast Syntax & Model Compilation Check
```bash
python3 -m py_compile main.py generator/*.py agents/*.py schemas/*.py memory/*.py tools/*.py
```

### 2. Offline Test Suite (no LLM or API cost)
```bash
python3 -m pytest
```

### 3. Fast Real-Model Run
```bash
python3 main.py --title "Verification Test" --concept "A specific original premise" \
  --chapters 2 --target-words 4000 --provider ollama --reset
```
Output goes to `books/Verification_Test/`. `--reset` only touches that book.

---

## 🧱 Key Code Conventions & Schemas

### 1. Pydantic v2 Models (`schemas/models.py`)
- All agent inputs and outputs MUST be validated using Pydantic v2 `BaseModel`.
- Use `AliasChoices` for flexible LLM field mapping (e.g., `rule_name`, `consequence`, `impact`).
- Agent output is requested through `generate_validated`, which feeds failures back to the model and raises `StructuredOutputError` rather than inventing content. Never add stock worlds, casts or outlines as fallbacks.

### 2. Resilient LLM Calls (`generator/llm_client.py`)
- **NEVER** re-introduce silent mock generators (`_call_offline_generator`). If an API or network call fails, raise a descriptive `RuntimeError`.
- Maintain DeepSeek-R1 `<think>.*?</think>` regex stripping (`re.DOTALL`) and preamble filtering.
- Keep request timeouts at `600` seconds and Ollama `num_ctx` at `16384` (8192 for small models). Keep retry with backoff in `_post_json`.

### 3. Beat-by-Beat Scene Drafting (`agents/prose_drafter.py`)
- Draft scenes sequentially per `SubBeat`.
- Always pass the preceding prose verbatim and `StoryState.chapter_recaps`.
- Revise flagged scenes in place with `revise_scene`; never discard a whole chapter to fix one problem.
- Retain Codex prompt constraints (*Show Don't Tell*, *Banish AI Slop*, *No Moralizing Conclusions*, *Dialogue Realism*).

---

## 🚦 Three-Tier Safety Boundary Matrix

| Tier | Category | Directives |
|---|---|---|
| 🟢 **ALWAYS** | Verification & Syntax | - Run `py_compile` before finalizing edits.<br>- Preserve Pydantic schema validation.<br>- Log live progress metrics (beat number and word count). |
| 🟡 **ASK FIRST** | Schema & Configuration | - Modifying `FORBIDDEN_SLOP_PATTERNS` in `prompts/system_prompts.py`.<br>- Adding new PyPI dependencies to `requirements.txt`.<br>- Altering SQLite table schemas in `memory/state_manager.py`. |
| 🔴 **NEVER** | System Integrity | - Re-introducing silent mock fallbacks or dummy prose generators.<br>- Hardcoding publisher press boilerplate, fake ISBN numbers, invented praise, bestseller claims, prices or credentials into any generated book or listing.<br>- Reporting a book as ready when a release check failed.<br>- Reducing Ollama `num_ctx` below 8192.<br>- Disabling the adversarial anti-slop critic pass. |

---

## 👤 Lead Architect Reference
**Pravin Tamilan** — Lead AI Systems Architect & Vice President (Chennai, India)
- Specialization: Agentic AI Orchestration, Model Context Protocol (MCP), Distributed Systems, Spring Boot & Angular Architectures.
