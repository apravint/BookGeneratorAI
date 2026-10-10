"""
Robust JSON Parser & Sanitizer Module
Extracts, cleans, repairs, and parses structured JSON output from LLM completions.
Handles trailing commas, markdown fences, unescaped characters, and deepseek-r1 reasoning blocks.
"""

import json
import re
from typing import Any, Optional, Type
from pydantic import BaseModel


def clean_json_string(text: str) -> str:
    """Cleans raw LLM response text into a valid JSON string candidate."""
    if not text or not text.strip():
        return ""

    # 1. Strip reasoning blocks
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    text = re.sub(r'<thought>.*?</thought>', '', text, flags=re.DOTALL)

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

    # 4. Remove trailing commas before closing braces/brackets
    candidate = re.sub(r',\s*([\]\}])', r'\1', candidate)

    # 5. Replace smart quotes with standard double quotes
    candidate = candidate.replace('“', '"').replace('”', '"').replace('’', "'").replace('‘', "'")

    return candidate


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
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # Secondary repair attempt: strip leading/trailing garbage
        try:
            # Try finding substring between first { and last }
            first_brace = cleaned.find('{')
            last_brace = cleaned.rfind('}')
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                sub = cleaned[first_brace:last_brace + 1]
                sub = re.sub(r',\s*([\]\}])', r'\1', sub)
                data = json.loads(sub)
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
