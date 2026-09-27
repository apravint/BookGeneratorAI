# AGENTS.md - Operational Instructions for AI Assistants 🤖

This file serves as the definitive instruction manual for autonomous AI coding assistants (e.g., Gemini, Claude, Cursor, Antigravity) operating within the `BookGeneratorAI` repository.

---

## 🎯 Repository Core Architecture

`BookGeneratorAI` is a production-grade multi-agent engine designed to orchestrate long-form manuscript generation (300+ pages / 80,000+ words). It enforces:
1. **Context Isolation**: No single LLM prompt receives the full manuscript history.
2. **Iterative Scene Drafting**: Chapters are split into 6 granular sub-beats (600–900 words each).
3. **Adversarial Critic Loop**: `AntiSlopEditorAgent` audits generated prose against banned AI tropes and voice fingerprint rules.
4. **Resilient Local Execution**: Direct Ollama REST integration with zero silent mock fallbacks.

---

## ⚙️ Executable Verification Commands

Before declaring any coding task complete, run the following verification pipeline:

### 1. Fast Syntax & Model Compilation Check
```bash
python3 -m py_compile main.py generator/*.py agents/*.py schemas/*.py memory/*.py tools/*.py
```

### 2. Fast Single-Chapter Execution Test
```bash
python3 main.py \
  --title "Verification Test" \
  --genre fiction \
  --author "Pravin Tamilan" \
  --provider ollama \
  --model "deepseek-r1:latest" \
  --reset \
  --output "output/Verification_Test.docx"
```

---

## 🧱 Key Code Conventions & Schemas

### 1. Pydantic v2 Models (`schemas/models.py`)
- All agent inputs and outputs MUST be validated using Pydantic v2 `BaseModel`.
- Use `AliasChoices` for flexible LLM field mapping (e.g., `rule_name`, `consequence`, `impact`).
- Provide non-empty genre-derived defaults for fallback methods.

### 2. Resilient LLM Calls (`generator/llm_client.py`)
- **NEVER** re-introduce silent mock generators (`_call_offline_generator`). If an API or network call fails, raise a descriptive `RuntimeError`.
- Maintain DeepSeek-R1 `<think>.*?</think>` regex stripping (`re.DOTALL`) and preamble filtering.
- Keep Ollama socket timeouts set to `600` seconds with `num_ctx: 16384`.

### 3. Beat-by-Beat Scene Drafting (`agents/prose_drafter.py`)
- Draft scenes sequentially per `SubBeat`.
- Always pass rolling scene context buffers and `StoryState.story_so_far_summary`.
- Retain Codex prompt constraints (*Show Don't Tell*, *Banish AI Slop*, *No Moralizing Conclusions*, *Dialogue Realism*).

---

## 🚦 Three-Tier Safety Boundary Matrix

| Tier | Category | Directives |
|---|---|---|
| 🟢 **ALWAYS** | Verification & Syntax | - Run `py_compile` before finalizing edits.<br>- Preserve Pydantic schema validation.<br>- Log live progress metrics (beat number and word count). |
| 🟡 **ASK FIRST** | Schema & Configuration | - Modifying `FORBIDDEN_SLOP_PATTERNS` in `prompts/system_prompts.py`.<br>- Adding new PyPI dependencies to `requirements.txt`.<br>- Altering SQLite table schemas in `memory/state_manager.py`. |
| 🔴 **NEVER** | System Integrity | - Re-introducing silent mock fallbacks or dummy prose generators.<br>- Hardcoding publisher press boilerplate or fake ISBN numbers into generated `.docx` manuscripts.<br>- Reducing Ollama `num_ctx` below 8192.<br>- Disabling the adversarial anti-slop critic pass. |

---

## 👤 Lead Architect Reference
**Pravin Tamilan** — Lead AI Systems Architect & Vice President (Chennai, India)
- Specialization: Agentic AI Orchestration, Model Context Protocol (MCP), Distributed Systems, Spring Boot & Angular Architectures.
