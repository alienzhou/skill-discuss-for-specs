"""
Common utilities for meta.yaml parsing and manipulation.

Schema:
- topic: Auto-derived from directory name
- created: ISO date string
- current_round: Session-based round counting
- config: stale_threshold (default 3)
- decisions: Array of {path, name, last_modified, last_updated_round}
- notes: Array of {path, name, last_modified, last_updated_round}
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


# Default staleness threshold (rounds without update before reminding)
DEFAULT_STALE_THRESHOLD = 3


def load_meta(discuss_path: str) -> Optional[Dict[str, Any]]:
    """
    Load meta.yaml from discussion directory.
    
    Args:
        discuss_path: Path to discussion directory
        
    Returns:
        Dictionary containing meta data, or None if file doesn't exist
    """
    meta_path = Path(discuss_path) / "meta.yaml"
    
    if not meta_path.exists():
        return None
    
    with open(meta_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_meta(discuss_path: str, meta: Dict[str, Any]) -> None:
    """
    Save meta.yaml to discussion directory.
    
    Args:
        discuss_path: Path to discussion directory
        meta: Dictionary containing meta data
    """
    meta_path = Path(discuss_path) / "meta.yaml"
    
    with open(meta_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(meta, f, sort_keys=False, allow_unicode=True)


def create_initial_meta(topic: Optional[str] = None) -> Dict[str, Any]:
    """
    Create initial meta.yaml content.
    
    Args:
        topic: Topic name (defaults to None, should be set from directory)
        
    Returns:
        Dictionary with initial meta structure
    """
    return {
        "topic": topic or "",
        "created": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "current_round": 0,
        "config": {
            "stale_threshold": DEFAULT_STALE_THRESHOLD,
        },
        "decisions": [],
        "notes": [],
    }


def ensure_meta_structure(meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure meta has all required fields, adding defaults if missing.
    
    Args:
        meta: Existing meta dictionary
        
    Returns:
        Meta dictionary with all required fields
    """
    if "current_round" not in meta:
        meta["current_round"] = 0
    
    if "config" not in meta:
        meta["config"] = {}
    
    config = meta["config"]
    if "stale_threshold" not in config:
        config["stale_threshold"] = DEFAULT_STALE_THRESHOLD
    
    if "decisions" not in meta:
        meta["decisions"] = []
    
    if "notes" not in meta:
        meta["notes"] = []
    
    return meta


def get_current_round(meta: Dict[str, Any]) -> int:
    """
    Get current round number from meta.
    
    Args:
        meta: Meta dictionary
        
    Returns:
        Current round number (default 0)
    """
    return meta.get("current_round", 0)


def check_stale_status(meta: Dict[str, Any]) -> List[Tuple[str, int, bool]]:
    """
    Check for stale file status (not updated for a while).
    
    Args:
        meta: Meta dictionary
        
    Returns:
        List of tuples: (file_type, stale_rounds, is_force_update)
    """
    meta = ensure_meta_structure(meta)
    
    current_round = get_current_round(meta)
    config = meta.get("config", {})
    threshold = config.get("stale_threshold", DEFAULT_STALE_THRESHOLD)
    force_threshold = threshold * 2  # Force at 2x the suggest threshold
    
    stale_items = []
    
    # Check decisions array
    for decision in meta.get("decisions", []):
        last_updated = decision.get("last_updated_round", 0)
        stale_rounds = current_round - last_updated
        if stale_rounds >= threshold:
            is_force = stale_rounds >= force_threshold
            stale_items.append(("decisions", stale_rounds, is_force))
            break  # Only report once per category
    
    # Check notes array
    for note in meta.get("notes", []):
        last_updated = note.get("last_updated_round", 0)
        stale_rounds = current_round - last_updated
        if stale_rounds >= threshold:
            is_force = stale_rounds >= force_threshold
            stale_items.append(("notes", stale_rounds, is_force))
            break  # Only report once per category
    
    return stale_items


def format_stale_reminder(stale_items: List[Tuple[str, int, bool]], discuss_path: str) -> str:
    """
    Format a reminder message for stale items.
    
    Args:
        stale_items: List of (file_type, stale_rounds, is_force) tuples
        discuss_path: Path to discussion directory for context
        
    Returns:
        Formatted reminder message
    """
    if not stale_items:
        return ""
    
    # Check if any item is force update
    has_force = any(item[2] for item in stale_items)
    
    if has_force:
        header = "## ⚠️ Precipitation Required\n\n"
        header += "The following discussion files have not been updated for too long:\n\n"
    else:
        header = "## 💡 Precipitation Suggestion\n\n"
        header += "The following discussion files may need updating:\n\n"
    
    items_text = ""
    for file_type, stale_runs, is_force in stale_items:
        status = "[REQUIRED]" if is_force else "[Suggested]"
        items_text += f"- {status} `{file_type}` - {stale_runs} rounds since last update\n"
    
    footer = f"\n📁 Discussion: `{discuss_path}`\n"
    
    if has_force:
        footer += "\n**Please update the discussion files before continuing.**\n"
    else:
        footer += "\nWould you like me to help update these files?\n"
    
    return header + items_text + footer


def scan_discussion_files(discuss_path: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Scan discussion directory for decisions and notes files.
    
    Args:
        discuss_path: Path to discussion directory
        
    Returns:
        Dictionary with 'decisions' and 'notes' lists
    """
    discuss_root = Path(discuss_path)
    result = {"decisions": [], "notes": []}
    
    # Scan decisions directory
    decisions_dir = discuss_root / "decisions"
    if decisions_dir.exists():
        for f in decisions_dir.glob("*.md"):
            result["decisions"].append({
                "path": f"decisions/{f.name}",
                "name": f.name,
                "last_modified": datetime.fromtimestamp(
                    f.stat().st_mtime, tz=timezone.utc
                ).isoformat(),
            })
    
    # Scan notes directory
    notes_dir = discuss_root / "notes"
    if notes_dir.exists():
        for f in notes_dir.glob("*.md"):
            result["notes"].append({
                "path": f"notes/{f.name}",
                "name": f.name,
                "last_modified": datetime.fromtimestamp(
                    f.stat().st_mtime, tz=timezone.utc
                ).isoformat(),
            })
    
    return result
