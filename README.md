# BookGenerator AI 📚🤖
### Production-Grade Multi-Agent Long-Form Book Generation Engine (Local Ollama & Open Models)

**BookGenerator AI** is an open-source, multi-agent AI architecture designed to autonomously generate complete, commercial-grade long-form manuscripts (300+ pages / 80,000+ words) using local LLMs (via Ollama) or cloud providers.

Unlike basic blog generators or single-prompt wrappers, **BookGenerator AI** solves the core challenges of long-form AI authorship: **context collapse, narrative drift, repetitive prose, and generic LLM tropes ("AI slop")**. It uses a hierarchical multi-agent workflow with context isolation, rolling narrative memory, beat-by-beat scene generation, and an adversarial critic loop.

---

## ⚡ The Adversarial Hook: Before & After Critic Audit

Standard LLMs default to generic clichés and preachy moral summary endings. **BookGenerator AI**'s `AntiSlopEditorAgent` actively intercepts and rewrites prose:

```diff
- RAW OLLAMA PROSE:
- "The quiet night was a testament to their unshakeable bond. Shivers ran down Clara's spine as a palpable tension filled the courtyard. Little did they know, their journey had only just begun. In conclusion, they learned that love conquers all."

+ ADVERSARIAL CRITIC REFINED PROSE:
+ "The courtyard fell quiet under the cold starlight. Clara gripped the stone archway, her knuckles pale against the damp granite. Julian didn't step back; he closed the distance between them until his breathing matched her own."
```

---

## 🌟 Key Highlights

### 1. 🔒 100% Private, Offline & Zero API Cost
Run full-length novel and non-fiction book generation completely on your local machine using **Ollama** (`deepseek-r1:latest`, `llama3.1`, `qwen2.5`, `mistral`). Keep your IP completely private with zero API costs.

### 2. 🤺 Adversarial Anti-Slop & Continuity Critics
A dedicated critic agent continuously audits drafted prose against forbidden tropes (e.g., *"a testament to"*, *"tapestry of"*, *"shivers down her spine"*, *"a palpable tension"*, *"little did they know"*, or preachy moralizing conclusions). If slop or voice fingerprint violations are detected, the critic issues actionable revision directives before approving the chapter.

### 3. 🎯 Beat-by-Beat Iterative Scene Drafter
Prevents LLM context degradation and token limits by breaking chapters into 6 granular sub-beats (600–900 words each). Scene drafters receive isolated context windows containing:
- Master World Bible rules & consequences
- Active character voice fingerprints & taboo phrases
- Rolling narrative memory (`Story So Far`)
- Current scene micro-beats & sensory anchors

### 4. 📖 Publication-Ready Commercial Compiler
Generates publication-ready Microsoft Word (`.docx`) documents complete with front/back title pages, dynamic multi-page Table of Contents, formatted chapter headers, and a dynamic concept index.

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
| `--genre` | `-g` | `auto` | Genre (`fiction`, `romance`, `business`, `technical`, `self-help`) |
| `--author` | `-a` | `Pravin Tamilan` | Author name for title page & headers |
| `--provider` | `-p` | `ollama` | Provider (`ollama`, `openai`, `gemini`, `anthropic`) |
| `--model` | `-m` | `deepseek-r1:latest` | Target LLM model |
| `--ollama-url` | | `http://localhost:11434` | Local Ollama REST endpoint |
| `--reset` | `-r` | `False` | Clean database (`memory/book_state.db`) & previous outputs before running |
| `--max-revisions` | | `1` | Max critic revision loops per chapter |
| `--output` | `-o` | `Generated_Book.docx` | Output path for `.docx` compilation |

---

## 🗺 Project Architectural Roadmap

We are actively expanding **BookGenerator AI** into the premier local-first book creation suite:

- [x] **Phase 1 (Current Release)**: Multi-agent beat-by-beat scene drafting, context isolation, adversarial anti-slop critics, and local Ollama REST integration.
- [ ] **Phase 2 (Semantic Vector Memory)**: Integration with local vector stores (ChromaDB / FAISS) for long-range semantic memory retrieval across 100k+ word manuscripts.
- [ ] **Phase 3 (Multi-Format Export)**: Native `.epub` and publication-ready `.pdf` compilation alongside `.docx`.
- [ ] **Phase 4 (Local Web UI)**: Lightweight local Web interface (FastAPI + React / Streamlit) for non-technical authors to review scene beats and trigger revisions visually.

---

## 🤝 Contributing

We welcome community contributions! Please check out [`CONTRIBUTING.md`](file:///Users/pravin/Code/BookGeneratorAI/CONTRIBUTING.md) for local environment setup, fast single-chapter test runs, and guidelines.

Good candidate issues labeled `good first issue`:
- Adding EPUB / PDF exporters.
- Writing unit tests for `AntiSlopEditorAgent` regex patterns.
- Adding interactive CLI prompts via `rich` / `questionary`.
- Building adapters for LM Studio or vLLM endpoints.

---

## 📜 License

Distributed under the **MIT License**. See `LICENSE` for more information.

---

## 👤 Author & Maintainer

**Pravin Tamilan**
- GitHub: [@apravint](https://github.com/apravint)
