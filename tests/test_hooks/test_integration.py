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
TRACK_FILE_EDIT = HOOKS_DIR / "file-edit" / "track_file_edit.py"
CHECK_PRECIPITATION = HOOKS_DIR / "stop" / "check_precipitation.py"


def run_hook(script_path: Path, input_data: dict, cwd: Path = None) -> tuple:
    """
    Run a hook script with given input.
    
    Returns:
        tuple: (return_code, stdout, stderr)
    """
    env = os.environ.copy()
    if cwd:
        # Override PWD to ensure hook uses the test directory
        env["PWD"] = str(cwd)
        env["WORKSPACE_ROOT"] = str(cwd)
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
        env=env,
    )
    return result.returncode, result.stdout, result.stderr


class TestTrackFileEditHook:
    """Integration tests for track_file_edit.py."""
    
    def test_non_discuss_file(self, tmp_path):
        """Test with file not in discussion directory."""
        random_file = tmp_path / "random.md"
        random_file.write_text("# Random")
        
        input_data = {"file_path": str(random_file)}
        
        code, stdout, stderr = run_hook(TRACK_FILE_EDIT, input_data)
        
        assert code == 0
        assert stdout.strip() == "{}"
    
    def test_outline_file_update(self, tmp_path):
        """Test tracking outline.md update."""
        # Create discussion structure
        discuss_dir = tmp_path / "discuss" / "topic"
        discuss_dir.mkdir(parents=True)
        
        # Create initial meta.yaml
        meta = {
            "current_run": 5,
            "config": {"suggest_update_runs": 3, "force_update_runs": 10},
            "file_status": {
                "outline": {"last_modified_run": 3, "pending_update": False},
                "decisions": {"last_modified_run": 2, "pending_update": False},
                "notes": {"last_modified_run": 0, "pending_update": False},
            }
        }
        (discuss_dir / "meta.yaml").write_text(yaml.dump(meta))
        
        # Create outline
        outline = discuss_dir / "outline.md"
        outline.write_text("# Outline")
        
        # Run hook
        input_data = {"file_path": str(outline)}
        code, stdout, stderr = run_hook(TRACK_FILE_EDIT, input_data)
        
        assert code == 0
        assert stdout.strip() == "{}"
        
        # Check meta.yaml was updated
        updated_meta = yaml.safe_load((discuss_dir / "meta.yaml").read_text())
        assert updated_meta["file_status"]["outline"]["pending_update"] is True
        assert updated_meta["file_status"]["decisions"]["pending_update"] is False
    
    def test_decision_file_update(self, tmp_path):
        """Test tracking decision file update."""
        # Create discussion structure
        discuss_dir = tmp_path / "discuss" / "topic"
        decisions_dir = discuss_dir / "decisions"
        decisions_dir.mkdir(parents=True)
        
        # Create initial meta.yaml
        meta = {
            "current_run": 5,
            "config": {"suggest_update_runs": 3, "force_update_runs": 10},
            "file_status": {
                "outline": {"last_modified_run": 4, "pending_update": False},
                "decisions": {"last_modified_run": 2, "pending_update": False},
                "notes": {"last_modified_run": 0, "pending_update": False},
            }
        }
        (discuss_dir / "meta.yaml").write_text(yaml.dump(meta))
        
        # Create decision file
        decision = decisions_dir / "01-test.md"
        decision.write_text("# Decision")
        
        # Run hook with Claude Code format
        input_data = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": str(decision),
                "old_string": "a",
                "new_string": "b"
            }
        }
        code, stdout, stderr = run_hook(TRACK_FILE_EDIT, input_data)
        
        assert code == 0
        
        # Check meta.yaml was updated
        updated_meta = yaml.safe_load((discuss_dir / "meta.yaml").read_text())
        assert updated_meta["file_status"]["decisions"]["pending_update"] is True


class TestCheckPrecipitationHook:
    """Integration tests for check_precipitation.py."""
    
    def test_no_discuss_dirs(self, tmp_path):
        """Test with no discussion directories."""
        input_data = {"status": "completed"}
        
        code, stdout, stderr = run_hook(CHECK_PRECIPITATION, input_data, cwd=tmp_path)
        
        assert code == 0
        assert stdout.strip() == "{}"
    
    def test_stop_hook_active_bypass(self, tmp_path):
        """Test that stop_hook_active=True bypasses check."""
        # Create discussion with stale content
        discuss_dir = tmp_path / "discuss" / "topic"
        discuss_dir.mkdir(parents=True)
        
        meta = {
            "current_run": 15,
            "config": {"suggest_update_runs": 3, "force_update_runs": 10},
            "file_status": {
                "outline": {"last_modified_run": 0, "pending_update": False},
                "decisions": {"last_modified_run": 0, "pending_update": False},
                "notes": {"last_modified_run": 0, "pending_update": False},
            }
        }
        (discuss_dir / "meta.yaml").write_text(yaml.dump(meta))
        
        # Run with stop_hook_active=True
        input_data = {
            "hook_event_name": "Stop",
            "stop_hook_active": True
        }
        code, stdout, stderr = run_hook(CHECK_PRECIPITATION, input_data, cwd=tmp_path)
        
        assert code == 0
        assert stdout.strip() == "{}"
    
    def test_clears_pending_and_increments_run(self, tmp_path):
        """Test that pending updates are cleared and run is incremented."""
        discuss_dir = tmp_path / "discuss" / "topic"
        discuss_dir.mkdir(parents=True)
        
        meta = {
            "current_run": 5,
            "config": {"suggest_update_runs": 3, "force_update_runs": 10},
            "file_status": {
                "outline": {"last_modified_run": 4, "pending_update": True},
                "decisions": {"last_modified_run": 4, "pending_update": False},
                "notes": {"last_modified_run": 0, "pending_update": False},
            }
        }
        (discuss_dir / "meta.yaml").write_text(yaml.dump(meta))
        
        input_data = {"status": "completed"}
        code, stdout, stderr = run_hook(CHECK_PRECIPITATION, input_data, cwd=tmp_path)
        
        assert code == 0
        
        # Check meta.yaml was updated
        updated_meta = yaml.safe_load((discuss_dir / "meta.yaml").read_text())
        assert updated_meta["current_run"] == 6
        assert updated_meta["file_status"]["outline"]["pending_update"] is False
        assert updated_meta["file_status"]["outline"]["last_modified_run"] == 5
