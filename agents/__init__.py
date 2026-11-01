"""
BookGenerator AI Agents Package
Exports all core agents for the multi-agent long-form manuscript pipeline.
"""

from .book_strategist import BookStrategistAgent
from .book_reviewer import BookReviewer
from .publishing_kit import PublishingKitAgent
from .world_builder import WorldBuilderAgent
from .character_architect import CharacterArchitectAgent
from .master_outliner import MasterOutlinerAgent
from .prose_drafter import ProseDrafterAgent
from .critics import (
    MasterAdversarialReviewer,
    AntiSlopEditorAgent,
    ContinuityEditorAgent,
    DevelopmentalEditorAgent
)

__all__ = [
    "BookStrategistAgent",
    "BookReviewer",
    "PublishingKitAgent",
    "DevelopmentalEditorAgent",
    "WorldBuilderAgent",
    "CharacterArchitectAgent",
    "MasterOutlinerAgent",
    "ProseDrafterAgent",
    "MasterAdversarialReviewer",
    "AntiSlopEditorAgent",
    "ContinuityEditorAgent"
]
