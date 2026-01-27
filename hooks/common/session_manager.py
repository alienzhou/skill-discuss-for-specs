"""
Session Manager for Hook scripts.

Manages session files to track per-conversation state.
Session files are organized by platform and session ID.

Session File Location: .discuss/.sessions/{platform}/{session_id}.json

Session File Content:
{
    "session_id": "abc123",
    "started_at": "2026-01-28T01:30:00Z",
    "outline_updated": true,
    "outline_paths": [".discuss/2026-01-28/topic/outline.md"]
}

Lifecycle:
1. Created: When outline edit is first detected in a conversation
2. Updated: Records which outlines were updated
3. Deleted: When stop hook completes
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .logging_utils import get_base_dir, log_debug, log_error, log_info


def get_sessions_dir() -> Path:
    """
    Get the global sessions directory.
    
    Sessions are stored in the global Discuss for Specs directory,
    not in project directories. This ensures sessions persist across
    projects and are easy to clean up.
    
    Returns:
        Path to sessions directory: ~/.discuss-for-specs/sessions/
    """
    return get_base_dir() / "sessions"


def get_session_id(hook_input: Dict[str, Any], platform: str) -> Optional[str]:
    """
    Extract session ID from hook input.
    
    Different platforms provide session ID in different ways.
    
    Args:
        hook_input: Hook input dictionary
        platform: Platform name ('claude-code', 'cursor', etc.)
        
    Returns:
        Session ID string, or None if not available
    """
    if not hook_input:
        return None
    
    # Claude Code provides session_id directly
    if platform == "claude-code":
        session_id = hook_input.get("session_id")
        if session_id:
            return str(session_id)
    
    # Cursor may use conversation_id or session_id
    if platform == "cursor":
        session_id = hook_input.get("conversation_id") or hook_input.get("session_id")
        if session_id:
            return str(session_id)
    
    # Fallback: try common keys
    for key in ["session_id", "conversation_id", "chat_id", "id"]:
        value = hook_input.get(key)
        if value:
            return str(value)
    
    # Last resort: generate a timestamp-based session ID
    # This is less accurate but allows functionality to continue
    log_debug("No session_id found in input, using timestamp-based fallback")
    return f"fallback-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}"


def get_session_path(platform: str, session_id: str) -> Path:
    """
    Get the path to a session file.
    
    Args:
        platform: Platform name
        session_id: Session ID
        
    Returns:
        Path to session file
    """
    return get_sessions_dir() / platform / f"{session_id}.json"


def load_session(platform: str, session_id: str) -> Optional[Dict[str, Any]]:
    """
    Load a session file.
    
    Args:
        platform: Platform name
        session_id: Session ID
        
    Returns:
        Session data dictionary, or None if not found
    """
    session_path = get_session_path(platform, session_id)
    
    if not session_path.exists():
        return None
    
    try:
        with open(session_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log_error(f"Failed to load session file: {session_path}", e)
        return None


def save_session(platform: str, session_id: str, data: Dict[str, Any]) -> bool:
    """
    Save a session file.
    
    Args:
        platform: Platform name
        session_id: Session ID
        data: Session data dictionary
        
    Returns:
        True if successful, False otherwise
    """
    session_path = get_session_path(platform, session_id)
    
    try:
        # Ensure directory exists
        session_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(session_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        
        log_debug(f"Saved session: {session_path}")
        return True
    except Exception as e:
        log_error(f"Failed to save session file: {session_path}", e)
        return False


def delete_session(platform: str, session_id: str) -> bool:
    """
    Delete a session file.
    
    Args:
        platform: Platform name
        session_id: Session ID
        
    Returns:
        True if deleted or didn't exist, False on error
    """
    session_path = get_session_path(platform, session_id)
    
    if not session_path.exists():
        return True
    
    try:
        session_path.unlink()
        log_debug(f"Deleted session: {session_path}")
        return True
    except Exception as e:
        log_error(f"Failed to delete session file: {session_path}", e)
        return False


def create_session(platform: str, session_id: str) -> Dict[str, Any]:
    """
    Create a new session data structure.
    
    Args:
        platform: Platform name
        session_id: Session ID
        
    Returns:
        New session data dictionary
    """
    return {
        "session_id": session_id,
        "platform": platform,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "outline_updated": False,
        "outline_paths": [],
    }


def mark_outline_updated(
    platform: str, 
    session_id: str, 
    outline_path: str
) -> bool:
    """
    Mark an outline as updated in the session.
    
    Args:
        platform: Platform name
        session_id: Session ID
        outline_path: Path to the updated outline file
        
    Returns:
        True if this is the first outline update in the session, False otherwise
    """
    session = load_session(platform, session_id)
    
    if session is None:
        # Create new session
        session = create_session(platform, session_id)
    
    # Check if this is the first outline update
    is_first_update = not session.get("outline_updated", False)
    
    # Update session
    session["outline_updated"] = True
    
    # Add outline path if not already present
    outline_paths = session.get("outline_paths", [])
    if outline_path not in outline_paths:
        outline_paths.append(outline_path)
        session["outline_paths"] = outline_paths
    
    # Save session
    save_session(platform, session_id, session)
    
    if is_first_update:
        log_info(f"First outline update in session {session_id}")
    else:
        log_debug(f"Additional outline update in session {session_id}")
    
    return is_first_update


def get_updated_outline_paths(platform: str, session_id: str) -> List[str]:
    """
    Get list of outline paths updated in this session.
    
    Args:
        platform: Platform name
        session_id: Session ID
        
    Returns:
        List of outline paths
    """
    session = load_session(platform, session_id)
    
    if session is None:
        return []
    
    return session.get("outline_paths", [])


def is_in_discussion_mode(platform: str, session_id: str) -> bool:
    """
    Check if user is currently in discussion mode.
    
    Discussion mode is detected by whether the outline was updated
    in the current conversation.
    
    Args:
        platform: Platform name
        session_id: Session ID
        
    Returns:
        True if in discussion mode (outline was updated)
    """
    session = load_session(platform, session_id)
    
    if session is None:
        return False
    
    return session.get("outline_updated", False)


def cleanup_old_sessions(platform: str, max_age_hours: int = 24) -> int:
    """
    Clean up old session files.
    
    Args:
        platform: Platform name
        max_age_hours: Maximum age in hours before cleanup
        
    Returns:
        Number of sessions cleaned up
    """
    sessions_dir = get_sessions_dir() / platform
    
    if not sessions_dir.exists():
        return 0
    
    cleaned = 0
    now = datetime.now(timezone.utc)
    
    for session_file in sessions_dir.glob("*.json"):
        try:
            with open(session_file, encoding="utf-8") as f:
                session = json.load(f)
            
            started_at = session.get("started_at")
            if started_at:
                started = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
                age_hours = (now - started).total_seconds() / 3600
                
                if age_hours > max_age_hours:
                    session_file.unlink()
                    cleaned += 1
                    log_debug(f"Cleaned up old session: {session_file}")
        except Exception as e:
            log_debug(f"Failed to check/clean session: {session_file}: {e}")
    
    return cleaned
    
    return cleaned
