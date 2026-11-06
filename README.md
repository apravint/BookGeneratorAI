# BookGenerator AI 📚🤖
### Executive-Grade Multi-Agent Long-Form Book Generation Engine (Local Ollama & Open Models)

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2-emerald.svg)](https://docs.pydantic.dev/)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20Inference-black.svg)](https://ollama.com)
[![DeepSeek R1](https://img.shields.io/badge/Model-DeepSeek--R1-purple.svg)](https://ollama.com/library/deepseek-r1)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![AGENTS.md](https://img.shields.io/badge/AI--Standards-AGENTS.md-blueviolet.svg)](AGENTS.md)

**BookGenerator AI** is an open-source multi-agent engine that plans, drafts, edits and packages full-length books (80,000 words by default), then tells you honestly whether each one is ready.

> **What it can and cannot promise.** The engine aims for the craft of commercial publishing, and refuses to call a book ready until it passes measurable and editorial checks. No software can guarantee sales. Readers buy on concept, cover, reviews and marketing too, and final quality still depends on your concept, your chosen model, and the human editing listed in every book's release report.

---

## 🏛 Executive Summary: The Engineering Challenge

### The Problem with Single-Prompt Long-Form AI Generation
Standard LLM wrappers fail catastrophically when tasked with long-form writing:
1. **Context degradation & Token Exhaustion**: Context windows overflow around 2,000–4,000 words, causing models to forget previous character developments, plot arcs, and established world constraints.
2. **Repetitive Tropes ("AI Slop")**: Models default to repetitive filler phrases (*"a testament to"*, *"tapestry of"*, *"shivers down her spine"*, *"a palpable tension"*) and forced moralizing summary conclusions.
3. **Hallucinatory Drift**: Without strict state isolation, characters swap voice patterns, break world rules, or solve major plot points prematurely.

### The Architectural Solution
`BookGeneratorAI` implements an enterprise-grade multi-agent architecture featuring:
- **Hierarchical State Isolation & Dynamic Knowledge Graph**: The drafting agent receives *only* the current scene micro-beat, active character living state, epistemic rules, active plot loops, and a rolling memory summary—never the full 80,000-word history.
- **Foreshadowing & Clue Tracking Engine**: Tracks planted narrative clues, suspense hooks, and target payoff chapters. Audits chapters so scheduled payoffs are never omitted or prematurely revealed.
- **Dynamic Character Relationship Network**: Models evolving interpersonal tension, alliances, debts, and affinity scores (-10 to +10) that adapt dynamically as dramatic beats resolve.
- **Portable Lorebooks & Character Cards**: Import and export standardized Character Cards and World Lorebooks (JSON/Markdown) across books and projects via `CardManager`.
- **Causal Chapter DAG & Surgical Invalidation**: Models chapter-to-chapter dependencies to allow surgical regeneration of specific chapters and downstream story branches without corrupting unrelated arcs.
- **Scene & Sequel Dramatic Beat Sheets**: Chapters are decomposed into 6 micro-beats adhering to Dwight Swain's dramatic patterns (Goal → Conflict → Disaster Reversal → Emotional Reaction → Dilemma → Pivotal Decision) with explicit micro-tension curves (1-10) and internal POV subtext.
- **Gary Provost Sentence Cadence & Deep POV Engine**: The adversarial critic intercepts repetitive mid-length sentence runs (the 15-word AI drone), enforces staccato (<5 words) and sweeping (>26 words) variety, and purges perceptual filter words ("she noticed that", "he felt that").
- **Dual-Format Compilation**: Compiles to a 6x9 print interior **DOCX** with mirrored margins, running heads and a live table of contents, and an **EPUB 3** with semantic navigation. Run EPUBCheck and your retailer's previewer before upload.

---

## ⚡ The Adversarial Critic Engine: Before vs. After Transformation

Standard LLMs default to generic clichés and preachy summary endings. `BookGeneratorAI`'s `AntiSlopEditorAgent` actively intercepts and rewrites prose:

```diff
- RAW UNCHECKED OLLAMA PROSE:
- "The quiet night was a testament to their unshakeable bond. Shivers ran down Clara's spine as a palpable tension filled the courtyard. Little did they know, their journey had only just begun. In conclusion, they learned that love conquers all."

+ ADVERSARIAL CRITIC REFINED PROSE:
+ "The courtyard fell quiet under the cold starlight. Clara gripped the stone archway, her knuckles pale against the damp granite. Julian didn't step back; he closed the distance between them until his breathing matched her own."
```

---

## 🏗 Multi-Agent Pipeline Architecture

```
                       ┌─────────────────────────┐
                       │    User Seed Concept    │
                       └────────────┬────────────┘
                                    │
               ┌────────────────────┴────────────────────┐
               ▼                                         ▼
   ┌───────────────────────┐                 ┌───────────────────────┐
   │ World Builder Agent   │                 │ Character Architect   │
   │ (Rules & Bible)       │                 │ (Voice Fingerprints)  │
   └───────────┬───────────┘                 └───────────┬───────────┘
               │                                         │
               └────────────────────┬────────────────────┘
                                    ▼
                       ┌─────────────────────────┐
                       │ Master Outliner Agent   │
                       │ (Bespoke Book Plan)     │
                       └────────────┬────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Iterative Execution Loop                         │
│                                                                         │
│  ┌─────────────────────────┐             ┌───────────────────────────┐  │
│  │ Prose Drafter Agent     │────────────>│ Adversarial Critic Loop   │  │
│  │ (Beat-by-Beat Scene)    │             │ (Continuity & Anti-Slop)  │  │
│  └─────────────────────────┘             └─────────────┬─────────────┘  │
│               ▲                                        │                │
│               │             Revision Directive         │                │
│               └────────────────────────────────────────┘                │
│                                                        │                │
│                                   Approved             │                │
│                                   ▼                    │                │
│                      ┌───────────────────────────┐     │                │
│                      │ State Memory Engine       │     │                │
│                      │ (Rolling Memory Update)   │     │                │
│                      └───────────────────────────┘     │                │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
                       ┌─────────────────────────┐
                       │ Commercial Export Bridge│
                       │ (DOCX + Validated EPUB3)│
                       └─────────────────────────┘
```

---

## 🔬 In-Depth Engineering & Edge-Case Handling

### 1. DeepSeek-R1 `<think>` Tag Sanitization
Reasoning models like DeepSeek-R1 output extensive inner-monologue reasoning blocks (`<think>...</think>`) before generating response content. `LlmClient._clean_llm_output()` strips reasoning traces and a leading meta preamble (`"Here is the scene:"`) while leaving real opening lines of prose intact.

### 2. SQLite State Persistence (`memory/state_manager.py`)
All intermediate state (brief, world, cast, outline, scenes as they are written, chapters and editor reports) is persisted to the book's own SQLite file (`books/<title>/state.db`). Interrupted runs resume at the next unwritten scene.

### 3. Circuit-Breaker Adversarial Loop
To prevent infinite revision loops when an LLM struggles with a complex constraint, the revision loop is bounded by `--max-revisions`. If a chapter still fails, its strongest version is kept and the failure becomes a blocker in the release report.

---

## 🧭 What Happens to a Book

| Phase | Agent | Output |
|---|---|---|
| 0 | Book Strategist | Target reader, promise, hook, ending, voice guide |
| 1 | World Builder, Character Architect, Master Outliner | Bespoke world, cast and a book-specific chapter and scene plan with setups and payoffs |
| 2 | Prose Drafter | Scene-by-scene prose; the book's first scene competes among several drafts |
| 3 | Developmental Editor + mechanical critics | Rubric scores; only flagged scenes are rewritten, and the best version is kept |
| 3 | Memory Engine | Recaps, threads, character state, relationships, secrets and clue status, read from the full chapter |
| 4 | Book Reviewer | `release_report.md`: PASS or NOT READY with every blocker |
| 5 | Publishing Kit | Store blurb, keywords, categories, cover brief, launch plan, 6x9 print DOCX, EPUB 3 |

Non-fiction gets no invented cast. Uncertain facts are marked `[VERIFY: ...]`, and every checkable claim is listed in `fact_check.md`.

Nothing is fabricated: no fake reviews, bestseller labels, prices or credentials. An ISBN, publisher, dedication or bio appears only if you supply it. If a model cannot produce valid output, the run stops instead of inserting stock content, and it resumes where it stopped.

Each book lives in its own folder:

```
books/<title>/
├── <title>.docx, <title>.epub
├── manuscript/chapter_01.md ...
├── publishing/release_report.md, listing.md, metadata.json, fact_check.md
└── state.db
```

---

## 🚀 Quick Start

```bash
git clone https://github.com/apravint/BookGeneratorAI.git
cd BookGeneratorAI
pip install -r requirements.txt
```

The concept matters more than any setting. Give it something specific and original:

```bash
python3 main.py \
  --title "The Ledger of the Drowned" \
  --concept "A river ferryman finds a waterlogged ledger recording every drowning in his town, including tomorrow's" \
  --genre thriller \
  --author "Your Name" \
  --provider anthropic
```

Try two chapters first to judge quality before paying for a full book:

```bash
python3 main.py -t "Sample Run" -c "Your concept" -n 2 --target-words 5000 --provider ollama
```

Models grade their own prose leniently, so judge with a different, stronger model. This also keeps costs down, because the expensive model only reviews:

```bash
python3 main.py -t "Your Title" -c "Your concept" --provider gemini --editor-provider anthropic
```

If an account runs out of quota or credit, the run stops immediately with a clear message instead of retrying. Rerun the same command to resume.

Set `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` or `GEMINI_API_KEY` for cloud providers. Local models are free, but small ones will rarely clear the editorial bar. Run the same command again to resume.

To add real endorsements, put permissioned quotes in `books/<title>/manuscript/praise.md`.

---

## ⚙️ CLI Options

| Flag | Short | Default | Description |
|---|---|---|---|
| `--title` | `-t` | **Required** | Book title; also identifies the book's folder |
| `--concept` | `-c` | title | Seed concept |
| `--genre` | `-g` | `auto` | Genre, detected from the title when `auto` |
| `--author` | `-a` | `Pravin Tamilan` | Author name |
| `--language` | `-l` | `english` | `english` or `tamil` |
| `--tamil` | | off | Shortcut for `--language tamil` |
| `--provider` | `-p` | auto-detected | `ollama`, `gemini`, `openai`, `anthropic`, `jev` |
| `--model` | `-m` | provider default | Model name |
| `--editor-provider` / `--editor-model` | | same as writer | Separate model that scores chapters, picks the opening and reviews the book |
| `--ollama-url` | | `http://localhost:11434` | Ollama endpoint |
| `--chapters` | `-n` | `24` | Number of chapters |
| `--scenes-per-chapter` | | `4` | Scenes per chapter |
| `--target-words` | | `80000` | Whole-book word target |
| `--max-revisions` | | `2` | Revision passes per chapter |
| `--opening-candidates` | | `3` | Competing drafts of the first scene |
| `--output` / `--epub` | `-o` | book folder | Output paths |
| `--cover` | | none | Cover `.jpg` for the EPUB |
| `--subtitle` `--isbn` `--publisher` `--year` `--dedication` `--author-bio` | | none | Printed only when supplied |
| `--reset` | `-r` | off | Restart this book only |
| `--export-cards` / `--import-lorebook` | | none | Portable character cards and lorebooks |

---

## 🌐 Web Dashboards & Streamlit Studio

### 1. Interactive Streamlit Studio App (`streamlit_app.py`)
Run a modern, multi-tab Streamlit dashboard:

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```
> Launch at **`http://localhost:8501`** to generate books, monitor the pipeline, and download the DOCX, EPUB and release report.

### 2. Built-in REST API & Multi-Book Web Server (`server.py`)
Run a zero-dependency local REST API web server:

```bash
python3 server.py
```
> Access at **`http://localhost:8080`**. It listens on this computer only, because the API starts paid LLM jobs and has no authentication.

---

## 🗺 Future Enterprise Roadmap

We are actively expanding **BookGenerator AI** into an enterprise-grade manuscript generation platform:

- [x] **Phase 1 (Current Engine)**: Multi-agent beat-by-beat scene drafting, context isolation, adversarial anti-slop critics, and local Ollama REST integration.
- [ ] **Phase 2 (Semantic Vector Memory & MCP Server)**: Local vector memory (ChromaDB / FAISS) and a native Model Context Protocol (MCP) server interface for IDE/agent integration.
- [ ] **Phase 3 (Enterprise UI & Streaming)**: Web-based authoring dashboard (Angular) powered by real-time event streaming (Apache Kafka / IBM MQ) for multi-user generation jobs.
- [ ] **Phase 4 (Enterprise Persistence & Multi-Format Exporters)**: Oracle DB enterprise state persistence alongside native `.epub` and publication-ready `.pdf` compilers.

---

## 🤖 AI Assistance & Contribution Guidelines

This repository follows modern AI contribution standards.
- **Human Contributors**: Please review [`CONTRIBUTING.md`](CONTRIBUTING.md) for local setup, fast single-chapter test flags, and PR guidelines.
- **Autonomous AI Agents**: Please inspect [`AGENTS.md`](AGENTS.md) for operational boundaries, mandatory verification commands, and safety rules.

---

## 📜 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.

---

## 👤 About the Author & Lead Architect

**Pravin Tamilan**  
*Vice President & Lead AI Systems Architect* — Chennai, India

Pravin is a technology leader specializing in agentic AI orchestration, Model Context Protocol (MCP) tool design, distributed microservices, and enterprise Spring Boot & Angular architectures.

- **GitHub**: [@apravint](https://github.com/apravint)
- **Specialization**: Enterprise AI Architecture, Multi-Agent Systems, Local Inference Engineering, High-Throughput Stream Processing.
