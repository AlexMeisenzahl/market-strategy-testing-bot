"""
Tests for Version Manager

Run with: pytest tests/test_version_manager.py
"""

import pytest
from pathlib import Path
import tempfile
import json
from version_manager import VersionManager


class TestVersionManager:
    """Test suite for VersionManager"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def version_manager(self, temp_dir):
        """Create VersionManager instance with temp directory"""
        return VersionManager(temp_dir)
    
    def test_get_current_version_default(self, version_manager):
        """Test getting version when file doesn't exist"""
        version = version_manager.get_current_version()
        assert version == "0.0.0"
    
    def test_set_and_get_version(self, version_manager):
        """Test setting and getting version"""
        version_manager.set_current_version("1.2.3")
        version = version_manager.get_current_version()
        assert version == "1.2.3"
    
    def test_compare_versions(self, version_manager):
        """Test version comparison"""
        # Test less than
        assert version_manager.compare_versions("1.0.0", "2.0.0") == -1
        assert version_manager.compare_versions("1.0.0", "1.1.0") == -1
        assert version_manager.compare_versions("1.0.0", "1.0.1") == -1
        
        # Test equal
        assert version_manager.compare_versions("1.0.0", "1.0.0") == 0
        
        # Test greater than
        assert version_manager.compare_versions("2.0.0", "1.0.0") == 1
        assert version_manager.compare_versions("1.1.0", "1.0.0") == 1
        assert version_manager.compare_versions("1.0.1", "1.0.0") == 1
        
        # Test with 'v' prefix
        assert version_manager.compare_versions("v1.0.0", "v2.0.0") == -1
    
    def test_update_history(self, version_manager):
        """Test adding and getting update history"""
        # Add record
        record = {
            'update_id': 'test-123',
            'from_version': '1.0.0',
            'to_version': '1.1.0',
            'status': 'success'
        }
        version_manager.add_update_record(record)
        
        # Get history
        history = version_manager.get_update_history()
        assert len(history) == 1
        assert history[0]['update_id'] == 'test-123'
        assert 'date' in history[0]  # Should auto-add date
    
    def test_get_latest_backup(self, version_manager, temp_dir):
        """Test getting latest backup"""
        # Create some backup directories
        backups_dir = temp_dir / "backups"
        backups_dir.mkdir()
        
        backup1 = backups_dir / "backup_20240101_120000"
        backup2 = backups_dir / "backup_20240102_120000"
        backup1.mkdir()
        backup2.mkdir()
        
        # Get latest
        latest = version_manager.get_latest_backup()
        assert latest is not None
        assert "backup_" in latest


class TestVersionChecking:
    """Test version checking and update detection"""
    
    @pytest.fixture
    def version_manager(self, temp_dir):
        with tempfile.TemporaryDirectory() as tmpdir:
            vm = VersionManager(Path(tmpdir))
            vm.set_current_version("1.0.0")
            yield vm
    
    def test_check_for_updates_structure(self, version_manager):
        """Test that check_for_updates returns expected structure"""
        result = version_manager.check_for_updates()
        
        # Should have these keys
        assert 'available' in result
        assert 'current' in result
        assert 'latest' in result
        assert 'changes' in result
        assert 'release_notes' in result
        
        # Types should be correct
        assert isinstance(result['available'], bool)
        assert isinstance(result['current'], str)
        assert isinstance(result['latest'], str)
        assert isinstance(result['changes'], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
