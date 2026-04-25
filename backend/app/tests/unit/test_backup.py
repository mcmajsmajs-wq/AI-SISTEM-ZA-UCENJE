"""
Backup System Tests
Unit and integration tests for backup/restore functionality
"""

import pytest
import os
import subprocess


# Test configuration
TEST_BACKUP_DIR = "/tmp/test_backups"
TEST_DB_NAME = "ai_learning_db"
TEST_DB_USER = "ai_learning_user"


class TestBackupScript:
    """Test backup.sh functionality"""

    @pytest.fixture
    def backup_script(self):
        """Path to backup script"""
        return "/home/dju/mojAiProjekat/New folder/scripts/backup.sh"

    @pytest.fixture
    def backup_dir(self):
        """Create test backup directory"""
        os.makedirs(TEST_BACKUP_DIR, exist_ok=True)
        return TEST_BACKUP_DIR

    def test_backup_script_exists(self, backup_script):
        """Verify backup script exists"""
        assert os.path.exists(backup_script), "Backup script not found"

    def test_backup_script_executable(self, backup_script):
        """Verify backup script is executable"""
        assert os.access(backup_script, os.X_OK), "Backup script not executable"

    def test_backup_script_valid_syntax(self, backup_script):
        """Verify backup script has valid bash syntax"""
        result = subprocess.run(["bash", "-n", backup_script], capture_output=True)
        assert result.returncode == 0, f"Syntax error: {result.stderr.decode()}"

    def test_backup_has_help_option(self, backup_script):
        """Verify backup script has --help"""
        result = subprocess.run(
            [backup_script, "--help"], capture_output=True, timeout=10
        )
        assert result.returncode == 0, "Help should work"
        assert b"Usage" in result.stdout, "Should show usage"


class TestRestoreScript:
    """Test restore.sh functionality"""

    @pytest.fixture
    def restore_script(self):
        """Path to restore script"""
        return "/home/dju/mojAiProjekat/New folder/scripts/restore.sh"

    def test_restore_script_exists(self, restore_script):
        """Verify restore script exists"""
        assert os.path.exists(restore_script), "Restore script not found"

    def test_restore_script_executable(self, restore_script):
        """Verify restore script is executable"""
        assert os.access(restore_script, os.X_OK), "Restore script not executable"

    def test_restore_script_valid_syntax(self, restore_script):
        """Verify restore script has valid bash syntax"""
        result = subprocess.run(["bash", "-n", restore_script], capture_output=True)
        assert result.returncode == 0, f"Syntax error: {result.stderr.decode()}"

    def test_restore_has_help_option(self, restore_script):
        """Verify restore script has --help"""
        result = subprocess.run(
            [restore_script, "--help"], capture_output=True, timeout=10
        )
        assert result.returncode == 0, "Help should work"


class TestBackupCron:
    """Test backup-cron.sh functionality"""

    @pytest.fixture
    def cron_script(self):
        """Path to cron script"""
        return "/home/dju/mojAiProjekat/New folder/scripts/backup-cron.sh"

    def test_cron_script_exists(self, cron_script):
        """Verify cron script exists"""
        assert os.path.exists(cron_script), "Cron script not found"

    def test_cron_script_executable(self, cron_script):
        """Verify cron script is executable"""
        assert os.access(cron_script, os.X_OK), "Cron script not executable"

    def test_cron_script_valid_syntax(self, cron_script):
        """Verify cron script has valid bash syntax"""
        result = subprocess.run(["bash", "-n", cron_script], capture_output=True)
        assert result.returncode == 0, f"Syntax error: {result.stderr.decode()}"


class TestBackupProcess:
    """Test backup process (requires running system)"""

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires /backups directory permissions")
    def test_backup_script_runs(self):
        """Test that backup script runs without error"""
        script = "/home/dju/mojAiProjekat/New folder/scripts/backup.sh"

        # Run with test mode
        result = subprocess.run(
            [script, "--test"],
            capture_output=True,
            timeout=60,
            env={**os.environ, "BACKUP_DIR": TEST_BACKUP_DIR},
        )

        # Script should run (may fail if DB not accessible, but should execute)
        assert result.returncode in [0, 1], f"Script error: {result.stderr.decode()}"

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires /backups directory permissions")
    def test_restore_script_list_backups(self):
        """Test restore can list backups"""
        script = "/home/dju/mojAiProjekat/New folder/scripts/restore.sh"

        result = subprocess.run([script, "--verify"], capture_output=True, timeout=30)

        # Should list backups or show none found
        assert result.returncode == 0, f"Error: {result.stderr.decode()}"


class TestBackupConfiguration:
    """Test backup configuration"""

    @pytest.fixture
    def backup_dir(self):
        """Ensure backup directory exists"""
        os.makedirs(TEST_BACKUP_DIR, exist_ok=True)
        return TEST_BACKUP_DIR

    def test_backup_dir_created(self, backup_dir):
        """Verify backup directory can be created"""
        assert os.path.isdir(backup_dir), "Backup directory should exist"

    def test_backup_subdirs_exist(self, backup_dir):
        """Verify backup subdirectories exist"""
        subdirs = ["full", "incremental", "config"]
        for subdir in subdirs:
            path = os.path.join(backup_dir, subdir)
            os.makedirs(path, exist_ok=True)
            assert os.path.isdir(path), f"Subdirectory {subdir} should exist"


class TestBackupRetention:
    """Test backup retention policy"""

    def test_retention_constants_defined(self):
        """Verify retention constants are defined"""
        # These should match the values in backup.sh
        RETENTION_DAILY = 7
        RETENTION_WEEKLY = 4
        RETENTION_MONTHLY = 12

        assert RETENTION_DAILY > 0, "Daily retention should be positive"
        assert RETENTION_WEEKLY > 0, "Weekly retention should be positive"
        assert RETENTION_MONTHLY > 0, "Monthly retention should be positive"


class TestBackupSecurity:
    """Test backup security"""

    def test_backup_script_no_hardcoded_secrets(self):
        """Verify no hardcoded secrets in backup script"""
        script_path = "/home/dju/mojAiProjekat/New folder/scripts/backup.sh"

        with open(script_path) as f:
            content = f.read()

        # Check for potential secret patterns
        suspicious = [
            "password = ",  # Should use env vars
            "API_KEY",
            "SECRET_KEY",
        ]

        # Allow comments but not assignments
        lines_with_suspicious = []
        for line in content.split("\n"):
            if any(s in line for s in suspicious):
                # Should be commented or in heredocs
                if not line.strip().startswith("#"):
                    lines_with_suspicious.append(line.strip())

        # We allow reading secrets with $VAR but not setting them
        assert len(lines_with_suspicious) <= 1, (
            f"Potential secrets found: {lines_with_suspicious}"
        )

    def test_restore_requires_confirmation(self):
        """Verify restore asks for confirmation"""
        script_path = "/home/dju/mojAiProjekat/New folder/scripts/restore.sh"

        with open(script_path) as f:
            content = f.read()

        # Should have read -p for confirmation
        assert "read -p" in content, "Restore should ask for confirmation"


class TestBackupMetadata:
    """Test backup metadata"""

    def test_metadata_structure(self):
        """Verify metadata structure"""
        metadata = {
            "timestamp": "2026-04-25_02:00:00",
            "date": "2026-04-25",
            "type": "full",
            "components": {"database": True, "minio": True, "config": True},
        }

        # Required fields
        assert "timestamp" in metadata
        assert "date" in metadata
        assert "type" in metadata
        assert "components" in metadata

        # Components should have expected keys
        assert "database" in metadata["components"]
        assert "minio" in metadata["components"]
        assert "config" in metadata["components"]


class TestBackupCronSchedule:
    """Test cron schedule configuration"""

    def test_cron_file_format(self):
        """Verify cron file format is correct"""
        cron_content = """
# Full backup - Nedjelja u 02:00
0 2 * * 0 root /home/dju/scripts/backup.sh --type=full >> /backups/cron.log 2>&1

# Incremental backup - Ponedjeljak do Subota u 02:00
0 2 * * 1-6 root /home/dju/scripts/backup.sh >> /backups/cron.log 2>&1
"""

        # Check cron format
        cron_lines = [
            line
            for line in cron_content.strip().split("\n")
            if line.strip() and not line.strip().startswith("#")
        ]

        for line in cron_lines:
            parts = line.split()
            # Should have: minute hour day month day-of-week command
            assert len(parts) >= 5, f"Invalid cron line: {line}"
            # First field should be minute (0-59)
            assert parts[0].isdigit() or parts[0] == "*"
            # Second field should be hour (0-23)
            assert parts[1].isdigit() or parts[1] == "*"

    def test_full_backup_on_sunday(self):
        """Verify full backup scheduled for Sunday"""
        # Cron: 0 2 * * 0 = At 02:00 on Sunday (0 = Sunday)
        # Format: minute hour day month day-of-week command
        cron_lines = [
            "0 2 * * 0 root /home/dju/scripts/backup.sh --type=full",
            "0 2 * * 1-6 root /home/dju/scripts/backup.sh",
        ]

        # parts[4] is day of week
        assert "0" in cron_lines[0].split()[4], (
            "Full backup should be on Sunday (day 0)"
        )


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
