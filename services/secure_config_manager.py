"""
Secure Credentials Manager

Manages encrypted storage of API credentials and sensitive configuration.
Uses AES-256 encryption via Fernet for secure credential storage.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet


class SecureConfigManager:
    """Manages encrypted API credentials and configuration"""

    # Fields that should be encrypted
    SENSITIVE_FIELDS = {
        "api_key",
        "api_secret",
        "bot_token",
        "password",
        "app_password",
        "secret",
        "private_key",
    }

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize secure config manager

        Args:
            config_dir: Directory for storing config files (defaults to ./config)
        """
        if config_dir is None:
            # Use config directory in project root
            base_dir = Path(__file__).resolve().parent.parent
            config_dir = base_dir / "config"
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.credentials_file = self.config_dir / "credentials.json"
        self.key_file = self.config_dir / "encryption.key"
        
        # Initialize or load encryption key
        self._cipher = self._init_cipher()

    def _init_cipher(self) -> Fernet:
        """
        Initialize Fernet cipher with encryption key

        Returns:
            Fernet cipher instance
        """
        if self.key_file.exists():
            # Load existing key
            with open(self.key_file, "rb") as f:
                key = f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(key)
            # Secure the key file (Unix only)
            if hasattr(os, "chmod"):
                os.chmod(self.key_file, 0o600)
        
        return Fernet(key)

    def _load_credentials(self) -> Dict[str, Any]:
        """
        Load credentials from encrypted storage

        Returns:
            Dictionary of all stored credentials
        """
        if not self.credentials_file.exists():
            return {}
        
        try:
            with open(self.credentials_file, "r") as f:
                encrypted_data = json.load(f)
            
            # Decrypt each service's credentials
            credentials = {}
            for service, encrypted_creds in encrypted_data.items():
                if isinstance(encrypted_creds, dict):
                    credentials[service] = self._decrypt_dict(encrypted_creds)
                else:
                    credentials[service] = encrypted_creds
            
            return credentials
        except Exception as e:
            print(f"Error loading credentials: {e}")
            return {}

    def _save_credentials(self, credentials: Dict[str, Any]) -> None:
        """
        Save credentials to encrypted storage

        Args:
            credentials: Dictionary of all credentials to save
        """
        try:
            # Encrypt sensitive fields
            encrypted_data = {}
            for service, creds in credentials.items():
                if isinstance(creds, dict):
                    encrypted_data[service] = self._encrypt_dict(creds)
                else:
                    encrypted_data[service] = creds
            
            # Save to file
            with open(self.credentials_file, "w") as f:
                json.dump(encrypted_data, f, indent=2)
            
            # Secure the credentials file (Unix only)
            if hasattr(os, "chmod"):
                os.chmod(self.credentials_file, 0o600)
        except Exception as e:
            print(f"Error saving credentials: {e}")
            raise

    def _encrypt_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt sensitive fields in a dictionary

        Args:
            data: Dictionary to encrypt

        Returns:
            Dictionary with sensitive fields encrypted
        """
        encrypted = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in self.SENSITIVE_FIELDS):
                if value and isinstance(value, str):
                    # Encrypt the value
                    encrypted[key] = self._cipher.encrypt(value.encode()).decode()
                else:
                    encrypted[key] = value
            else:
                encrypted[key] = value
        return encrypted

    def _decrypt_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt sensitive fields in a dictionary

        Args:
            data: Dictionary with encrypted fields

        Returns:
            Dictionary with sensitive fields decrypted
        """
        decrypted = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in self.SENSITIVE_FIELDS):
                if value and isinstance(value, str):
                    try:
                        # Try to decrypt
                        decrypted[key] = self._cipher.decrypt(value.encode()).decode()
                    except Exception:
                        # If decryption fails, assume it's not encrypted
                        decrypted[key] = value
                else:
                    decrypted[key] = value
            else:
                decrypted[key] = value
        return decrypted

    def save_api_credentials(self, service: str, credentials: Dict[str, Any]) -> None:
        """
        Save API credentials for a service (encrypted)

        Args:
            service: Service name (e.g., 'polymarket', 'crypto', 'telegram', 'email')
            credentials: Credential dictionary to save
        """
        all_credentials = self._load_credentials()
        all_credentials[service] = credentials
        self._save_credentials(all_credentials)

    def get_api_credentials(self, service: str) -> Optional[Dict[str, Any]]:
        """
        Get decrypted API credentials for a service

        Args:
            service: Service name

        Returns:
            Credential dictionary or None if not found
        """
        all_credentials = self._load_credentials()
        return all_credentials.get(service)

    def get_masked_credentials(self, service: str) -> Optional[Dict[str, Any]]:
        """
        Get credentials with sensitive fields masked

        Args:
            service: Service name

        Returns:
            Credential dictionary with masked sensitive values
        """
        credentials = self.get_api_credentials(service)
        if not credentials:
            return None
        
        masked = {}
        for key, value in credentials.items():
            if any(sensitive in key.lower() for sensitive in self.SENSITIVE_FIELDS):
                if value and isinstance(value, str) and len(value) > 6:
                    # Show only last 6 characters
                    masked[key] = f"****{value[-6:]}"
                elif value:
                    masked[key] = "****"
                else:
                    masked[key] = ""
            else:
                masked[key] = value
        return masked

    def has_polymarket_api(self) -> bool:
        """
        Check if Polymarket API credentials are configured

        Returns:
            True if configured, False otherwise
        """
        creds = self.get_api_credentials("polymarket")
        if not creds:
            return False
        # Check if api_key exists and is not empty
        return bool(creds.get("api_key"))

    def has_crypto_api(self) -> bool:
        """
        Check if crypto API credentials are configured

        Returns:
            True if configured, False otherwise
        """
        creds = self.get_api_credentials("crypto")
        if not creds:
            return False
        # CoinGecko doesn't require API key for basic tier
        # Consider it configured if provider is set
        return bool(creds.get("provider"))

    def get_data_mode(self) -> str:
        """
        Determine current data mode based on API configuration

        Returns:
            'live' if APIs are configured, 'mock' otherwise
        """
        # Consider it live mode if at least one API is configured
        if self.has_polymarket_api() or self.has_crypto_api():
            return "live"
        return "mock"

    def delete_credentials(self, service: str) -> bool:
        """
        Delete credentials for a service

        Args:
            service: Service name

        Returns:
            True if deleted, False if not found
        """
        all_credentials = self._load_credentials()
        if service in all_credentials:
            del all_credentials[service]
            self._save_credentials(all_credentials)
            return True
        return False

    def list_services(self) -> list:
        """
        List all services with stored credentials

        Returns:
            List of service names
        """
        all_credentials = self._load_credentials()
        return list(all_credentials.keys())
