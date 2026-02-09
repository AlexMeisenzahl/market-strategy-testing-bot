"""
Base Client Interface

Defines the base interface that all data clients must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseClient(ABC):
    """Base interface for all data clients"""

    def __init__(self):
        """Initialize the base client"""
        self._connected = False

    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the data source

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to the data source

        Returns:
            Dictionary with:
            - success: bool - Whether connection test passed
            - message: str - Success message
            - error: str - Error message if failed (empty if success)
        """
        pass

    def is_connected(self) -> bool:
        """
        Check if client is connected

        Returns:
            True if connected, False otherwise
        """
        return self._connected

    def disconnect(self) -> None:
        """Disconnect from the data source"""
        self._connected = False
