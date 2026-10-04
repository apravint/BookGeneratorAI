"""
BookGenerator AI Agents Package
Exports all core agents for the multi-agent long-form manuscript pipeline.
"""

from .world_builder import WorldBuilderAgent
from .character_architect import CharacterArchitectAgent
from .master_outliner import MasterOutlinerAgent
from .prose_drafter import ProseDrafterAgent
from .critics import (
    MasterAdversarialReviewer,
    AntiSlopEditorAgent,
    ContinuityEditorAgent
)

__all__ = [
    "WorldBuilderAgent",
    "CharacterArchitectAgent",
    "MasterOutlinerAgent",
    "ProseDrafterAgent",
    "MasterAdversarialReviewer",
    "AntiSlopEditorAgent",
    "ContinuityEditorAgent"
]
