"""
Tests for hooks/common/meta_parser.py
"""

import pytest
import tempfile
import os
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hooks"))

from common.meta_parser import (
    load_meta,
    save_meta,
    create_initial_meta,
    ensure_meta_structure,
    get_current_run,
    set_pending_update,
    get_pending_updates,
    clear_pending_and_update_run,
    check_stale_status,
    format_stale_reminder,
)


class TestLoadSaveMeta:
    """Tests for load_meta and save_meta functions."""
    
    def test_load_meta_nonexistent(self, tmp_path):
        """Test loading from non-existent directory."""
        result = load_meta(str(tmp_path / "nonexistent"))
        assert result is None
    
    def test_load_meta_no_file(self, tmp_path):
        """Test loading from directory without meta.yaml."""
        result = load_meta(str(tmp_path))
        assert result is None
    
    def test_save_and_load_meta(self, tmp_path):
        """Test saving and loading meta.yaml."""
        meta = {"current_run": 5, "test_key": "test_value"}
        
        save_meta(str(tmp_path), meta)
        
        loaded = load_meta(str(tmp_path))
        assert loaded == meta
    
    def test_save_meta_creates_file(self, tmp_path):
        """Test that save_meta creates meta.yaml file."""
        meta = {"current_run": 1}
        
        save_meta(str(tmp_path), meta)
        
        assert (tmp_path / "meta.yaml").exists()


class TestCreateInitialMeta:
    """Tests for create_initial_meta function."""
    
    def test_has_required_fields(self):
        """Test initial meta has all required fields."""
        meta = create_initial_meta()
        
        assert "created_at" in meta
        assert "current_run" in meta
        assert "config" in meta
        assert "file_status" in meta
    
    def test_current_run_starts_at_zero(self):
        """Test current_run starts at 0."""
        meta = create_initial_meta()
        assert meta["current_run"] == 0
    
    def test_config_has_defaults(self):
        """Test config has default thresholds."""
        meta = create_initial_meta()
        
        assert meta["config"]["suggest_update_runs"] == 3
        assert meta["config"]["force_update_runs"] == 10
    
    def test_file_status_has_all_types(self):
        """Test file_status includes all file types."""
        meta = create_initial_meta()
        
        assert "outline" in meta["file_status"]
        assert "decisions" in meta["file_status"]
        assert "notes" in meta["file_status"]
    
    def test_file_status_initial_values(self):
        """Test file_status initial values are correct."""
        meta = create_initial_meta()
        
        for file_type in ["outline", "decisions", "notes"]:
            assert meta["file_status"][file_type]["last_modified_run"] == 0
            assert meta["file_status"][file_type]["pending_update"] is False


class TestEnsureMetaStructure:
    """Tests for ensure_meta_structure function."""
    
    def test_adds_missing_fields(self):
        """Test adds all missing fields."""
        meta = {}
        
        result = ensure_meta_structure(meta)
        
        assert "current_run" in result
        assert "config" in result
        assert "file_status" in result
    
    def test_preserves_existing_values(self):
        """Test preserves existing values."""
        meta = {
            "current_run": 10,
            "custom_field": "custom_value"
        }
        
        result = ensure_meta_structure(meta)
        
        assert result["current_run"] == 10
        assert result["custom_field"] == "custom_value"
    
    def test_adds_missing_file_types(self):
        """Test adds missing file types to file_status."""
        meta = {
            "file_status": {
                "outline": {"last_modified_run": 5, "pending_update": False}
            }
        }
        
        result = ensure_meta_structure(meta)
        
        assert "decisions" in result["file_status"]
        assert "notes" in result["file_status"]
        # Original outline is preserved
        assert result["file_status"]["outline"]["last_modified_run"] == 5


class TestPendingUpdates:
    """Tests for pending update related functions."""
    
    def test_set_pending_update(self):
        """Test setting pending_update flag."""
        meta = create_initial_meta()
        
        result = set_pending_update(meta, "outline")
        
        assert result["file_status"]["outline"]["pending_update"] is True
        assert result["file_status"]["decisions"]["pending_update"] is False
    
    def test_get_pending_updates_empty(self):
        """Test getting pending updates when none are set."""
        meta = create_initial_meta()
        
        result = get_pending_updates(meta)
        
        assert result == []
    
    def test_get_pending_updates_single(self):
        """Test getting single pending update."""
        meta = create_initial_meta()
        meta = set_pending_update(meta, "decisions")
        
        result = get_pending_updates(meta)
        
        assert result == ["decisions"]
    
    def test_get_pending_updates_multiple(self):
        """Test getting multiple pending updates."""
        meta = create_initial_meta()
        meta = set_pending_update(meta, "outline")
        meta = set_pending_update(meta, "decisions")
        
        result = get_pending_updates(meta)
        
        assert set(result) == {"outline", "decisions"}


class TestClearPendingAndUpdateRun:
    """Tests for clear_pending_and_update_run function."""
    
    def test_increments_current_run(self):
        """Test that current_run is incremented."""
        meta = create_initial_meta()
        meta["current_run"] = 5
        
        result = clear_pending_and_update_run(meta)
        
        assert result["current_run"] == 6
    
    def test_updates_last_modified_run(self):
        """Test that last_modified_run is updated for pending items."""
        meta = create_initial_meta()
        meta["current_run"] = 5
        meta = set_pending_update(meta, "outline")
        
        result = clear_pending_and_update_run(meta)
        
        assert result["file_status"]["outline"]["last_modified_run"] == 5
    
    def test_clears_pending_update(self):
        """Test that pending_update flags are cleared."""
        meta = create_initial_meta()
        meta = set_pending_update(meta, "outline")
        meta = set_pending_update(meta, "decisions")
        
        result = clear_pending_and_update_run(meta)
        
        assert result["file_status"]["outline"]["pending_update"] is False
        assert result["file_status"]["decisions"]["pending_update"] is False


class TestCheckStaleStatus:
    """Tests for check_stale_status function."""
    
    def test_no_stale_items(self):
        """Test no stale items when recently updated."""
        meta = create_initial_meta()
        meta["current_run"] = 2
        meta["file_status"]["outline"]["last_modified_run"] = 1
        meta["file_status"]["decisions"]["last_modified_run"] = 1
        
        result = check_stale_status(meta)
        
        assert result == []
    
    def test_suggest_threshold(self):
        """Test suggest threshold detection."""
        meta = create_initial_meta()
        meta["current_run"] = 5
        meta["file_status"]["outline"]["last_modified_run"] = 2
        meta["file_status"]["decisions"]["last_modified_run"] = 4
        
        result = check_stale_status(meta)
        
        # outline is stale (5-2=3 >= suggest_update_runs=3)
        assert len(result) == 1
        assert result[0][0] == "outline"
        assert result[0][1] == 3
        assert result[0][2] is False  # not force
    
    def test_force_threshold(self):
        """Test force threshold detection."""
        meta = create_initial_meta()
        meta["current_run"] = 15
        meta["file_status"]["outline"]["last_modified_run"] = 5
        meta["file_status"]["decisions"]["last_modified_run"] = 14
        
        result = check_stale_status(meta)
        
        # outline is force stale (15-5=10 >= force_update_runs=10)
        assert len(result) == 1
        assert result[0][0] == "outline"
        assert result[0][1] == 10
        assert result[0][2] is True  # is force


class TestFormatStaleReminder:
    """Tests for format_stale_reminder function."""
    
    def test_empty_stale_items(self):
        """Test empty output for no stale items."""
        result = format_stale_reminder([], "/test/path")
        assert result == ""
    
    def test_suggest_message(self):
        """Test suggestion message format."""
        stale_items = [("outline", 3, False)]
        
        result = format_stale_reminder(stale_items, "/test/discuss")
        
        assert "Suggestion" in result
        assert "outline" in result
        assert "3 runs" in result
    
    def test_force_message(self):
        """Test force message format."""
        stale_items = [("outline", 10, True)]
        
        result = format_stale_reminder(stale_items, "/test/discuss")
        
        assert "Required" in result
        assert "REQUIRED" in result
        assert "outline" in result
