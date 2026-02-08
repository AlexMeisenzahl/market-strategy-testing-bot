"""
Tests for Update Service

Run with: pytest tests/test_update_service.py
"""

import pytest
from pathlib import Path
import tempfile
import time
from datetime import datetime, timezone, timedelta
from services.update_service import UpdateService, UpdateStatus


class TestUpdateService:
    """Test suite for UpdateService"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def update_service(self, temp_dir):
        """Create UpdateService instance with temp directory"""
        return UpdateService(temp_dir)

    def test_lock_creation(self, update_service):
        """Test update lock creation"""
        update_id = "test-lock-123"
        success = update_service._create_lock(update_id)
        assert success is True
        assert update_service.lock_file.exists()

    def test_lock_detection(self, update_service):
        """Test lock detection"""
        # No lock initially
        is_locked, data = update_service._is_locked()
        assert is_locked is False

        # Create lock
        update_service._create_lock("test-123")

        # Should be locked now
        is_locked, data = update_service._is_locked()
        assert is_locked is True
        assert data["update_id"] == "test-123"

    def test_stale_lock_detection(self, update_service):
        """Test stale lock detection (>30 min)"""
        # Create lock
        update_service._create_lock("test-123")

        # Manually set old timestamp (simulate old lock)
        import json

        old_time = datetime.now(timezone.utc) - timedelta(minutes=35)
        lock_data = {
            "update_id": "test-123",
            "start_time": old_time.isoformat().replace("+00:00", "Z"),
            "pid": 12345,
            "step": "checking",
        }

        with open(update_service.lock_file, "w") as f:
            json.dump(lock_data, f)

        # Should detect as stale
        is_locked, data = update_service._is_locked()
        assert is_locked is False  # Stale locks return False

    def test_unlock(self, update_service):
        """Test unlocking"""
        # Create lock
        update_service._create_lock("test-123")
        assert update_service.lock_file.exists()

        # Unlock
        success = update_service.unlock_update(force=True)
        assert success is True
        assert not update_service.lock_file.exists()

    def test_pre_flight_checks(self, update_service):
        """Test pre-flight checks"""
        all_passed, checks = update_service.pre_flight_checks()

        # Should return list of checks
        assert isinstance(checks, list)
        assert len(checks) > 0

        # Each check should have required fields
        for check in checks:
            assert "name" in check
            assert "passed" in check
            assert "message" in check

    def test_progress_update(self, update_service):
        """Test progress tracking"""
        update_service.current_update_id = "test-123"

        # Update progress
        update_service._update_progress(
            UpdateStatus.DOWNLOADING, 50, "Test message", ["Log 1", "Log 2"]
        )

        # Check progress file exists
        assert update_service.progress_file.exists()

        # Read progress
        progress = update_service.get_progress()
        assert progress is not None
        assert progress["update_id"] == "test-123"
        assert progress["progress"] == 50
        assert progress["message"] == "Test message"
        assert len(progress["logs"]) == 2


class TestBackupCreation:
    """Test backup functionality"""

    @pytest.fixture
    def update_service(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)

            # Create some files to backup
            (base_dir / "test.py").write_text("print('test')")
            (base_dir / "VERSION").write_text("1.0.0")

            us = UpdateService(base_dir)
            yield us

    def test_backup_creation(self, update_service):
        """Test creating a backup"""
        success, backup_name = update_service.create_backup()

        assert success is True
        assert backup_name is not None
        assert "backup_" in backup_name

        # Check backup exists
        backup_path = update_service.backups_dir / backup_name
        assert backup_path.exists()
        assert backup_path.is_dir()

    def test_backup_cleanup(self, update_service):
        """Test old backup cleanup"""
        # Create 7 backup directories manually to test cleanup
        for i in range(7):
            backup_name = f"backup_test_{i:02d}"
            backup_path = update_service.backups_dir / backup_name
            backup_path.mkdir(exist_ok=True)
            # Touch a file to ensure it's not empty
            (backup_path / "test.txt").write_text("test")
            time.sleep(0.01)  # Ensure different timestamps

        # Run cleanup
        update_service._cleanup_old_backups(keep=5)

        # Should only keep 5
        backups = list(update_service.backups_dir.iterdir())
        assert len(backups) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
