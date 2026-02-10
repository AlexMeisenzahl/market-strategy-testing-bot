"""
Data Sources API Routes

Provides REST API endpoints for managing data source configurations:
- Get current data source settings
- Save API credentials (encrypted)
- Test API connections
- Check data mode (live/mock)
"""

from flask import Blueprint, jsonify, request
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from services.secure_config_manager import SecureConfigManager
from clients import (
    PolymarketClient,
    CoinGeckoClient,
    MockMarketClient,
    MockCryptoClient,
)

data_sources_api = Blueprint("data_sources_api", __name__, url_prefix="/api/settings")

# Initialize secure config manager
config_manager = SecureConfigManager()


@data_sources_api.route("/data-sources", methods=["GET"])
def get_data_sources():
    """
    Get current data source settings with masked credentials

    Returns:
        JSON response with data sources configuration
    """
    try:
        # Get masked credentials for each service
        polymarket = config_manager.get_masked_credentials("polymarket") or {}
        crypto = config_manager.get_masked_credentials("crypto") or {}
        telegram = config_manager.get_masked_credentials("telegram") or {}
        email = config_manager.get_masked_credentials("email") or {}

        # Determine current data mode
        data_mode = config_manager.get_data_mode()

        response = {
            "success": True,
            "data_mode": data_mode,
            "polymarket": {
                "endpoint": polymarket.get("endpoint", "https://clob.polymarket.com"),
                "api_key": polymarket.get("api_key", ""),
            },
            "crypto": {
                "provider": crypto.get("provider", "coingecko"),
                "endpoint": crypto.get("endpoint", "https://api.coingecko.com/api/v3"),
                "api_key": crypto.get("api_key", ""),
            },
            "telegram": {
                "bot_token": telegram.get("bot_token", ""),
                "chat_id": telegram.get("chat_id", ""),
            },
            "email": {
                "smtp_server": email.get("smtp_server", "smtp.gmail.com"),
                "smtp_port": email.get("smtp_port", 587),
                "username": email.get("username", ""),
                "password": email.get("password", ""),
            },
        }

        return jsonify(response)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@data_sources_api.route("/data-sources", methods=["POST"])
def save_data_sources():
    """
    Save API credentials for a data source (encrypted)

    Request body should contain:
    {
        "service": "polymarket|crypto|telegram|email",
        "credentials": {...}
    }

    Returns:
        JSON response with success status and new data mode
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        service = data.get("service")
        credentials = data.get("credentials")

        if not service:
            return jsonify({"success": False, "error": "Service name required"}), 400

        if not credentials:
            return jsonify({"success": False, "error": "Credentials required"}), 400

        # Validate service name
        valid_services = ["polymarket", "crypto", "telegram", "email"]
        if service not in valid_services:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Invalid service. Must be one of: {', '.join(valid_services)}",
                    }
                ),
                400,
            )

        # Phase 6B: merge with existing so partial updates (e.g. only api_key) do not wipe other fields
        existing = config_manager.get_api_credentials(service) or {}
        merged = {**existing}
        for k, v in credentials.items():
            if v is not None and str(v).strip():
                merged[k] = v.strip() if isinstance(v, str) else v
        config_manager.save_api_credentials(service, merged)

        # Get new data mode after saving
        data_mode = config_manager.get_data_mode()

        return jsonify(
            {
                "success": True,
                "message": f"{service.capitalize()} credentials saved successfully",
                "data_mode": data_mode,
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@data_sources_api.route("/test-connection", methods=["POST"])
def test_connection():
    """
    Test connection to a data source API

    Request body should contain:
    {
        "service": "polymarket|crypto|telegram|email",
        "credentials": {...} (optional, will use saved if not provided)
    }

    Returns:
        JSON response with connection test result
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        service = data.get("service")
        if not service:
            return jsonify({"success": False, "error": "Service name required"}), 400

        # Get credentials (from request or saved)
        credentials = data.get("credentials")
        if not credentials:
            credentials = config_manager.get_api_credentials(service)
            if not credentials:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": f"No credentials found for {service}",
                        }
                    ),
                    400,
                )

        # Test connection based on service
        if service == "polymarket":
            endpoint = credentials.get("endpoint", "https://clob.polymarket.com")
            api_key = credentials.get("api_key")
            client = PolymarketClient(endpoint=endpoint, api_key=api_key)
            result = client.test_connection()

        elif service == "crypto":
            provider = credentials.get("provider", "coingecko")
            if provider == "coingecko":
                endpoint = credentials.get(
                    "endpoint", "https://api.coingecko.com/api/v3"
                )
                api_key = credentials.get("api_key")
                client = CoinGeckoClient(endpoint=endpoint, api_key=api_key)
                result = client.test_connection()
            else:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": f"Unsupported crypto provider: {provider}",
                        }
                    ),
                    400,
                )

        elif service == "telegram":
            # For now, just return success (can add actual Telegram test later)
            result = {
                "success": True,
                "message": "Telegram credentials saved (test not implemented yet)",
                "error": "",
            }

        elif service == "email":
            # For now, just return success (can add actual email test later)
            result = {
                "success": True,
                "message": "Email credentials saved (test not implemented yet)",
                "error": "",
            }

        else:
            return (
                jsonify({"success": False, "error": f"Unknown service: {service}"}),
                400,
            )

        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# Phase 6B: Canonical list of integrations (SecureConfigManager only). Used by System & Settings UI.
INTEGRATION_SERVICES = [
    {"id": "polymarket", "label": "Polymarket", "description": "Prediction market data", "fields": ["endpoint", "api_key"]},
    {"id": "crypto", "label": "Crypto (CoinGecko)", "description": "Crypto prices", "fields": ["provider", "endpoint", "api_key"]},
    {"id": "telegram", "label": "Telegram", "description": "Notifications", "fields": ["bot_token", "chat_id"]},
    {"id": "email", "label": "Email (SMTP)", "description": "Email alerts", "fields": ["smtp_server", "smtp_port", "username", "password"]},
]
INTEGRATION_DEPENDENCIES = {
    "polymarket": ["Polymarket arbitrage", "Market data"],
    "crypto": ["Crypto momentum", "Price data", "Data sources"],
    "telegram": ["Notifications"],
    "email": ["Notifications"],
}


@data_sources_api.route("/integrations", methods=["GET"])
def get_integrations():
    """
    List all integrations with masked credentials only. Canonical source: SecureConfigManager.
    Used by System & Settings UI. Never returns raw secrets.
    """
    try:
        out = []
        for svc in INTEGRATION_SERVICES:
            sid = svc["id"]
            masked = config_manager.get_masked_credentials(sid) or {}
            out.append({
                "id": sid,
                "label": svc["label"],
                "description": svc["description"],
                "configured": bool(config_manager.get_api_credentials(sid)),
                "masked": masked,
                "used_by": INTEGRATION_DEPENDENCIES.get(sid, []),
            })
        return jsonify({"success": True, "integrations": out})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@data_sources_api.route("/data-mode", methods=["GET"])
def get_data_mode():
    """
    Get current data mode and configuration status

    Returns:
        JSON response with data mode and status for each service
    """
    try:
        data_mode = config_manager.get_data_mode()
        has_polymarket = config_manager.has_polymarket_api()
        has_crypto = config_manager.has_crypto_api()

        # Determine type for each service
        polymarket_type = "live" if has_polymarket else "mock"
        crypto_type = "live" if has_crypto else "mock"

        response = {
            "success": True,
            "data": {
                "mode": data_mode,
                "polymarket": {"configured": has_polymarket, "type": polymarket_type},
                "crypto": {"configured": has_crypto, "type": crypto_type},
            },
        }

        return jsonify(response)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
