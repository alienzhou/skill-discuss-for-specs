#!/usr/bin/env python3
"""
Hook 2: Precipitation Check

This hook is triggered when AI conversation ends and checks if discussion
files need to be updated (precipitated).

Trigger:
- Claude Code: Stop hook
- Cursor: stop hook

Input (stdin JSON):
- Cursor: {"status": "completed", ...}
- Claude Code: {"hook_event_name": "Stop", "stop_hook_active": false, ...}

Output (stdout JSON):
- Allow: {}
- Block (Cursor): {"followup_message": "..."}
- Block (Claude Code): {"decision": "block", "reason": "..."}

Workflow:
1. Check if stop_hook_active is true (prevent infinite loop)
2. Scan for discussions with pending_update=true
3. Update last_modified_run and clear pending_update
4. Increment current_run
5. Check for stale files and remind if necessary
"""

import os
import sys
from pathlib import Path
from typing import List

# Add parent directory to path for common imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.logging_utils import (
    log_debug,
    log_error,
    log_hook_end,
    log_hook_start,
    log_info,
    log_meta_update,
    log_stale_detection,
    log_warning,
)
from common.meta_parser import (
    check_stale_status,
    clear_pending_and_update_run,
    format_stale_reminder,
    get_pending_updates,
    load_meta,
    save_meta,
)
from common.platform_utils import (
    Platform,
    allow_and_exit,
    block_and_exit,
    detect_platform,
    is_stop_hook_active,
    read_stdin_json,
)


HOOK_NAME = "check_precipitation"


def find_all_discuss_dirs(workspace_root: Path) -> List[Path]:
    """
    Find all discussion directories in the workspace.
    
    A discussion directory is identified by containing a meta.yaml file.
    
    Args:
        workspace_root: Root directory to search from
        
    Returns:
        List of paths to discussion directories
    """
    discuss_dirs = []
    
    # Common patterns for discussion directories
    search_patterns = [
        "discuss",
        "discussions",
        ".discuss",
    ]
    
    for pattern in search_patterns:
        discuss_root = workspace_root / pattern
        if discuss_root.exists():
            # Search recursively for meta.yaml files
            for meta_file in discuss_root.rglob("meta.yaml"):
                discuss_dirs.append(meta_file.parent)
    
    return discuss_dirs


def get_workspace_root() -> Path:
    """
    Get the workspace root directory.
    
    Uses environment variables or current working directory.
    
    Returns:
        Path to workspace root
    """
    # Try common environment variables
    for env_var in ["WORKSPACE_ROOT", "PROJECT_ROOT", "PWD"]:
        if env_var in os.environ:
            return Path(os.environ[env_var])
    
    # Fallback to current working directory
    return Path.cwd()


def main():
    """Main entry point for the precipitation check hook."""
    input_data = None
    platform = Platform.UNKNOWN
    
    try:
        # Read input from stdin
        input_data = read_stdin_json()
        log_hook_start(HOOK_NAME, input_data)
        
        # Detect platform
        platform = detect_platform(input_data) if input_data else Platform.UNKNOWN
        log_info(f"Detected platform: {platform.value}")
        
        # Check if this is a continuation after stop hook already triggered
        if input_data and is_stop_hook_active(input_data):
            log_debug("stop_hook_active is True, bypassing check")
            log_hook_end(HOOK_NAME, {}, success=True)
            allow_and_exit()
        
        # Find workspace root
        workspace_root = get_workspace_root()
        log_debug(f"Workspace root: {workspace_root}")
        
        # Find all discussion directories
        discuss_dirs = find_all_discuss_dirs(workspace_root)
        log_info(f"Found {len(discuss_dirs)} discussion directories")
        
        if not discuss_dirs:
            log_debug("No discussion directories found, allowing operation")
            log_hook_end(HOOK_NAME, {}, success=True)
            allow_and_exit()
        
        # Process each discussion directory
        modified_discussions = []
        stale_reminders = []
        
        for discuss_dir in discuss_dirs:
            log_debug(f"Processing discussion: {discuss_dir}")
            
            meta = load_meta(str(discuss_dir))
            
            if meta is None:
                log_debug(f"No meta.yaml found in {discuss_dir}, skipping")
                continue
            
            # Check if this discussion has pending updates
            pending = get_pending_updates(meta)
            
            if pending:
                log_info(f"Found pending updates in {discuss_dir}: {pending}")
                modified_discussions.append((discuss_dir, pending))
                
                # Clear pending updates and increment run
                old_run = meta.get("current_run", 0)
                meta = clear_pending_and_update_run(meta)
                save_meta(str(discuss_dir), meta)
                
                log_meta_update(str(discuss_dir), {
                    "current_run": f"{old_run} -> {meta['current_run']}",
                    "cleared_pending": pending
                })
            
            # Check for stale status
            stale_items = check_stale_status(meta)
            log_stale_detection(str(discuss_dir), stale_items)
            
            if stale_items:
                reminder = format_stale_reminder(stale_items, str(discuss_dir))
                stale_reminders.append(reminder)
        
        # Summary logging
        log_info(f"Modified discussions: {len(modified_discussions)}")
        log_info(f"Stale reminders: {len(stale_reminders)}")
        
        # If there are stale reminders, block with the reminder
        if stale_reminders:
            combined_reminder = "\n\n---\n\n".join(stale_reminders)
            log_warning(f"Blocking with {len(stale_reminders)} stale reminder(s)")
            log_hook_end(HOOK_NAME, {"action": "block"}, success=True)
            block_and_exit(combined_reminder, platform)
        
        # No issues, allow and exit
        log_hook_end(HOOK_NAME, {}, success=True)
        allow_and_exit()
        
    except Exception as e:
        log_error(f"Unexpected error in {HOOK_NAME}", e)
        log_hook_end(HOOK_NAME, {}, success=False)
        # Still allow operation to continue even on error
        allow_and_exit()


if __name__ == "__main__":
    main()
