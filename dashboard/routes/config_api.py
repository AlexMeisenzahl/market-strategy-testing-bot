"""
Configuration API Routes

Provides REST API endpoints for managing bot configuration from web interface:
- Get current configuration
- Update configuration parameters
- Validate configuration changes
- Reset to defaults
"""

from flask import Blueprint, jsonify, request
import yaml
from pathlib import Path
from typing import Dict, Any
import os


config_api = Blueprint('config_api', __name__, url_prefix='/api/config')

# Configuration file path
CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config.yaml"


@config_api.route('/', methods=['GET'])
def get_config():
    """
    Get current configuration
    
    Returns:
        JSON response with full configuration
    """
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
            
        return jsonify({
            "success": True,
            "config": config
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@config_api.route('/', methods=['PUT'])
def update_config():
    """
    Update configuration
    
    Request body should contain configuration changes in JSON format
    
    Returns:
        JSON response with success status
    """
    try:
        updates = request.get_json()
        
        if not updates:
            return jsonify({
                "success": False,
                "error": "No configuration data provided"
            }), 400
            
        # Load current config
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
            
        # Apply updates
        config = _deep_update(config, updates)
        
        # Validate configuration
        validation = _validate_config(config)
        if not validation["valid"]:
            return jsonify({
                "success": False,
                "error": "Configuration validation failed",
                "details": validation["errors"]
            }), 400
            
        # Save configuration
        with open(CONFIG_PATH, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            
        return jsonify({
            "success": True,
            "message": "Configuration updated successfully",
            "config": config
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@config_api.route('/section/<section>', methods=['GET'])
def get_config_section(section):
    """
    Get a specific configuration section
    
    Args:
        section: Configuration section name
        
    Returns:
        JSON response with section data
    """
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
            
        if section not in config:
            return jsonify({
                "success": False,
                "error": f"Section '{section}' not found"
            }), 404
            
        return jsonify({
            "success": True,
            "section": section,
            "data": config[section]
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@config_api.route('/section/<section>', methods=['PUT'])
def update_config_section(section):
    """
    Update a specific configuration section
    
    Args:
        section: Configuration section name
        
    Returns:
        JSON response with success status
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No data provided"
            }), 400
            
        # Load current config
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
            
        # Update section
        config[section] = data
        
        # Validate
        validation = _validate_config(config)
        if not validation["valid"]:
            return jsonify({
                "success": False,
                "error": "Configuration validation failed",
                "details": validation["errors"]
            }), 400
            
        # Save
        with open(CONFIG_PATH, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            
        return jsonify({
            "success": True,
            "message": f"Section '{section}' updated successfully"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@config_api.route('/validate', methods=['POST'])
def validate_config():
    """
    Validate configuration without saving
    
    Returns:
        JSON response with validation results
    """
    try:
        config = request.get_json()
        
        if not config:
            return jsonify({
                "success": False,
                "error": "No configuration provided"
            }), 400
            
        validation = _validate_config(config)
        
        return jsonify({
            "success": True,
            "valid": validation["valid"],
            "errors": validation["errors"],
            "warnings": validation["warnings"]
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@config_api.route('/reset', methods=['POST'])
def reset_config():
    """
    Reset configuration to example defaults
    
    Returns:
        JSON response with success status
    """
    try:
        example_config_path = Path(__file__).resolve().parent.parent.parent / "config.example.yaml"
        
        if not example_config_path.exists():
            return jsonify({
                "success": False,
                "error": "Example configuration file not found"
            }), 404
            
        # Copy example config to config
        with open(example_config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        with open(CONFIG_PATH, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            
        return jsonify({
            "success": True,
            "message": "Configuration reset to defaults",
            "config": config
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# Helper functions

def _deep_update(base: Dict, updates: Dict) -> Dict:
    """
    Deep update dictionary
    
    Args:
        base: Base dictionary
        updates: Updates to apply
        
    Returns:
        Updated dictionary
    """
    for key, value in updates.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            base[key] = _deep_update(base[key], value)
        else:
            base[key] = value
    return base


def _validate_config(config: Dict) -> Dict[str, Any]:
    """
    Validate configuration
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Validation result with errors and warnings
    """
    errors = []
    warnings = []
    
    # Required fields
    required_fields = ['paper_trading', 'max_trade_size', 'min_profit_margin']
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")
            
    # Paper trading must be true (safety)
    if not config.get('paper_trading', False):
        errors.append("Paper trading must be enabled (paper_trading: true)")
        
    # Validate numeric ranges
    if 'max_trade_size' in config:
        max_trade = config['max_trade_size']
        if not isinstance(max_trade, (int, float)) or max_trade <= 0:
            errors.append("max_trade_size must be a positive number")
        elif max_trade > 1000:
            warnings.append("max_trade_size is very high (>$1000)")
            
    if 'min_profit_margin' in config:
        min_profit = config['min_profit_margin']
        if not isinstance(min_profit, (int, float)) or min_profit < 0:
            errors.append("min_profit_margin must be a non-negative number")
            
    # Validate strategies section
    if 'strategies' in config:
        strategies = config['strategies']
        if not isinstance(strategies, dict):
            errors.append("strategies must be a dictionary")
        else:
            # Check each strategy
            for strategy_name, strategy_config in strategies.items():
                if not isinstance(strategy_config, dict):
                    errors.append(f"Strategy '{strategy_name}' configuration must be a dictionary")
                    continue
                    
                # Validate enabled flag
                if 'enabled' in strategy_config and not isinstance(strategy_config['enabled'], bool):
                    errors.append(f"Strategy '{strategy_name}' enabled flag must be boolean")
                    
    # Validate dashboard section
    if 'dashboard' in config:
        dashboard = config['dashboard']
        if 'port' in dashboard:
            port = dashboard['port']
            if not isinstance(port, int) or port < 1024 or port > 65535:
                errors.append("dashboard.port must be between 1024 and 65535")
                
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }
