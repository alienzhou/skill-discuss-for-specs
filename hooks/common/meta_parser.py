"""
Common utilities for meta.yaml parsing and manipulation.

New Schema (v2):
- created_at: ISO timestamp
- current_run: incremented by stop hook
- config: suggest_update_runs, force_update_runs
- file_status: outline/decisions/notes tracking
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


# Default configuration values
DEFAULT_SUGGEST_UPDATE_RUNS = 3
DEFAULT_FORCE_UPDATE_RUNS = 10


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


def create_initial_meta() -> Dict[str, Any]:
    """
    Create initial meta.yaml content with default values.
    
    Returns:
        Dictionary with initial meta structure
    """
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "current_run": 0,
        "config": {
            "suggest_update_runs": DEFAULT_SUGGEST_UPDATE_RUNS,
            "force_update_runs": DEFAULT_FORCE_UPDATE_RUNS,
        },
        "file_status": {
            "outline": {
                "last_modified_run": 0,
                "pending_update": False,
            },
            "decisions": {
                "last_modified_run": 0,
                "pending_update": False,
            },
            "notes": {
                "last_modified_run": 0,
                "pending_update": False,
            },
        },
    }


def ensure_meta_structure(meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure meta has all required fields, adding defaults if missing.
    
    Args:
        meta: Existing meta dictionary
        
    Returns:
        Meta dictionary with all required fields
    """
    if "current_run" not in meta:
        meta["current_run"] = 0
    
    if "config" not in meta:
        meta["config"] = {}
    
    config = meta["config"]
    if "suggest_update_runs" not in config:
        config["suggest_update_runs"] = DEFAULT_SUGGEST_UPDATE_RUNS
    if "force_update_runs" not in config:
        config["force_update_runs"] = DEFAULT_FORCE_UPDATE_RUNS
    
    if "file_status" not in meta:
        meta["file_status"] = {}
    
    file_status = meta["file_status"]
    for file_type in ["outline", "decisions", "notes"]:
        if file_type not in file_status:
            file_status[file_type] = {
                "last_modified_run": 0,
                "pending_update": False,
            }
        else:
            if "last_modified_run" not in file_status[file_type]:
                file_status[file_type]["last_modified_run"] = 0
            if "pending_update" not in file_status[file_type]:
                file_status[file_type]["pending_update"] = False
    
    return meta


def get_current_run(meta: Dict[str, Any]) -> int:
    """
    Get current run number from meta.
    
    Args:
        meta: Meta dictionary
        
    Returns:
        Current run number (default 0)
    """
    return meta.get("current_run", 0)


def set_pending_update(meta: Dict[str, Any], file_type: str) -> Dict[str, Any]:
    """
    Set pending_update flag for a file type.
    
    Args:
        meta: Meta dictionary
        file_type: One of "outline", "decisions", "notes"
        
    Returns:
        Updated meta dictionary
    """
    meta = ensure_meta_structure(meta)
    meta["file_status"][file_type]["pending_update"] = True
    return meta


def get_pending_updates(meta: Dict[str, Any]) -> List[str]:
    """
    Get list of file types with pending updates.
    
    Args:
        meta: Meta dictionary
        
    Returns:
        List of file types with pending_update=True
    """
    meta = ensure_meta_structure(meta)
    pending = []
    
    for file_type, status in meta.get("file_status", {}).items():
        if isinstance(status, dict) and status.get("pending_update", False):
            pending.append(file_type)
    
    return pending


def clear_pending_and_update_run(meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clear all pending_update flags and increment current_run.
    
    Also updates last_modified_run for file types that had pending updates.
    
    Args:
        meta: Meta dictionary
        
    Returns:
        Updated meta dictionary
    """
    meta = ensure_meta_structure(meta)
    current_run = meta["current_run"]
    
    # Update last_modified_run for pending updates, then clear flags
    for file_type in meta.get("file_status", {}):
        status = meta["file_status"][file_type]
        if isinstance(status, dict) and status.get("pending_update", False):
            status["last_modified_run"] = current_run
            status["pending_update"] = False
    
    # Increment run counter
    meta["current_run"] = current_run + 1
    
    return meta


def check_stale_status(meta: Dict[str, Any]) -> List[Tuple[str, int, bool]]:
    """
    Check for stale file status (not updated for a while).
    
    Args:
        meta: Meta dictionary
        
    Returns:
        List of tuples: (file_type, stale_runs, is_force_update)
    """
    meta = ensure_meta_structure(meta)
    
    current_run = meta["current_run"]
    config = meta["config"]
    suggest_runs = config.get("suggest_update_runs", DEFAULT_SUGGEST_UPDATE_RUNS)
    force_runs = config.get("force_update_runs", DEFAULT_FORCE_UPDATE_RUNS)
    
    stale_items = []
    
    # Only check outline and decisions, notes is optional
    for file_type in ["outline", "decisions"]:
        status = meta["file_status"].get(file_type, {})
        last_modified = status.get("last_modified_run", 0)
        stale_runs = current_run - last_modified
        
        if stale_runs >= suggest_runs:
            is_force = stale_runs >= force_runs
            stale_items.append((file_type, stale_runs, is_force))
    
    return stale_items


def format_stale_reminder(stale_items: List[Tuple[str, int, bool]], discuss_path: str) -> str:
    """
    Format a reminder message for stale items.
    
    Args:
        stale_items: List of (file_type, stale_runs, is_force) tuples
        discuss_path: Path to discussion directory for context
        
    Returns:
        Formatted reminder message
    """
    if not stale_items:
        return ""
    
    # Check if any item is force update
    has_force = any(item[2] for item in stale_items)
    
    if has_force:
        header = "## Precipitation Required\n\n"
        header += "The following discussion files have not been updated for too long:\n\n"
    else:
        header = "## Precipitation Suggestion\n\n"
        header += "The following discussion files may need updating:\n\n"
    
    items_text = ""
    for file_type, stale_runs, is_force in stale_items:
        status = "[REQUIRED]" if is_force else "[Suggested]"
        items_text += f"- {status} `{file_type}` - {stale_runs} runs since last update\n"
    
    footer = f"\nDiscussion: `{discuss_path}`\n"
    
    if has_force:
        footer += "\nPlease update the discussion files before continuing."
    else:
        footer += "\nWould you like me to help update these files?"
    
    return header + items_text + footer
