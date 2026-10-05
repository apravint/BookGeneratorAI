# BookGenerator AI 📚🤖
### Executive-Grade Multi-Agent Long-Form Book Generation Engine (Local Ollama & Open Models)

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2-emerald.svg)](https://docs.pydantic.dev/)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20Inference-black.svg)](https://ollama.com)
[![DeepSeek R1](https://img.shields.io/badge/Model-DeepSeek--R1-purple.svg)](https://ollama.com/library/deepseek-r1)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![AGENTS.md](https://img.shields.io/badge/AI--Standards-AGENTS.md-blueviolet.svg)](AGENTS.md)

**BookGenerator AI** is an open-source, production-grade multi-agent engine engineered to solve the hardest challenge in generative AI: **autonomously drafting complete, publication-ready 300-page commercial manuscripts (80,000+ words) without context collapse or prose degradation.**

---

## 🏛 Executive Summary: The Engineering Challenge

### The Problem with Single-Prompt Long-Form AI Generation
Standard LLM wrappers fail catastrophically when tasked with long-form writing:
1. **Context degradation & Token Exhaustion**: Context windows overflow around 2,000–4,000 words, causing models to forget previous character developments, plot arcs, and established world constraints.
2. **Repetitive Tropes ("AI Slop")**: Models default to repetitive filler phrases (*"a testament to"*, *"tapestry of"*, *"shivers down her spine"*, *"a palpable tension"*) and forced moralizing summary conclusions.
3. **Hallucinatory Drift**: Without strict state isolation, characters swap voice patterns, break world rules, or solve major plot points prematurely.

### The Architectural Solution
`BookGeneratorAI` implements an enterprise-grade multi-agent architecture featuring:
- **Hierarchical State Isolation**: The drafting agent receives *only* the current scene micro-beat, active character voice fingerprints, and a 1,200-word rolling memory summary—never the full 80,000-word history.
- **Beat-by-Beat Iterative Scene Generator**: Chapters are decomposed into 6 sub-beats (600–900 words each), guaranteeing rich sensory grounding and avoiding model context ceilings.
- **Adversarial Anti-Slop & Continuity Critics**: An independent reviewer agent audits every drafted chapter against banned tropes and character voice fingerprints, issuing mandatory revision briefs before state commitment.

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
                       │ (4-Part, 12 Chapters)   │
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
                       │ Commercial DOCX Bridge  │
                       │ (Dynamic TOC & Index)   │
                       └─────────────────────────┘
```

---

## 🔬 In-Depth Engineering & Edge-Case Handling

### 1. DeepSeek-R1 `<think>` Tag Sanitization
Reasoning models like DeepSeek-R1 output extensive inner-monologue reasoning blocks (`<think>...</think>`) before generating response content. `LlmClient._clean_llm_output()` implements a robust multi-pass regex filter (`re.DOTALL`) that strips reasoning traces, conversational preambles (`"Okay, let's write..."`), and prompt meta-leakage without corrupting structured JSON schemas or Markdown prose headings.

### 2. SQLite State Persistence (`memory/state_manager.py`)
To protect long-running generations (which can take 30–60 minutes locally), all intermediate states—`WorldBible`, `CharacterRegistry`, `MasterOutline`, chapter drafts, and critic revision briefs—are persisted transactionally to SQLite (`memory/book_state.db`). Interrupted runs can resume instantly without re-generating prior chapters.

### 3. Circuit-Breaker Adversarial Loop
To prevent infinite revision loops when an LLM struggles with a complex constraint, `MasterAdversarialReviewer` enforces strict revision bounds (`max-revisions`, default 1–2 passes). If a draft fails audit after max attempts, the system logs the residual warnings, applies non-blocking text cleanup, and safely advances state.

---

## 🚀 Quick Start

### 1. Prerequisites & Installation
Ensure Python 3.10+ and [Ollama](https://ollama.com) are installed.

```bash
git clone https://github.com/apravint/BookGeneratorAI.git
cd BookGeneratorAI
pip install -r requirements.txt
```

Ensure your target model is pulled in Ollama (e.g. DeepSeek-R1):
```bash
ollama pull deepseek-r1:latest
```

### 2. Basic Usage

#### Generate a Full Fiction Novel (Offline via Local Ollama)
```bash
python3 main.py \
  --title "The Love Story" \
  --genre fiction \
  --author "Pravin Tamilan" \
  --provider ollama \
  --model "deepseek-r1:latest" \
  --reset \
  --output "The_Love_Story.docx"
```

#### Generate a Non-Fiction Architecture Book
```bash
python3 main.py \
  --title "Building Distributed Stream Engines" \
  --genre technical \
  --author "Pravin Tamilan" \
  --provider ollama \
  --model "deepseek-r1:latest" \
  --reset \
  --output "Distributed_Streams.docx"
```

#### Cloud LLM Providers (OpenAI, Gemini, Anthropic)
```bash
export OPENAI_API_KEY="your-api-key"

python3 main.py \
  --title "The Exponential Leader" \
  --genre business \
  --author "Pravin Tamilan" \
  --provider openai \
  --model "gpt-4o" \
  --output "Exponential_Leader.docx"
```

---

## ⚙️ CLI Options

| Flag | Short | Default | Description |
|---|---|---|---|
| `--title` | `-t` | **Required** | Book title |
| `--concept` | `-c` | `""` | Seed concept or story prompt |
| `--language` | `-l` | `english` | Primary language (`tamil` / `english`) |
| `--tamil` | | `False` | Preset flag for Tamil language book generation |
| `--genre` | `-g` | `auto` | Genre (`tamil_historical`, `tamil_thirukkural`, `tamil_kavithai`, `tamil_fiction`, `fiction`, `business`) |
| `--author` | `-a` | `Pravin Tamilan` | Author name for title page & headers |
| `--provider` | `-p` | `ollama` | Provider (`ollama`, `gemini`, `openai`, `anthropic`, `jev`) |
| `--model` | `-m` | `deepseek-r1:latest` | Target LLM model |
| `--ollama-url` | | `http://localhost:11434` | Local Ollama REST endpoint |
| `--reset` | `-r` | `False` | Clean database (`memory/book_state.db`) & previous outputs before running |
| `--max-revisions` | | `1` | Max critic revision loops per chapter |
| `--output` | `-o` | `Generated_Book.docx` | Output path for `.docx` compilation |

---

## 🌐 Web Dashboards & Streamlit Studio

### 1. Interactive Streamlit Studio App (`streamlit_app.py`)
Run a modern, multi-tab Streamlit dashboard:

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```
> Launch at **`http://localhost:8501`** to generate books, monitor live pipeline execution, read chapters, and download DOCX files.

### 2. Built-in REST API & Multi-Book Web Server (`server.py`)
Run a zero-dependency local REST API web server:

```bash
python3 server.py
```
> Access at **`http://localhost:8080`** for live 5-node agent pipeline monitoring and multi-book job creation.

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
