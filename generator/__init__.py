"""
BookGenerator AI Engine Package
Exports core generation, compilation, and LLM communication utilities.
"""

from .llm_client import LlmClient, LLMClient
from .blueprint import BookBlueprint, BLUEPRINTS, get_blueprint_for_genre, TAMIL_GENRES
from .docx_compiler import compile_book, compile_book_to_docx
from .writer import ChapterWriter
from .editor import DevelopmentalEditor

__version__ = "4.0.0"

__all__ = [
    "LlmClient",
    "LLMClient",
    "BookBlueprint",
    "BLUEPRINTS",
    "get_blueprint_for_genre",
    "TAMIL_GENRES",
    "compile_book",
    "compile_book_to_docx",
    "ChapterWriter",
    "DevelopmentalEditor"
]
