"""
Health Check Service

Monitors the health of all external services and APIs.
"""

import logging
import time
import requests
from typing import Dict, Any, Optional
from datetime import datetime
import sqlite3
from pathlib import Path


logger = logging.getLogger(__name__)


class HealthCheckService:
    """Service for checking health of external APIs and services."""
    
    def __init__(self):
        """Initialize health check service."""
        self.logger = logging.getLogger(__name__)
        self.last_check: Dict[str, datetime] = {}
        self.cache_ttl = 30  # Cache results for 30 seconds
    
    def check_all(self) -> Dict[str, Any]:
        """
        Check health of all services.
        
        Returns:
            Dictionary with health status for each service
        """
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'healthy',
            'services': {}
        }
        
        # Check crypto APIs
        results['services']['crypto_apis'] = {
            'coingecko': self.check_coingecko(),
            'binance': self.check_binance(),
            'coinbase': self.check_coinbase()
        }
        
        # Check prediction market APIs
        results['services']['prediction_markets'] = {
            'polymarket': self.check_polymarket(),
            'kalshi': self.check_kalshi()
        }
        
        # Check database
        results['services']['database'] = self.check_database()
        
        # Determine overall status
        all_services = []
        for category in results['services'].values():
            if isinstance(category, dict):
                for service in category.values():
                    if isinstance(service, dict) and 'status' in service:
                        all_services.append(service['status'])
            elif isinstance(category, dict) and 'status' in category:
                all_services.append(category['status'])
        
        if any(s == 'down' for s in all_services):
            results['overall_status'] = 'degraded'
        if all(s == 'down' for s in all_services):
            results['overall_status'] = 'down'
        
        return results
    
    def check_coingecko(self) -> Dict[str, Any]:
        """
        Check CoinGecko API health.
        
        Returns:
            Health status dict
        """
        return self._check_api(
            'coingecko',
            'https://api.coingecko.com/api/v3/ping',
            timeout=5
        )
    
    def check_binance(self) -> Dict[str, Any]:
        """
        Check Binance API health.
        
        Returns:
            Health status dict
        """
        return self._check_api(
            'binance',
            'https://api.binance.com/api/v3/ping',
            timeout=5
        )
    
    def check_coinbase(self) -> Dict[str, Any]:
        """
        Check Coinbase API health.
        
        Returns:
            Health status dict
        """
        return self._check_api(
            'coinbase',
            'https://api.coinbase.com/v2/time',
            timeout=5
        )
    
    def check_polymarket(self) -> Dict[str, Any]:
        """
        Check Polymarket API health.
        
        Returns:
            Health status dict
        """
        # Check GraphQL endpoint
        return self._check_api(
            'polymarket',
            'https://api.thegraph.com/subgraphs/name/polymarket/polymarket',
            method='POST',
            data={'query': '{ markets(first: 1) { id } }'},
            timeout=5
        )
    
    def check_kalshi(self) -> Dict[str, Any]:
        """
        Check Kalshi API health.
        
        Returns:
            Health status dict
        """
        return self._check_api(
            'kalshi',
            'https://trading-api.kalshi.com/trade-api/v2/status',
            timeout=5
        )
    
    def check_database(self) -> Dict[str, Any]:
        """
        Check database connectivity.
        
        Returns:
            Health status dict
        """
        try:
            start_time = time.time()
            
            # Try to connect to settings database
            db_file = Path(__file__).parent.parent / 'data' / 'settings.db'
            
            if not db_file.exists():
                return {
                    'status': 'down',
                    'message': 'Database file does not exist',
                    'response_time_ms': 0,
                    'last_checked': datetime.utcnow().isoformat()
                }
            
            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            cursor.fetchone()
            conn.close()
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                'status': 'healthy',
                'message': 'Database connection successful',
                'response_time_ms': round(response_time, 2),
                'last_checked': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'down',
                'message': f'Database error: {str(e)}',
                'response_time_ms': 0,
                'last_checked': datetime.utcnow().isoformat()
            }
    
    def _check_api(
        self,
        service_name: str,
        url: str,
        method: str = 'GET',
        data: Optional[Dict] = None,
        timeout: int = 5
    ) -> Dict[str, Any]:
        """
        Check API endpoint health.
        
        Args:
            service_name: Name of service
            url: API endpoint URL
            method: HTTP method
            data: Request data for POST
            timeout: Request timeout in seconds
            
        Returns:
            Health status dict
        """
        try:
            start_time = time.time()
            
            if method == 'POST':
                response = requests.post(url, json=data, timeout=timeout)
            else:
                response = requests.get(url, timeout=timeout)
            
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code >= 200 and response.status_code < 300:
                status = 'healthy'
                message = 'API is responding'
            elif response.status_code >= 500:
                status = 'down'
                message = f'Server error: {response.status_code}'
            else:
                status = 'degraded'
                message = f'Unexpected status: {response.status_code}'
            
            return {
                'status': status,
                'message': message,
                'status_code': response.status_code,
                'response_time_ms': round(response_time, 2),
                'last_checked': datetime.utcnow().isoformat()
            }
            
        except requests.Timeout:
            return {
                'status': 'down',
                'message': 'Request timeout',
                'response_time_ms': timeout * 1000,
                'last_checked': datetime.utcnow().isoformat()
            }
        except requests.ConnectionError:
            return {
                'status': 'down',
                'message': 'Connection failed',
                'response_time_ms': 0,
                'last_checked': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'down',
                'message': f'Error: {str(e)}',
                'response_time_ms': 0,
                'last_checked': datetime.utcnow().isoformat()
            }


# Global instance
health_service = HealthCheckService()
