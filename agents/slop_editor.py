"""
Compatibility shim for AntiSlopEditorAgent.
Re-exports AntiSlopEditorAgent from agents.critics.
"""

from .critics import AntiSlopEditorAgent

__all__ = ["AntiSlopEditorAgent"]
