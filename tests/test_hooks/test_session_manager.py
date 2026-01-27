"""
Tests for hooks/common/session_manager.py
"""

import pytest
import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hooks"))

from common.session_manager import (
    get_session_id,
    get_session_path,
    load_session,
    save_session,
    delete_session,
    create_session,
    mark_outline_updated,
    get_updated_outline_paths,
    is_in_discussion_mode,
    cleanup_old_sessions,
)


class TestGetSessionId:
    """Tests for get_session_id function."""
    
    def test_claude_code_session_id(self):
        """Test extracting session_id from Claude Code input."""
        hook_input = {"session_id": "abc123"}
        
        result = get_session_id(hook_input, "claude-code")
        
        assert result == "abc123"
    
    def test_cursor_conversation_id(self):
        """Test extracting conversation_id from Cursor input."""
        hook_input = {"conversation_id": "xyz789"}
        
        result = get_session_id(hook_input, "cursor")
        
        assert result == "xyz789"
    
    def test_cursor_session_id_fallback(self):
        """Test Cursor falling back to session_id."""
        hook_input = {"session_id": "session456"}
        
        result = get_session_id(hook_input, "cursor")
        
        assert result == "session456"
    
    def test_generic_fallback_keys(self):
        """Test fallback to common keys."""
        hook_input = {"chat_id": "chat123"}
        
        result = get_session_id(hook_input, "unknown")
        
        assert result == "chat123"
    
    def test_timestamp_fallback(self):
        """Test timestamp-based fallback when no ID found for unknown platform."""
        hook_input = {"some_other_field": "value"}  # Non-empty but no session keys
        
        result = get_session_id(hook_input, "unknown-platform")
        
        assert result is not None
        assert result.startswith("fallback-")
    
    def test_none_input(self):
        """Test handling None input."""
        result = get_session_id(None, "claude-code")
        
        assert result is None


class TestSessionPath:
    """Tests for get_session_path function."""
    
    def test_path_structure(self, monkeypatch, tmp_path):
        """Test session path has correct structure."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        result = get_session_path("claude-code", "session123")
        
        expected = tmp_path / ".discuss-for-specs" / "sessions" / "claude-code" / "session123.json"
        assert result == expected
    
    def test_different_platforms(self, monkeypatch, tmp_path):
        """Test different platforms have different paths."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        claude_path = get_session_path("claude-code", "s1")
        cursor_path = get_session_path("cursor", "s1")
        
        assert "claude-code" in str(claude_path)
        assert "cursor" in str(cursor_path)
        assert claude_path != cursor_path


class TestCreateSession:
    """Tests for create_session function."""
    
    def test_has_required_fields(self):
        """Test created session has all required fields."""
        session = create_session("claude-code", "test123")
        
        assert session["session_id"] == "test123"
        assert session["platform"] == "claude-code"
        assert "started_at" in session
        assert session["outline_updated"] is False
        assert session["outline_paths"] == []
    
    def test_started_at_is_iso_format(self):
        """Test started_at is in ISO format."""
        session = create_session("cursor", "abc")
        
        # Should be parseable as ISO timestamp
        from datetime import datetime
        datetime.fromisoformat(session["started_at"].replace("Z", "+00:00"))


class TestSaveLoadSession:
    """Tests for save_session and load_session functions."""
    
    def test_save_creates_file(self, monkeypatch, tmp_path):
        """Test save creates session file."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        session = create_session("claude-code", "s1")
        result = save_session("claude-code", "s1", session)
        
        assert result is True
        session_path = get_session_path("claude-code", "s1")
        assert session_path.exists()
    
    def test_load_nonexistent(self, monkeypatch, tmp_path):
        """Test loading non-existent session returns None."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        result = load_session("claude-code", "nonexistent")
        
        assert result is None
    
    def test_save_and_load(self, monkeypatch, tmp_path):
        """Test save and load roundtrip."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        original = create_session("claude-code", "test")
        original["outline_updated"] = True
        original["outline_paths"] = ["/path/to/outline.md"]
        
        save_session("claude-code", "test", original)
        loaded = load_session("claude-code", "test")
        
        assert loaded["session_id"] == "test"
        assert loaded["outline_updated"] is True
        assert loaded["outline_paths"] == ["/path/to/outline.md"]


class TestDeleteSession:
    """Tests for delete_session function."""
    
    def test_delete_existing(self, monkeypatch, tmp_path):
        """Test deleting existing session."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        # Create session
        session = create_session("claude-code", "todelete")
        save_session("claude-code", "todelete", session)
        
        # Verify exists
        assert get_session_path("claude-code", "todelete").exists()
        
        # Delete
        result = delete_session("claude-code", "todelete")
        
        assert result is True
        assert not get_session_path("claude-code", "todelete").exists()
    
    def test_delete_nonexistent(self, monkeypatch, tmp_path):
        """Test deleting non-existent session returns True."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        result = delete_session("claude-code", "doesnotexist")
        
        assert result is True


class TestMarkOutlineUpdated:
    """Tests for mark_outline_updated function."""
    
    def test_first_update_returns_true(self, monkeypatch, tmp_path):
        """Test first outline update returns True."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        result = mark_outline_updated("claude-code", "s1", "/path/outline.md")
        
        assert result is True
    
    def test_second_update_returns_false(self, monkeypatch, tmp_path):
        """Test subsequent updates return False."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        # First update
        mark_outline_updated("claude-code", "s2", "/path/outline.md")
        
        # Second update
        result = mark_outline_updated("claude-code", "s2", "/path/outline.md")
        
        assert result is False
    
    def test_adds_outline_path(self, monkeypatch, tmp_path):
        """Test outline path is added to session."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        mark_outline_updated("claude-code", "s3", "/path/to/outline.md")
        
        session = load_session("claude-code", "s3")
        assert "/path/to/outline.md" in session["outline_paths"]
    
    def test_multiple_outlines(self, monkeypatch, tmp_path):
        """Test multiple different outlines can be tracked."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        mark_outline_updated("claude-code", "s4", "/path1/outline.md")
        mark_outline_updated("claude-code", "s4", "/path2/outline.md")
        
        session = load_session("claude-code", "s4")
        assert len(session["outline_paths"]) == 2


class TestGetUpdatedOutlinePaths:
    """Tests for get_updated_outline_paths function."""
    
    def test_returns_empty_for_new_session(self, monkeypatch, tmp_path):
        """Test returns empty list for non-existent session."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        result = get_updated_outline_paths("claude-code", "new")
        
        assert result == []
    
    def test_returns_updated_paths(self, monkeypatch, tmp_path):
        """Test returns list of updated outline paths."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        mark_outline_updated("claude-code", "s5", "/a/outline.md")
        mark_outline_updated("claude-code", "s5", "/b/outline.md")
        
        result = get_updated_outline_paths("claude-code", "s5")
        
        assert len(result) == 2
        assert "/a/outline.md" in result
        assert "/b/outline.md" in result


class TestIsInDiscussionMode:
    """Tests for is_in_discussion_mode function."""
    
    def test_false_for_new_session(self, monkeypatch, tmp_path):
        """Test returns False for non-existent session."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        result = is_in_discussion_mode("claude-code", "nonexistent")
        
        assert result is False
    
    def test_false_for_no_outline_updates(self, monkeypatch, tmp_path):
        """Test returns False when outline not updated."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        session = create_session("claude-code", "s6")
        save_session("claude-code", "s6", session)
        
        result = is_in_discussion_mode("claude-code", "s6")
        
        assert result is False
    
    def test_true_after_outline_update(self, monkeypatch, tmp_path):
        """Test returns True after outline is updated."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        mark_outline_updated("claude-code", "s7", "/path/outline.md")
        
        result = is_in_discussion_mode("claude-code", "s7")
        
        assert result is True


class TestCleanupOldSessions:
    """Tests for cleanup_old_sessions function."""
    
    def test_cleanup_empty_directory(self, monkeypatch, tmp_path):
        """Test cleanup on empty/non-existent directory."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        result = cleanup_old_sessions("claude-code", max_age_hours=1)
        
        assert result == 0
    
    def test_cleanup_preserves_recent(self, monkeypatch, tmp_path):
        """Test cleanup preserves recent sessions."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        # Create a fresh session
        session = create_session("claude-code", "recent")
        save_session("claude-code", "recent", session)
        
        result = cleanup_old_sessions("claude-code", max_age_hours=24)
        
        # Should not clean up recent session
        assert result == 0
        assert load_session("claude-code", "recent") is not None
