"""
Tests for hooks/post-response/check_stale.py
"""

import pytest
import yaml
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hooks"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hooks" / "post-response"))

from check_stale import (
    load_config,
    check_stale_decisions,
    format_reminder,
)


class TestLoadConfig:
    """Tests for load_config function."""
    
    def test_default_config(self):
        """Test default configuration when no config file."""
        result = load_config(None)
        
        assert result['stale_detection']['enabled'] is True
        assert result['stale_detection']['max_stale_rounds'] == 3
    
    def test_load_from_file(self, tmp_path):
        """Test loading config from file."""
        config = {
            'stale_detection': {
                'enabled': True,
                'max_stale_rounds': 5
            }
        }
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(config))
        
        result = load_config(str(config_path))
        
        assert result['stale_detection']['max_stale_rounds'] == 5
    
    def test_nonexistent_config_returns_default(self):
        """Test that nonexistent config returns default."""
        result = load_config("/nonexistent/path/config.yaml")
        
        assert result['stale_detection']['enabled'] is True
        assert result['stale_detection']['max_stale_rounds'] == 3


class TestCheckStaleDecisions:
    """Tests for check_stale_decisions function."""
    
    def test_no_meta_file(self, tmp_path):
        """Test with no meta.yaml file."""
        config = {'stale_detection': {'enabled': True, 'max_stale_rounds': 3}}
        
        result = check_stale_decisions(str(tmp_path), config)
        
        assert result == []
    
    def test_no_stale_decisions(self, tmp_path):
        """Test with no stale decisions."""
        meta = {
            'current_round': 5,
            'decisions': [
                {'id': 'D1', 'title': 'Decision 1', 'doc_path': '/path/to/doc.md', 'confirmed_at': 3}
            ]
        }
        (tmp_path / "meta.yaml").write_text(yaml.dump(meta))
        
        config = {'stale_detection': {'enabled': True, 'max_stale_rounds': 3}}
        result = check_stale_decisions(str(tmp_path), config)
        
        assert result == []
    
    def test_stale_decision_detected(self, tmp_path):
        """Test detecting stale decision."""
        meta = {
            'current_round': 10,
            'decisions': [
                {'id': 'D1', 'title': 'Stale Decision', 'doc_path': None, 'confirmed_at': 5}
            ]
        }
        (tmp_path / "meta.yaml").write_text(yaml.dump(meta))
        
        config = {'stale_detection': {'enabled': True, 'max_stale_rounds': 3}}
        result = check_stale_decisions(str(tmp_path), config)
        
        assert len(result) == 1
        assert result[0]['id'] == 'D1'
        assert result[0]['stale_rounds'] == 5
    
    def test_not_stale_if_within_threshold(self, tmp_path):
        """Test decision not stale if within threshold."""
        meta = {
            'current_round': 5,
            'decisions': [
                {'id': 'D1', 'title': 'Recent Decision', 'doc_path': None, 'confirmed_at': 4}
            ]
        }
        (tmp_path / "meta.yaml").write_text(yaml.dump(meta))
        
        config = {'stale_detection': {'enabled': True, 'max_stale_rounds': 3}}
        result = check_stale_decisions(str(tmp_path), config)
        
        assert result == []
    
    def test_multiple_stale_decisions(self, tmp_path):
        """Test detecting multiple stale decisions."""
        meta = {
            'current_round': 15,
            'decisions': [
                {'id': 'D1', 'title': 'Stale 1', 'doc_path': None, 'confirmed_at': 5},
                {'id': 'D2', 'title': 'Stale 2', 'doc_path': None, 'confirmed_at': 7},
                {'id': 'D3', 'title': 'Not Stale', 'doc_path': '/path.md', 'confirmed_at': 3},
            ]
        }
        (tmp_path / "meta.yaml").write_text(yaml.dump(meta))
        
        config = {'stale_detection': {'enabled': True, 'max_stale_rounds': 3}}
        result = check_stale_decisions(str(tmp_path), config)
        
        assert len(result) == 2
        ids = [d['id'] for d in result]
        assert 'D1' in ids
        assert 'D2' in ids


class TestFormatReminder:
    """Tests for format_reminder function."""
    
    def test_no_stale_returns_none(self):
        """Test empty list returns None."""
        result = format_reminder([], 5)
        
        assert result is None
    
    def test_formats_single_decision(self):
        """Test formatting single stale decision."""
        stale = [{'id': 'D1', 'title': 'Test Decision', 'confirmed_at': 3, 'stale_rounds': 5}]
        
        result = format_reminder(stale, 8)
        
        assert "⚠️ Precipitation Reminder" in result
        assert "D1: Test Decision" in result
        assert "confirmed at #R3" in result
        assert "now #R8" in result
        assert "5 rounds ago" in result
    
    def test_formats_multiple_decisions(self):
        """Test formatting multiple stale decisions."""
        stale = [
            {'id': 'D1', 'title': 'Decision One', 'confirmed_at': 2, 'stale_rounds': 8},
            {'id': 'D2', 'title': 'Decision Two', 'confirmed_at': 5, 'stale_rounds': 5}
        ]
        
        result = format_reminder(stale, 10)
        
        assert "D1: Decision One" in result
        assert "D2: Decision Two" in result
    
    def test_includes_recommendations(self):
        """Test reminder includes recommendations."""
        stale = [{'id': 'D1', 'title': 'Test', 'confirmed_at': 1, 'stale_rounds': 5}]
        
        result = format_reminder(stale, 6)
        
        assert "Recommendation" in result
        assert "document" in result.lower()
