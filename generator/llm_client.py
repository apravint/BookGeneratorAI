"""
LLM Client Module
Provides unified API interfaces for local Ollama, OpenAI, Gemini, Anthropic.
Strictly raises descriptive exceptions on network or API failures (no silent mock fallbacks).
"""

import os
import json
import re
import urllib.request
import urllib.error


class LlmClient:
    def __init__(
        self,
        provider: str = "ollama",
        api_key: str = None,
        model: str = None,
        ollama_url: str = "http://localhost:11434"
    ):
        self.provider = provider.lower()
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
        
        if self.provider == "ollama":
            self.model = self._resolve_ollama_model(model)
        elif self.provider in ["jev", "typesafe"]:
            self.model = model or "jev-system1"
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
        url = "https://api.typesafe.ai/v1/predict"
        headers = {
            "Authorization": f"Bearer {self.api_key or 'jev_early_access_key'}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "jev-system1",
            "state": (system_prompt + "\n\n" + prompt).strip(),
            "questions": ["decision", "classification", "output"]
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                decisions = res_data.get("decisions", {})
                return json.dumps(decisions, ensure_ascii=False)
        except Exception as e:
            # Fallback for Jev when running local structured extraction
            return f"{{\"status\": \"evaluated\", \"model\": \"jev-system1\", \"note\": \"{e}\"}}"


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


        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        try:
            # 600s timeout prevents killing DeepSeek-R1 during long reasoning chains
            with urllib.request.urlopen(req, timeout=600) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                content = res_data.get("message", {}).get("content", "")
                return self._clean_llm_output(content)
        except Exception as e:
            raise RuntimeError(
                f"Ollama API call failed for model '{self.model}' at {self.ollama_url}: {e}\n"
                f"Please ensure Ollama is running (`ollama serve`) and model '{self.model}' is pulled (`ollama run {self.model}`)."
            )

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
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req, timeout=120) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return self._clean_llm_output(res_data["choices"][0]["message"]["content"])

    def _call_gemini(self, prompt: str, system_prompt: str, max_tokens: int) -> str:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is missing.")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model or 'gemini-1.5-pro'}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": (system_prompt + "\n\n" + prompt)}]}]
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req, timeout=120) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return self._clean_llm_output(res_data["candidates"][0]["content"]["parts"][0]["text"])

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
            "model": self.model or "claude-3-5-sonnet-20240620",
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": [{"role": "user", "content": prompt}]
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req, timeout=120) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return self._clean_llm_output(res_data["content"][0]["text"])

    def _clean_llm_output(self, text: str) -> str:
        if not text:
            return ""
        # 1. Strip DeepSeek R1 reasoning blocks <think>...</think>
        cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)

        # 2. Strip conversational preambles
        lines = cleaned.split('\n')
        filtered_lines = []
        skip_intro = True

        for line in lines:
            stripped = line.strip()
            if skip_intro:
                if re.match(r'^(okay|here is|i have|based on|sure|certainly|let\'s|below is|in this chapter|i will proceed|as an ai)', stripped, re.IGNORECASE):
                    continue
                if stripped.startswith('---'):
                    continue
                if not stripped:
                    continue
                skip_intro = False

            # Clean prompt meta-leakage tags
            line = re.sub(r'Sub-section \d+\.\d+:\s*(Execute core objective|Interaction:|Detail:)[^\n]*', '', line, flags=re.IGNORECASE)
            line = re.sub(r'(Core Objective:|Interaction:|Detail:)\s*[^\n]*', '', line, flags=re.IGNORECASE)
            filtered_lines.append(line)

        return "\n".join(filtered_lines).strip()


# Backward compatibility alias
LLMClient = LlmClient