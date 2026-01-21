"""
Tests for hooks/post-response/update_round.py
"""

import pytest
import yaml
from pathlib import Path
import sys
from io import StringIO

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hooks"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hooks" / "post-response"))

from update_round import update_round


class TestUpdateRound:
    """Tests for update_round function."""
    
    def test_increments_round(self, tmp_path, capsys):
        """Test round counter is incremented."""
        meta = {
            'current_round': 5,
            'other_field': 'preserved'
        }
        (tmp_path / "meta.yaml").write_text(yaml.dump(meta))
        
        update_round(str(tmp_path))
        
        updated_meta = yaml.safe_load((tmp_path / "meta.yaml").read_text())
        assert updated_meta['current_round'] == 6
        assert updated_meta['other_field'] == 'preserved'
    
    def test_starts_from_zero(self, tmp_path, capsys):
        """Test round counter starts from 0 if not present."""
        meta = {'topic': 'test'}
        (tmp_path / "meta.yaml").write_text(yaml.dump(meta))
        
        update_round(str(tmp_path))
        
        updated_meta = yaml.safe_load((tmp_path / "meta.yaml").read_text())
        assert updated_meta['current_round'] == 1
    
    def test_prints_update_message(self, tmp_path, capsys):
        """Test update message is printed."""
        meta = {'current_round': 3}
        (tmp_path / "meta.yaml").write_text(yaml.dump(meta))
        
        update_round(str(tmp_path))
        
        captured = capsys.readouterr()
        assert "3 → 4" in captured.out
        assert "✓" in captured.out
    
    def test_no_meta_file(self, tmp_path, capsys):
        """Test warning when meta.yaml doesn't exist."""
        update_round(str(tmp_path))
        
        captured = capsys.readouterr()
        assert "Warning" in captured.out
        assert "not found" in captured.out
    
    def test_preserves_yaml_structure(self, tmp_path):
        """Test that YAML structure is preserved."""
        meta = {
            'topic': 'Test Topic',
            'current_round': 2,
            'decisions': [
                {'id': 'D1', 'title': 'Decision 1'}
            ],
            'config': {
                'nested': 'value'
            }
        }
        (tmp_path / "meta.yaml").write_text(yaml.dump(meta))
        
        update_round(str(tmp_path))
        
        updated_meta = yaml.safe_load((tmp_path / "meta.yaml").read_text())
        assert updated_meta['current_round'] == 3
        assert updated_meta['topic'] == 'Test Topic'
        assert updated_meta['decisions'] == [{'id': 'D1', 'title': 'Decision 1'}]
        assert updated_meta['config']['nested'] == 'value'
