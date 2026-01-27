"""
Tests for hooks/common/meta_parser.py
"""

import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hooks"))

from common.meta_parser import (
    load_meta,
    save_meta,
    create_initial_meta,
    ensure_meta_structure,
    get_current_round,
    check_stale_status,
    format_stale_reminder,
    scan_discussion_files,
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
        meta = {"current_round": 5, "test_key": "test_value"}
        
        save_meta(str(tmp_path), meta)
        
        loaded = load_meta(str(tmp_path))
        assert loaded == meta
    
    def test_save_meta_creates_file(self, tmp_path):
        """Test that save_meta creates meta.yaml file."""
        meta = {"current_round": 1}
        
        save_meta(str(tmp_path), meta)
        
        assert (tmp_path / "meta.yaml").exists()


class TestCreateInitialMeta:
    """Tests for create_initial_meta function."""
    
    def test_has_required_fields(self):
        """Test initial meta has all required fields."""
        meta = create_initial_meta()
        
        assert "created" in meta
        assert "current_round" in meta
        assert "config" in meta
        assert "decisions" in meta
        assert "notes" in meta
    
    def test_current_round_starts_at_zero(self):
        """Test current_round starts at 0."""
        meta = create_initial_meta()
        assert meta["current_round"] == 0
    
    def test_config_has_defaults(self):
        """Test config has default threshold."""
        meta = create_initial_meta()
        
        assert meta["config"]["stale_threshold"] == 3
    
    def test_decisions_and_notes_empty(self):
        """Test decisions and notes start empty."""
        meta = create_initial_meta()
        
        assert meta["decisions"] == []
        assert meta["notes"] == []
    
    def test_topic_can_be_set(self):
        """Test topic can be set on creation."""
        meta = create_initial_meta(topic="test-topic")
        
        assert meta["topic"] == "test-topic"
    
    def test_no_file_status_field(self):
        """Test new schema doesn't include old file_status field."""
        meta = create_initial_meta()
        
        assert "file_status" not in meta


class TestEnsureMetaStructure:
    """Tests for ensure_meta_structure function."""
    
    def test_adds_missing_fields(self):
        """Test adds all missing fields."""
        meta = {}
        
        result = ensure_meta_structure(meta)
        
        assert "current_round" in result
        assert "config" in result
        assert "decisions" in result
        assert "notes" in result
    
    def test_preserves_existing_values(self):
        """Test preserves existing values."""
        meta = {
            "current_round": 10,
            "custom_field": "custom_value"
        }
        
        result = ensure_meta_structure(meta)
        
        assert result["current_round"] == 10
        assert result["custom_field"] == "custom_value"
    
    def test_adds_missing_config(self):
        """Test adds missing config with defaults."""
        meta = {"current_round": 5}
        
        result = ensure_meta_structure(meta)
        
        assert "config" in result
        assert result["config"]["stale_threshold"] == 3
    
    def test_adds_empty_arrays(self):
        """Test adds empty decisions and notes arrays."""
        meta = {}
        
        result = ensure_meta_structure(meta)
        
        assert result["decisions"] == []
        assert result["notes"] == []


class TestGetCurrentRound:
    """Tests for get_current_round function."""
    
    def test_returns_current_round(self):
        """Test returns current_round value."""
        meta = {"current_round": 7}
        
        result = get_current_round(meta)
        
        assert result == 7
    
    def test_returns_zero_if_missing(self):
        """Test returns 0 if current_round missing."""
        meta = {}
        
        result = get_current_round(meta)
        
        assert result == 0


class TestCheckStaleStatus:
    """Tests for check_stale_status function."""
    
    def test_no_stale_items_empty_arrays(self):
        """Test no stale items when arrays are empty."""
        meta = create_initial_meta()
        meta["current_round"] = 5
        
        result = check_stale_status(meta)
        
        assert result == []
    
    def test_no_stale_items_recently_updated(self):
        """Test no stale items when recently updated."""
        meta = create_initial_meta()
        meta["current_round"] = 5
        meta["decisions"] = [
            {"name": "D01.md", "last_updated_round": 4}
        ]
        
        result = check_stale_status(meta)
        
        assert result == []
    
    def test_stale_decision_detected(self):
        """Test stale decision is detected."""
        meta = create_initial_meta()
        meta["current_round"] = 10
        meta["decisions"] = [
            {"name": "D01.md", "last_updated_round": 5}  # 10-5=5 >= 3
        ]
        
        result = check_stale_status(meta)
        
        assert len(result) == 1
        assert result[0][0] == "decisions"
        assert result[0][1] == 5  # stale rounds
        assert result[0][2] is False  # not force (5 < 6)
    
    def test_force_threshold(self):
        """Test force threshold detection (2x stale_threshold)."""
        meta = create_initial_meta()
        meta["current_round"] = 10
        meta["decisions"] = [
            {"name": "D01.md", "last_updated_round": 3}  # 10-3=7 >= 6 (force)
        ]
        
        result = check_stale_status(meta)
        
        assert len(result) == 1
        assert result[0][2] is True  # is force
    
    def test_multiple_categories_stale(self):
        """Test both decisions and notes can be stale."""
        meta = create_initial_meta()
        meta["current_round"] = 10
        meta["decisions"] = [
            {"name": "D01.md", "last_updated_round": 2}
        ]
        meta["notes"] = [
            {"name": "note.md", "last_updated_round": 1}
        ]
        
        result = check_stale_status(meta)
        
        assert len(result) == 2
        file_types = [r[0] for r in result]
        assert "decisions" in file_types
        assert "notes" in file_types


class TestFormatStaleReminder:
    """Tests for format_stale_reminder function."""
    
    def test_empty_stale_items(self):
        """Test empty output for no stale items."""
        result = format_stale_reminder([], "/test/path")
        assert result == ""
    
    def test_suggest_message(self):
        """Test suggestion message format."""
        stale_items = [("decisions", 3, False)]
        
        result = format_stale_reminder(stale_items, "/test/discuss")
        
        assert "Suggestion" in result
        assert "decisions" in result
        assert "3 rounds" in result
    
    def test_force_message(self):
        """Test force message format."""
        stale_items = [("decisions", 10, True)]
        
        result = format_stale_reminder(stale_items, "/test/discuss")
        
        assert "Required" in result
        assert "REQUIRED" in result
        assert "decisions" in result
    
    def test_includes_discuss_path(self):
        """Test reminder includes discuss path."""
        stale_items = [("notes", 5, False)]
        
        result = format_stale_reminder(stale_items, "/my/project/.discuss/topic")
        
        assert "/my/project/.discuss/topic" in result


class TestScanDiscussionFiles:
    """Tests for scan_discussion_files function."""
    
    def test_empty_directory(self, tmp_path):
        """Test scanning empty directory."""
        result = scan_discussion_files(str(tmp_path))
        
        assert result["decisions"] == []
        assert result["notes"] == []
    
    def test_scans_decisions(self, tmp_path):
        """Test scanning decisions directory."""
        decisions_dir = tmp_path / "decisions"
        decisions_dir.mkdir()
        (decisions_dir / "D01-test.md").write_text("# Decision 1")
        (decisions_dir / "D02-another.md").write_text("# Decision 2")
        
        result = scan_discussion_files(str(tmp_path))
        
        assert len(result["decisions"]) == 2
        names = [d["name"] for d in result["decisions"]]
        assert "D01-test.md" in names
        assert "D02-another.md" in names
    
    def test_scans_notes(self, tmp_path):
        """Test scanning notes directory."""
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()
        (notes_dir / "research.md").write_text("# Research")
        
        result = scan_discussion_files(str(tmp_path))
        
        assert len(result["notes"]) == 1
        assert result["notes"][0]["name"] == "research.md"
    
    def test_includes_path_and_last_modified(self, tmp_path):
        """Test scanned files include path and last_modified."""
        decisions_dir = tmp_path / "decisions"
        decisions_dir.mkdir()
        (decisions_dir / "D01.md").write_text("content")
        
        result = scan_discussion_files(str(tmp_path))
        
        decision = result["decisions"][0]
        assert decision["path"] == "decisions/D01.md"
        assert "last_modified" in decision
