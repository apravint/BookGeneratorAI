"""
Robust JSON Parser & Sanitizer Module
Extracts, cleans, repairs, and parses structured JSON output from LLM completions.
Handles trailing commas, markdown fences, unescaped characters, and deepseek-r1 reasoning blocks.
"""

import json
import re
from typing import Any, Callable, Optional, Type
from pydantic import BaseModel


def clean_json_string(text: str) -> str:
    """Cleans raw LLM response text into a valid JSON string candidate."""
    if not text or not text.strip():
        return ""

    # 1. Strip reasoning blocks
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    text = re.sub(r'<thought>.*?</thought>', '', text, flags=re.DOTALL)
    text = re.sub(r'^.*?</think>', '', text, flags=re.DOTALL)

    # 2. Extract markdown code block if present
    if "```json" in text:
        text = text.split("```json", 1)[1].split("```", 1)[0]
    elif "```" in text:
        text = text.split("```", 1)[1].split("```", 1)[0]

    # 3. Match outermost JSON structure ({...} or [...])
    obj_match = re.search(r'(\{[\s\S]*\})', text)
    arr_match = re.search(r'(\[[\s\S]*\])', text)

    candidate = text.strip()
    if obj_match and arr_match:
        # Choose the one starting earlier
        if obj_match.start() < arr_match.start():
            candidate = obj_match.group(1).strip()
        else:
            candidate = arr_match.group(1).strip()
    elif obj_match:
        candidate = obj_match.group(1).strip()
    elif arr_match:
        candidate = arr_match.group(1).strip()

    return candidate


def _load_json(candidate: str) -> Any:
    """Parses strictly first so valid strings containing smart quotes or commas stay untouched."""
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass
    # Remove trailing commas before closing braces/brackets
    repaired = re.sub(r',\s*([\]\}])', r'\1', candidate)
    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        pass
    # Last resort: model used smart quotes as JSON delimiters
    repaired = repaired.replace('“', '"').replace('”', '"').replace('’', "'").replace('‘', "'")
    return json.loads(repaired)


def parse_llm_json(text: str, model_class: Optional[Type[BaseModel]] = None) -> Optional[Any]:
    """
    Parses LLM output into a dictionary or Pydantic model.
    Returns parsed object or None if unparseable.
    """
    if not text or not text.strip():
        return None

    cleaned = clean_json_string(text)
    if not cleaned or not (cleaned.startswith('{') or cleaned.startswith('[')):
        return None

    data = None

    try:
        data = _load_json(cleaned)
    except json.JSONDecodeError:
        # Secondary repair attempt: strip leading/trailing garbage
        try:
            first_brace = cleaned.find('{')
            last_brace = cleaned.rfind('}')
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                data = _load_json(cleaned[first_brace:last_brace + 1])
        except Exception:
            return None

    if data is None:
        return None

    if model_class is not None:
        try:
            return model_class.model_validate(data)
        except Exception:
            return None

    return data


class StructuredOutputError(RuntimeError):
    """The model never produced output that satisfied the requested schema."""


def generate_validated(
    llm,
    prompt: str,
    system_prompt: str,
    model_class: Type[BaseModel],
    validator: Optional[Callable[[Any], Optional[str]]] = None,
    max_tokens: int = 4096,
    attempts: int = 3,
) -> Any:
    """
    Requests JSON, validating it and feeding each failure back to the model.
    validator returns a problem description, or None when the object is acceptable.
    Raises StructuredOutputError instead of inventing content.
    """
    problem = ""
    for _ in range(attempts):
        correction = f"\n\nYOUR PREVIOUS RESPONSE WAS REJECTED: {problem}\nReturn ONLY corrected raw JSON." if problem else ""
        text = llm.generate_text(prompt + correction, system_prompt=system_prompt, max_tokens=max_tokens)
        parsed = parse_llm_json(text, model_class=model_class) if isinstance(text, str) else None
        if parsed is None:
            problem = "It was not valid JSON matching the requested schema."
            continue
        problem = validator(parsed) if validator else None
        if not problem:
            return parsed
    raise StructuredOutputError(f"{model_class.__name__} rejected after {attempts} attempts: {problem}")
