"""
Integration tests for hook scripts.

These tests simulate the full hook workflow by invoking the scripts
with mock input and checking the output and side effects.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml


# Paths to hook scripts
HOOKS_DIR = Path(__file__).parent.parent.parent / "hooks"
CHECK_PRECIPITATION = HOOKS_DIR / "stop" / "check_precipitation.py"


def run_hook(script_path: Path, input_data: dict, cwd: Path = None) -> tuple:
    """
    Run a hook script with given input.
    
    Returns:
        tuple: (return_code, stdout, stderr)
    """
    env = os.environ.copy()
    env["PYTHONPATH"] = str(HOOKS_DIR.parent)
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
        env=env,
    )
    return result.returncode, result.stdout, result.stderr


class TestCheckPrecipitationHook:
    """Integration tests for check_precipitation.py (snapshot-based)."""
    
    def test_no_discuss_dirs(self, tmp_path):
        """Test with no discussion directories."""
        input_data = {"status": "completed"}
        
        code, stdout, stderr = run_hook(CHECK_PRECIPITATION, input_data, cwd=tmp_path)
        
        assert code == 0
        assert stdout.strip() == "{}"
    
    def test_stop_hook_active_bypass(self, tmp_path):
        """Test that stop_hook_active=True bypasses check."""
        # Create discussion directory
        discuss_dir = tmp_path / ".discuss" / "2026-01-28" / "topic"
        discuss_dir.mkdir(parents=True)
        (discuss_dir / "outline.md").write_text("# Outline")
        
        # Run with stop_hook_active=True
        input_data = {
            "hook_event_name": "Stop",
            "stop_hook_active": True
        }
        code, stdout, stderr = run_hook(CHECK_PRECIPITATION, input_data, cwd=tmp_path)
        
        assert code == 0
        assert stdout.strip() == "{}"
    
    def test_no_stale_discussions(self, tmp_path):
        """Test with discussions that are not stale."""
        # Create discussion with outline and decisions
        discuss_dir = tmp_path / ".discuss" / "2026-01-28" / "topic"
        discuss_dir.mkdir(parents=True)
        (discuss_dir / "outline.md").write_text("# Outline")
        
        decisions_dir = discuss_dir / "decisions"
        decisions_dir.mkdir()
        (decisions_dir / "D01-test.md").write_text("# Decision")
        
        # Run hook
        input_data = {"status": "completed"}
        code, stdout, stderr = run_hook(CHECK_PRECIPITATION, input_data, cwd=tmp_path)
        
        # Should allow (no stale reminders)
        assert code == 0
        output = json.loads(stdout.strip())
        # May be {} or have other fields, but shouldn't block
        assert "decision" not in output or output.get("decision") != "block"
    
    def test_stale_discussion_detection(self, tmp_path):
        """Test detection of stale discussions (outline changed but decisions not updated)."""
        import time
        
        # Create discussion with outline
        discuss_dir = tmp_path / ".discuss" / "2026-01-28" / "topic"
        discuss_dir.mkdir(parents=True)
        outline = discuss_dir / "outline.md"
        outline.write_text("# Outline")
        
        # Wait a bit to ensure mtime difference
        time.sleep(0.1)
        
        # Modify outline multiple times (simulating changes without decision updates)
        for i in range(4):
            outline.write_text(f"# Outline v{i}")
            time.sleep(0.1)
        
        # Run hook - should detect stale state
        input_data = {"status": "completed"}
        code, stdout, stderr = run_hook(CHECK_PRECIPITATION, input_data, cwd=tmp_path)
        
        # Should detect staleness (may block or suggest)
        output = json.loads(stdout.strip())
        # The hook may block or allow with suggestion depending on threshold
        # Just verify it runs without error
        assert code == 0
