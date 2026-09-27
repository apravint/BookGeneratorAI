# Contributing to BookGenerator AI 📚✨

Thank you for your interest in contributing to **BookGenerator AI**! We are building the open-source standard for local, multi-agent long-form AI book generation.

Whether you want to add support for new LLM runners, refine anti-slop tropes, add export formats, or build web interfaces, your contributions are welcome!

---

## 🚀 Quickstart for Developers

### 1. Fork & Clone
```bash
git clone https://github.com/apravint/BookGeneratorAI.git
cd BookGeneratorAI
```

### 2. Set Up Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Fast Single-Chapter Test Run
Don't waste time generating full 12-chapter books during development! Run a single-chapter generation test:
```bash
python3 main.py \
  --title "Test Book" \
  --genre fiction \
  --author "Pravin Tamilan" \
  --provider ollama \
  --model "deepseek-r1:latest" \
  --reset \
  --output "output/Test_Run.docx"
```

---

## 🎯 Good First Issues for New Contributors

Looking for a manageable task to get started? Check out our open issues labeled `good first issue` or pick one of these candidate tasks:

1. **`AntiSlopEditorAgent` Unit Tests**: Write unit tests in `tests/test_critics.py` testing regex detection of banned phrases and preachy endings.
2. **EPUB / PDF Exporter**: Extend `generator/docx_compiler.py` or add `generator/epub_compiler.py` to compile Markdown output directly to `.epub` or `.pdf`.
3. **Interactive CLI Menu**: Add an interactive terminal prompt using `rich` or `questionary` when `main.py` is called with no arguments.
4. **LM Studio / vLLM API Adapter**: Extend `generator/llm_client.py` to natively support LM Studio (`http://localhost:1234/v1`) and vLLM endpoints.

---

## 📋 Pull Request Guidelines

1. **Keep PRs Focused**: Keep pull requests centered on a single feature or bug fix.
2. **Verify Code Syntax**: Ensure all Python files compile cleanly before opening a PR:
   ```bash
   python3 -m py_compile main.py generator/*.py agents/*.py schemas/*.py memory/*.py tools/*.py
   ```
3. **Adhere to Architecture Principles**:
   - **No Silent Fallbacks**: Raise explicit exceptions rather than silently outputting dummy text.
   - **Context Isolation**: Maintain strict separation between agent prompt windows.
   - **Anti-Slop Directives**: Preserve strict guardrails against AI writing tropes.

---

## 🤝 Maintainer Commitment

We promise to review incoming PRs promptly within **24–48 hours**. Clear maintainer feedback and rapid merge cycles keep open-source development fun and efficient.

Thank you for helping us empower authors with 100% private, local AI generation! 🚀
