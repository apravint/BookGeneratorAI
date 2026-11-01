"""
LLM Client Module
Provides unified API interfaces for local Ollama, OpenAI, Gemini, Anthropic.
Strictly raises descriptive exceptions on network or API failures (no silent mock fallbacks).
"""

import os
import json
import re
import time
import urllib.request
import urllib.error

RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504, 529}
MAX_ATTEMPTS = 5
REQUEST_TIMEOUT = 600
META_PREAMBLE = re.compile(r"^(okay|ok|sure|certainly|of course|here is|here's|below is|as an ai)\b", re.IGNORECASE)
META_SUBJECT = re.compile(r"\b(chapter|scene|draft|manuscript|prose|revis|rewrit|json|beat|section)", re.IGNORECASE)


class LlmClient:
    def __init__(
        self,
        provider: str = None,
        api_key: str = None,
        model: str = None,
        ollama_url: str = "http://localhost:11434"
    ):
        default_provider = "gemini" if (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")) else "ollama"
        self.provider = (provider or default_provider).lower()
        if self.provider == "default":
            self.provider = default_provider
        if api_key:
            self.api_key = api_key
        else:
            if self.provider == "openai":
                self.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
            elif self.provider == "gemini":
                self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("LLM_API_KEY")
            elif self.provider == "anthropic":
                self.api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("LLM_API_KEY")
            elif self.provider in ["jev", "typesafe"]:
                self.api_key = os.getenv("JEV_API_KEY") or os.getenv("TYPESAFE_API_KEY") or os.getenv("LLM_API_KEY")
            else:
                self.api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

        self.ollama_url = (ollama_url or "http://localhost:11434").rstrip("/")
        self._truncated = False
        
        if self.provider == "ollama":
            self.model = self._resolve_ollama_model(model or os.getenv("OLLAMA_MODEL"))
        elif self.provider in ["jev", "typesafe"]:
            self.model = model or "jev-system1"
        elif self.provider == "gemini":
            self.model = model or os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
        elif self.provider == "anthropic":
            self.model = model or "claude-opus-5-5"
        else:
            self.model = model or "gpt-4o"

    def _resolve_ollama_model(self, user_model: str = None) -> str:
        """Queries local Ollama tags API to resolve model names and installed aliases."""
        target = user_model or "qwen2.5:1.5b"
        try:
            url = f"{self.ollama_url}/api/tags"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
                models = [m.get("name", "") for m in data.get("models", [])]
                if target in models:
                    return target
                # Check tag prefix match (e.g., 'deepseek-r1' -> 'deepseek-r1:latest')
                for m in models:
                    if m == f"{target}:latest" or m.startswith(target):
                        print(f"  [Ollama Tag Resolved] Mapped '{target}' -> installed tag '{m}'")
                        return m
                if models:
                    print(f"  [Ollama Auto-Detect] Target model '{target}' not found. Using installed model '{models[0]}'")
                    return models[0]
        except Exception:
            pass
        return target

    def generate_text(self, prompt: str, system_prompt: str = "", max_tokens: int = 4096) -> str:
        """Generates text; a reply cut off at the token limit is retried once with double the room."""
        text = self._dispatch(prompt, system_prompt, max_tokens)
        if self._truncated:
            print(f"  [LLM Retry] Response hit the {max_tokens}-token limit. Retrying with {max_tokens * 2}...")
            text = self._dispatch(prompt, system_prompt, max_tokens * 2)
            if self._truncated:
                print("  [LLM Warning] Response is still cut off at the token limit.")
        if not text:
            raise RuntimeError(f"{self.provider} returned no text for model '{self.model}'.")
        return text

    def _dispatch(self, prompt: str, system_prompt: str, max_tokens: int) -> str:
        self._truncated = False
        if self.provider == "ollama":
            return self._call_ollama(prompt, system_prompt, max_tokens)
        elif self.provider in ["jev", "typesafe"]:
            return self._call_jev(prompt, system_prompt, max_tokens)
        elif self.provider == "openai":
            return self._call_openai(prompt, system_prompt, max_tokens)
        elif self.provider == "gemini":
            return self._call_gemini(prompt, system_prompt, max_tokens)
        elif self.provider == "anthropic":
            return self._call_anthropic(prompt, system_prompt, max_tokens)
        else:
            raise ValueError(f"Unsupported or unconfigured LLM provider: '{self.provider}'.")

    def _call_jev(self, prompt: str, system_prompt: str, max_tokens: int) -> str:
        """TypeSafe AI Jev System-One Model API Client (70ms Parallel Decision Sampling)."""
        if not self.api_key:
            raise ValueError("JEV_API_KEY environment variable is missing.")
        payload = {
            "model": "jev-system1",
            "state": (system_prompt + "\n\n" + prompt).strip(),
            "questions": ["decision", "classification", "output"]
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        res_data = self._post_json("https://api.typesafe.ai/v1/predict", payload, headers)
        return json.dumps(res_data.get("decisions", {}), ensure_ascii=False)

    def _post_json(self, url: str, payload: dict, headers: dict) -> dict:
        """POST with exponential backoff on rate limits, server errors and dropped connections."""
        body = json.dumps(payload).encode("utf-8")
        last_error = None
        for attempt in range(MAX_ATTEMPTS):
            if attempt:
                delay = min(2 ** attempt, 60)
                print(f"  [LLM Retry] {last_error}. Attempt {attempt + 1}/{MAX_ATTEMPTS} in {delay}s...")
                time.sleep(delay)
            req = urllib.request.Request(url, data=body, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                detail = e.read().decode("utf-8", errors="replace")[:500]
                last_error = f"HTTP {e.code} from {self.provider}: {detail}"
                if e.code not in RETRYABLE_STATUS:
                    break
            except (urllib.error.URLError, TimeoutError, ConnectionError, json.JSONDecodeError) as e:
                last_error = f"{self.provider} request failed: {e}"
        raise RuntimeError(f"LLM call failed for model '{self.model}': {last_error}")

    def _call_ollama(self, prompt: str, system_prompt: str, max_tokens: int) -> str:
        url = f"{self.ollama_url}/api/chat"
        headers = {"Content-Type": "application/json"}
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        ctx_size = 8192 if any(m in self.model for m in ["1.5b", "0.5b", "3b"]) else 16384
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": max_tokens,
                "num_ctx": ctx_size
            }
        }


        try:
            res_data = self._post_json(url, payload, headers)
        except RuntimeError as e:
            raise RuntimeError(
                f"{e}\nPlease ensure Ollama is running (`ollama serve`) at {self.ollama_url} "
                f"and model '{self.model}' is pulled (`ollama run {self.model}`)."
            )
        self._truncated = res_data.get("done_reason") == "length"
        return self._require_text(res_data.get("message", {}).get("content", ""), res_data)

    def _call_openai(self, prompt: str, system_prompt: str, max_tokens: int) -> str:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is missing.")
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model or "gpt-4o",
            "messages": [
                {"role": "system", "content": system_prompt or "You are an award-winning author."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        res_data = self._post_json(url, payload, headers)
        choices = res_data.get("choices") or [{}]
        self._truncated = choices[0].get("finish_reason") == "length"
        return self._require_text(choices[0].get("message", {}).get("content", ""), res_data)

    def _call_gemini(self, prompt: str, system_prompt: str, max_tokens: int) -> str:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is missing.")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model or 'gemini-3.5-flash-lite'}:generateContent"
        headers = {"Content-Type": "application/json", "x-goog-api-key": self.api_key}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.7}
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
        res_data = self._post_json(url, payload, headers)
        candidates = res_data.get("candidates") or [{}]
        self._truncated = candidates[0].get("finishReason") == "MAX_TOKENS"
        parts = candidates[0].get("content", {}).get("parts", [])
        return self._require_text("".join(p.get("text", "") for p in parts if not p.get("thought")), res_data)

    def _call_anthropic(self, prompt: str, system_prompt: str, max_tokens: int) -> str:
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is missing.")
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": [{"role": "user", "content": prompt}]
        }
        res_data = self._post_json(url, payload, headers)
        self._truncated = res_data.get("stop_reason") == "max_tokens"
        text = "".join(b.get("text", "") for b in res_data.get("content", []) if b.get("type") == "text")
        return self._require_text(text, res_data)

    def _require_text(self, text: str, res_data: dict) -> str:
        cleaned = self._clean_llm_output(text)
        # A model can spend its whole allowance on thinking; generate_text retries that case
        if not cleaned and not self._truncated:
            raise RuntimeError(f"{self.provider} returned no text for model '{self.model}': {json.dumps(res_data)[:500]}")
        return cleaned

    def _clean_llm_output(self, text: str) -> str:
        if not text:
            return ""
        # 1. Strip DeepSeek R1 reasoning blocks <think>...</think>, including an unopened closing tag
        cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        cleaned = re.sub(r'^.*?</think>', '', cleaned, flags=re.DOTALL).strip()

        # 2. Strip one leading conversational preamble; opening lines of real prose must survive
        first_line, _, rest = cleaned.partition('\n')
        first = first_line.strip()
        if META_PREAMBLE.match(first) and (first.endswith(':') or META_SUBJECT.search(first)):
            cleaned = rest.strip()
        return re.sub(r'^-{3,}\s*\n', '', cleaned).strip()


# Backward compatibility alias
LLMClient = LlmClient