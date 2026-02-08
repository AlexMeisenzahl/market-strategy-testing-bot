"""
Version Manager for Market Strategy Testing Bot

Handles version tracking, GitHub integration, and update history.
"""

import json
import os
import requests
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from packaging import version as pkg_version

from logger import get_logger

logger = get_logger()


class VersionManager:
    """Manages version tracking and update checking"""

    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Path(__file__).resolve().parent
        self.version_file = self.base_dir / "VERSION"
        self.history_file = self.base_dir / "logs" / "update_history.json"
        self.github_owner = "AlexMeisenzahl"
        self.github_repo = "market-strategy-testing-bot"
        self.github_api = (
            f"https://api.github.com/repos/{self.github_owner}/{self.github_repo}"
        )

        # Ensure logs directory exists
        self.history_file.parent.mkdir(exist_ok=True)

    def get_current_version(self) -> str:
        """
        Get current version from VERSION file

        Returns:
            Version string (e.g., "1.0.0")
        """
        try:
            if self.version_file.exists():
                version = self.version_file.read_text().strip()
                logger.log_info(f"Current version: {version}")
                return version
            else:
                logger.log_warning("VERSION file not found, defaulting to 0.0.0")
                return "0.0.0"
        except Exception as e:
            logger.log_error(f"Error reading version file: {e}")
            return "0.0.0"

    def set_current_version(self, new_version: str) -> bool:
        """
        Update VERSION file with new version

        Args:
            new_version: New version string

        Returns:
            True if successful
        """
        try:
            self.version_file.write_text(new_version + "\n")
            logger.log_info(f"Updated version to {new_version}")
            return True
        except Exception as e:
            logger.log_error(f"Error updating version file: {e}")
            return False

    def fetch_latest_release(self) -> Optional[Dict]:
        """
        Fetch latest release from GitHub

        Returns:
            Release data dict or None if error
        """
        try:
            response = requests.get(
                f"{self.github_api}/releases/latest",
                timeout=10,
                headers={"Accept": "application/vnd.github.v3+json"},
            )

            if response.status_code == 200:
                release = response.json()
                logger.log_info(f"Latest release: {release.get('tag_name')}")
                return release
            elif response.status_code == 404:
                logger.log_warning("No releases found on GitHub")
                return None
            else:
                logger.log_error(f"GitHub API error: {response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            logger.log_error(f"Error fetching latest release: {e}")
            return None

    def fetch_all_releases(self, per_page: int = 10) -> List[Dict]:
        """
        Fetch all releases from GitHub

        Args:
            per_page: Number of releases per page

        Returns:
            List of release data dicts
        """
        try:
            response = requests.get(
                f"{self.github_api}/releases",
                params={"per_page": per_page},
                timeout=10,
                headers={"Accept": "application/vnd.github.v3+json"},
            )

            if response.status_code == 200:
                releases = response.json()
                logger.log_info(f"Fetched {len(releases)} releases")
                return releases
            else:
                logger.log_error(f"GitHub API error: {response.status_code}")
                return []

        except requests.exceptions.RequestException as e:
            logger.log_error(f"Error fetching releases: {e}")
            return []

    def compare_versions(self, version1: str, version2: str) -> int:
        """
        Compare two semantic versions

        Args:
            version1: First version string
            version2: Second version string

        Returns:
            -1 if version1 < version2
             0 if version1 == version2
             1 if version1 > version2
        """
        try:
            # Remove 'v' prefix if present
            v1 = version1.lstrip("v")
            v2 = version2.lstrip("v")

            v1_parsed = pkg_version.parse(v1)
            v2_parsed = pkg_version.parse(v2)

            if v1_parsed < v2_parsed:
                return -1
            elif v1_parsed > v2_parsed:
                return 1
            else:
                return 0
        except Exception as e:
            logger.log_error(f"Error comparing versions: {e}")
            return 0

    def check_for_updates(self) -> Dict:
        """
        Check if updates are available

        Returns:
            Dict with update information:
            {
                'available': bool,
                'current': str,
                'latest': str,
                'changes': List[str],
                'release_notes': str,
                'published_at': str,
                'size_mb': float (estimated)
            }
        """
        current = self.get_current_version()
        release = self.fetch_latest_release()

        if not release:
            return {
                "available": False,
                "current": current,
                "latest": current,
                "changes": [],
                "release_notes": "",
                "published_at": "",
                "size_mb": 0,
            }

        latest = release.get("tag_name", "").lstrip("v")

        # Check if update available
        available = self.compare_versions(current, latest) < 0

        # Extract release notes
        release_notes = release.get("body", "")

        # Parse changelog items (look for bullet points)
        changes = []
        for line in release_notes.split("\n"):
            line = line.strip()
            if line.startswith("-") or line.startswith("*"):
                changes.append(line.lstrip("-*").strip())

        # Estimate size from assets (if available)
        size_mb = 0
        assets = release.get("assets", [])
        if assets:
            total_bytes = sum(asset.get("size", 0) for asset in assets)
            size_mb = round(total_bytes / (1024 * 1024), 1)
        else:
            # Default estimate for git clone
            size_mb = 15

        return {
            "available": available,
            "current": current,
            "latest": latest,
            "changes": changes,
            "release_notes": release_notes,
            "published_at": release.get("published_at", ""),
            "size_mb": size_mb,
            "html_url": release.get("html_url", ""),
        }

    def get_update_history(self) -> List[Dict]:
        """
        Get update history from JSON file

        Returns:
            List of update records
        """
        try:
            if self.history_file.exists():
                with open(self.history_file, "r") as f:
                    history = json.load(f)
                logger.log_info(f"Loaded {len(history)} update records")
                return history
            else:
                return []
        except Exception as e:
            logger.log_error(f"Error reading update history: {e}")
            return []

    def add_update_record(self, record: Dict) -> bool:
        """
        Add update record to history

        Args:
            record: Update record dict with keys:
                - update_id
                - date
                - from_version
                - to_version
                - status
                - duration_seconds
                - backup
                - changes
                - rollback_available
                - error (optional)

        Returns:
            True if successful
        """
        try:
            history = self.get_update_history()

            # Add timestamp if not present
            if "date" not in record:
                record["date"] = (
                    datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                )

            history.insert(0, record)  # Most recent first

            # Keep only last 50 records
            history = history[:50]

            with open(self.history_file, "w") as f:
                json.dump(history, f, indent=2)

            logger.log_info(f"Added update record: {record.get('update_id')}")
            return True

        except Exception as e:
            logger.log_error(f"Error adding update record: {e}")
            return False

    def get_latest_backup(self) -> Optional[str]:
        """
        Get the most recent backup directory name

        Returns:
            Backup directory name or None
        """
        try:
            backups_dir = self.base_dir / "backups"
            if not backups_dir.exists():
                return None

            # List all backup directories
            backups = [d for d in backups_dir.iterdir() if d.is_dir()]
            if not backups:
                return None

            # Sort by modification time, most recent first
            backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            return backups[0].name

        except Exception as e:
            logger.log_error(f"Error getting latest backup: {e}")
            return None
