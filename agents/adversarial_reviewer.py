"""
Compatibility shim for MasterAdversarialReviewer.
Re-exports MasterAdversarialReviewer from agents.critics.
"""

from .critics import MasterAdversarialReviewer

__all__ = ["MasterAdversarialReviewer"]
