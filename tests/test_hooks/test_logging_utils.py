"""
Tests for hooks/common/logging_utils.py
"""

import pytest
import logging
from pathlib import Path
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hooks"))

from common.logging_utils import (
    get_config_dir,
    get_data_dir,
    get_log_dir,
    ensure_directories,
    get_logger,
    log_hook_start,
    log_hook_end,
    log_file_operation,
    log_discuss_detection,
    log_meta_update,
    log_stale_detection,
    log_error,
    log_warning,
    log_info,
    log_debug,
)


class TestDirectoryPaths:
    """Tests for directory path functions."""
    
    def test_get_config_dir(self):
        """Test config directory path."""
        result = get_config_dir()
        assert result == Path.home() / ".config" / "DiscussForSpecs"
    
    def test_get_data_dir(self):
        """Test data directory path."""
        result = get_data_dir()
        assert result == Path.home() / "DiscussForSpecs"
    
    def test_get_log_dir(self):
        """Test log directory path."""
        result = get_log_dir()
        assert result == Path.home() / "DiscussForSpecs" / "logs"


class TestEnsureDirectories:
    """Tests for ensure_directories function."""
    
    def test_creates_directories(self, tmp_path, monkeypatch):
        """Test that directories are created."""
        # Mock Path.home() to return tmp_path
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        ensure_directories()
        
        config_dir = tmp_path / ".config" / "DiscussForSpecs"
        log_dir = tmp_path / "DiscussForSpecs" / "logs"
        
        assert config_dir.exists()
        assert log_dir.exists()


class TestGetLogger:
    """Tests for get_logger function."""
    
    def test_returns_logger(self, tmp_path, monkeypatch):
        """Test logger creation."""
        # Mock home directory
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        # Clear cached logger
        import common.logging_utils as logging_module
        logging_module._logger = None
        
        logger = get_logger("test-logger")
        
        assert logger is not None
        assert isinstance(logger, logging.Logger)
    
    def test_returns_same_instance(self, tmp_path, monkeypatch):
        """Test logger singleton behavior."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        import common.logging_utils as logging_module
        logging_module._logger = None
        
        logger1 = get_logger("test-logger")
        logger2 = get_logger("test-logger")
        
        assert logger1 is logger2


class TestLogHookStart:
    """Tests for log_hook_start function."""
    
    def test_logs_hook_start(self, tmp_path, monkeypatch):
        """Test hook start logging."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        import common.logging_utils as logging_module
        logging_module._logger = None
        
        # Should not raise
        log_hook_start("test_hook", {"key": "value"})
    
    def test_logs_without_input_data(self, tmp_path, monkeypatch):
        """Test hook start logging without input data."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        import common.logging_utils as logging_module
        logging_module._logger = None
        
        # Should not raise
        log_hook_start("test_hook")


class TestLogHookEnd:
    """Tests for log_hook_end function."""
    
    def test_logs_success(self, tmp_path, monkeypatch):
        """Test successful hook end logging."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        import common.logging_utils as logging_module
        logging_module._logger = None
        
        log_hook_end("test_hook", {"result": "ok"}, success=True)
    
    def test_logs_failure(self, tmp_path, monkeypatch):
        """Test failed hook end logging."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        import common.logging_utils as logging_module
        logging_module._logger = None
        
        log_hook_end("test_hook", {"error": "fail"}, success=False)


class TestLogFileOperation:
    """Tests for log_file_operation function."""
    
    def test_logs_operation(self, tmp_path, monkeypatch):
        """Test file operation logging."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        import common.logging_utils as logging_module
        logging_module._logger = None
        
        log_file_operation("READ", "/path/to/file.md", "success")
    
    def test_logs_without_details(self, tmp_path, monkeypatch):
        """Test file operation logging without details."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        import common.logging_utils as logging_module
        logging_module._logger = None
        
        log_file_operation("WRITE", "/path/to/file.md")


class TestLogDiscussDetection:
    """Tests for log_discuss_detection function."""
    
    def test_logs_with_file_type(self, tmp_path, monkeypatch):
        """Test discuss detection logging with file type."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        import common.logging_utils as logging_module
        logging_module._logger = None
        
        log_discuss_detection("/discuss/topic", "outline")
    
    def test_logs_without_file_type(self, tmp_path, monkeypatch):
        """Test discuss detection logging without file type."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        import common.logging_utils as logging_module
        logging_module._logger = None
        
        log_discuss_detection("/discuss/topic")


class TestLogMetaUpdate:
    """Tests for log_meta_update function."""
    
    def test_logs_changes(self, tmp_path, monkeypatch):
        """Test meta update logging."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        import common.logging_utils as logging_module
        logging_module._logger = None
        
        log_meta_update("/discuss/topic", {"current_run": 5, "pending": True})


class TestLogStaleDetection:
    """Tests for log_stale_detection function."""
    
    def test_logs_stale_items(self, tmp_path, monkeypatch):
        """Test stale detection logging with items."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        import common.logging_utils as logging_module
        logging_module._logger = None
        
        stale_items = [
            ("outline", 5, False),
            ("decisions", 10, True)
        ]
        log_stale_detection("/discuss/topic", stale_items)
    
    def test_logs_empty_stale_items(self, tmp_path, monkeypatch):
        """Test stale detection logging with no items."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        import common.logging_utils as logging_module
        logging_module._logger = None
        
        log_stale_detection("/discuss/topic", [])


class TestLogLevels:
    """Tests for simple log level functions."""
    
    def test_log_error_with_exception(self, tmp_path, monkeypatch):
        """Test error logging with exception."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        import common.logging_utils as logging_module
        logging_module._logger = None
        
        try:
            raise ValueError("test error")
        except Exception as e:
            log_error("Something went wrong", e)
    
    def test_log_error_without_exception(self, tmp_path, monkeypatch):
        """Test error logging without exception."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        import common.logging_utils as logging_module
        logging_module._logger = None
        
        log_error("Something went wrong")
    
    def test_log_warning(self, tmp_path, monkeypatch):
        """Test warning logging."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        import common.logging_utils as logging_module
        logging_module._logger = None
        
        log_warning("This is a warning")
    
    def test_log_info(self, tmp_path, monkeypatch):
        """Test info logging."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        import common.logging_utils as logging_module
        logging_module._logger = None
        
        log_info("This is info")
    
    def test_log_debug(self, tmp_path, monkeypatch):
        """Test debug logging."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        import common.logging_utils as logging_module
        logging_module._logger = None
        
        log_debug("This is debug")
