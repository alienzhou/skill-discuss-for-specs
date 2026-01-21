#!/usr/bin/env python3
"""
Hook 1: File Edit Tracking

This hook is triggered after each file edit and tracks which discussion
files have been modified during the current AI conversation session.

Trigger:
- Claude Code: PostToolUse with matcher "Edit|Write|MultiEdit"
- Cursor: afterFileEdit

Input (stdin JSON):
- Cursor: {"file_path": "/path/to/file.md", ...}
- Claude Code: {"tool_input": {"file_path": "/path/to/file.md", ...}, ...}

Output (stdout JSON):
- Always outputs {} to allow the operation to continue

Side Effect:
- Updates meta.yaml with pending_update=true for the relevant file type
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for common imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.file_utils import find_discuss_root
from common.logging_utils import (
    log_debug,
    log_discuss_detection,
    log_error,
    log_file_operation,
    log_hook_end,
    log_hook_start,
    log_meta_update,
)
from common.meta_parser import (
    create_initial_meta,
    ensure_meta_structure,
    load_meta,
    save_meta,
    set_pending_update,
)
from common.platform_utils import (
    allow_and_exit,
    get_file_path_from_input,
    read_stdin_json,
)


HOOK_NAME = "track_file_edit"


def determine_file_type(file_path: Path, discuss_root: Path) -> Optional[str]:
    """
    Determine which file type category a file belongs to.
    
    Args:
        file_path: Absolute path to the edited file
        discuss_root: Path to the discussion root directory
        
    Returns:
        One of "outline", "decisions", "notes", or None if not a tracked type
    """
    try:
        relative_path = file_path.relative_to(discuss_root)
    except ValueError:
        return None
    
    parts = relative_path.parts
    
    if not parts:
        return None
    
    # Check for outline.md
    if relative_path.name == "outline.md":
        return "outline"
    
    # Check for decisions/ directory
    if parts[0] == "decisions":
        return "decisions"
    
    # Check for notes/ directory
    if parts[0] == "notes":
        return "notes"
    
    return None


def main():
    """Main entry point for the file edit tracking hook."""
    input_data = None
    
    try:
        # Read input from stdin
        input_data = read_stdin_json()
        log_hook_start(HOOK_NAME, input_data)
        
        if input_data is None:
            log_debug("No input data received, allowing operation")
            log_hook_end(HOOK_NAME, {}, success=True)
            allow_and_exit()
        
        # Extract file path
        file_path_str = get_file_path_from_input(input_data)
        
        if not file_path_str:
            log_debug("No file path found in input, allowing operation")
            log_hook_end(HOOK_NAME, {}, success=True)
            allow_and_exit()
        
        log_file_operation("EDIT", file_path_str, "File edit detected")
        
        file_path = Path(file_path_str).resolve()
        
        # Find discussion root directory
        discuss_root = find_discuss_root(str(file_path))
        
        if discuss_root is None:
            log_debug(f"Not a discussion file: {file_path}")
            log_hook_end(HOOK_NAME, {}, success=True)
            allow_and_exit()
        
        # Determine file type
        file_type = determine_file_type(file_path, discuss_root)
        
        if file_type is None:
            log_debug(f"Not a tracked file type: {file_path}")
            log_hook_end(HOOK_NAME, {}, success=True)
            allow_and_exit()
        
        log_discuss_detection(str(discuss_root), file_type)
        
        # Load or create meta.yaml
        meta = load_meta(str(discuss_root))
        
        if meta is None:
            log_debug("No meta.yaml found, creating initial meta")
            meta = create_initial_meta()
        else:
            meta = ensure_meta_structure(meta)
        
        # Set pending_update for this file type
        meta = set_pending_update(meta, file_type)
        
        # Save updated meta
        save_meta(str(discuss_root), meta)
        log_meta_update(str(discuss_root), {f"{file_type}.pending_update": True})
        
        log_hook_end(HOOK_NAME, {}, success=True)
        allow_and_exit()
        
    except Exception as e:
        log_error(f"Unexpected error in {HOOK_NAME}", e)
        log_hook_end(HOOK_NAME, {}, success=False)
        # Still allow operation to continue even on error
        allow_and_exit()


if __name__ == "__main__":
    main()
