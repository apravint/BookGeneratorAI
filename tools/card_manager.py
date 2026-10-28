"""
Card Manager Tool - Portable Lorebook and Character Card Import/Export.
Inspired by MuMuAINovel's card management system and open lorebook standards.
Enables importing and exporting Character Cards, World Bibles, and Lorebooks
in JSON and structured Markdown across projects.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from schemas.models import (
    CharacterProfile,
    CharacterRegistry,
    CharacterVoice,
    CharacterRelation,
    WorldBible,
    WorldRule,
)


class CardManager:
    """Manages serialization, import, and export of character cards and world lorebooks."""

    @staticmethod
    def export_character_card(
        character: CharacterProfile,
        output_path: str | Path,
        format: str = "json"
    ) -> Path:
        """Exports a CharacterProfile to a portable card file (.json or .md)."""
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        if format.lower() == "markdown" or out.suffix.lower() == ".md":
            md_content = f"""# Character Card: {character.name}
- **ID:** `{character.character_id}`
- **Role:** {character.role}
- **Core Motivation:** {character.core_motivation}
- **Fatal Flaw:** {character.fatal_flaw}
- **Arc Trajectory:** {character.arc_trajectory}

## Backstory
{character.backstory_summary}

## Voice Fingerprint
- **Tone:** {character.voice_fingerprint.tone}
- **Sentence Structure:** {character.voice_fingerprint.sentence_structure}
- **Signature Vocabulary:** {", ".join(character.voice_fingerprint.frequently_used_terms) if character.voice_fingerprint.frequently_used_terms else "None"}
- **Taboo Phrases:** {", ".join(character.voice_fingerprint.taboo_phrases) if character.voice_fingerprint.taboo_phrases else "None"}

## Established Relationships
"""
            for target, rel_desc in character.relationships.items():
                md_content += f"- **{target}:** {rel_desc}\n"
            out.write_text(md_content, encoding="utf-8")
        else:
            card_dict = {
                "schema_version": "1.0",
                "card_type": "character",
                "data": character.model_dump()
            }
            out.write_text(json.dumps(card_dict, indent=2, ensure_ascii=False), encoding="utf-8")

        return out

    @staticmethod
    def import_character_card(file_path: str | Path) -> CharacterProfile:
        """Imports a character card from a JSON file."""
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Character card file not found: {path}")

        raw = json.loads(path.read_text(encoding="utf-8"))
        data = raw.get("data", raw)
        return CharacterProfile.model_validate(data)

    @staticmethod
    def export_lorebook(
        bible: WorldBible,
        registry: CharacterRegistry,
        relationships: Optional[List[CharacterRelation]] = None,
        output_path: str | Path = "lorebook.json"
    ) -> Path:
        """Exports an entire book's world, character registry, and relationship matrix to a portable lorebook pack."""
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        pack = {
            "schema_version": "1.0",
            "pack_type": "lorebook",
            "world_bible": bible.model_dump(),
            "characters": registry.model_dump()["characters"],
            "relationships": [r.model_dump() for r in relationships] if relationships else []
        }
        out.write_text(json.dumps(pack, indent=2, ensure_ascii=False), encoding="utf-8")
        return out

    @staticmethod
    def import_lorebook(
        file_path: str | Path
    ) -> Tuple[WorldBible, CharacterRegistry, List[CharacterRelation]]:
        """Imports a full lorebook pack containing WorldBible, CharacterRegistry, and CharacterRelations."""
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Lorebook file not found: {path}")

        raw = json.loads(path.read_text(encoding="utf-8"))
        bible_data = raw.get("world_bible", {})
        characters_data = raw.get("characters", [])
        relations_data = raw.get("relationships", [])

        bible = WorldBible.model_validate(bible_data)
        registry = CharacterRegistry(characters=[CharacterProfile.model_validate(c) for c in characters_data])
        relations = [CharacterRelation.model_validate(r) for r in relations_data]

        return bible, registry, relations
