"""
Sentry Integration for Error Tracking and Performance Monitoring
"""

import os
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from typing import Optional, Dict, Any
import logging


class SentryIntegration:
    """Sentry error tracking integration"""
    
    def __init__(self):
        self.enabled = False
        self.dsn = os.getenv('SENTRY_DSN', '')
        self.environment = os.getenv('SENTRY_ENVIRONMENT', 'production')
        self.traces_sample_rate = float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0.1'))
        
        if self.dsn:
            self._initialize_sentry()
    
    def _initialize_sentry(self):
        """Initialize Sentry SDK"""
        try:
            sentry_sdk.init(
                dsn=self.dsn,
                integrations=[
                    FlaskIntegration(),
                    LoggingIntegration(
                        level=logging.INFO,
                        event_level=logging.ERROR
                    ),
                ],
                environment=self.environment,
                traces_sample_rate=self.traces_sample_rate,
                send_default_pii=False,  # Don't send PII
                before_send=self._before_send,
                before_breadcrumb=self._before_breadcrumb,
            )
            self.enabled = True
            logging.info(f"Sentry initialized for environment: {self.environment}")
        except Exception as e:
            logging.error(f"Failed to initialize Sentry: {e}")
            self.enabled = False
    
    def _before_send(self, event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Filter/modify events before sending to Sentry"""
        # Remove sensitive data
        if 'request' in event:
            if 'headers' in event['request']:
                # Remove authorization headers
                headers = event['request']['headers']
                headers.pop('Authorization', None)
                headers.pop('X-API-Key', None)
        
        # Don't send test errors
        if 'exception' in event:
            for exception in event['exception'].get('values', []):
                if 'test' in exception.get('type', '').lower():
                    return None
        
        return event
    
    def _before_breadcrumb(self, crumb: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Filter/modify breadcrumbs before adding"""
        # Remove sensitive query parameters
        if crumb.get('category') == 'httplib':
            if 'data' in crumb:
                data = crumb['data']
                if 'url' in data:
                    # Remove API keys from URL
                    data['url'] = data['url'].split('?')[0]
        
        return crumb
    
    def capture_exception(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Capture exception with optional context"""
        if not self.enabled:
            return
        
        try:
            with sentry_sdk.push_scope() as scope:
                if context:
                    for key, value in context.items():
                        scope.set_context(key, value)
                
                sentry_sdk.capture_exception(error)
        except Exception as e:
            logging.error(f"Failed to send exception to Sentry: {e}")
    
    def capture_message(self, message: str, level: str = 'info', context: Optional[Dict[str, Any]] = None):
        """Capture message with optional context"""
        if not self.enabled:
            return
        
        try:
            with sentry_sdk.push_scope() as scope:
                if context:
                    for key, value in context.items():
                        scope.set_context(key, value)
                
                sentry_sdk.capture_message(message, level=level)
        except Exception as e:
            logging.error(f"Failed to send message to Sentry: {e}")
    
    def set_user(self, user_id: Optional[str] = None, email: Optional[str] = None, 
                 username: Optional[str] = None):
        """Set user context"""
        if not self.enabled:
            return
        
        sentry_sdk.set_user({
            "id": user_id,
            "email": email,
            "username": username
        })
    
    def set_tag(self, key: str, value: str):
        """Set tag for grouping"""
        if not self.enabled:
            return
        
        sentry_sdk.set_tag(key, value)
    
    def add_breadcrumb(self, message: str, category: str = 'default', 
                       level: str = 'info', data: Optional[Dict[str, Any]] = None):
        """Add breadcrumb for tracking user actions"""
        if not self.enabled:
            return
        
        sentry_sdk.add_breadcrumb(
            message=message,
            category=category,
            level=level,
            data=data or {}
        )
    
    def start_transaction(self, name: str, op: str = 'task') -> Optional[Any]:
        """Start performance transaction"""
        if not self.enabled:
            return None
        
        return sentry_sdk.start_transaction(name=name, op=op)
    
    def capture_trading_error(self, error: Exception, strategy: str, market: str):
        """Capture trading-specific error"""
        self.capture_exception(error, {
            'trading': {
                'strategy': strategy,
                'market': market
            }
        })
    
    def capture_api_error(self, error: Exception, service: str, endpoint: str):
        """Capture API-specific error"""
        self.capture_exception(error, {
            'api': {
                'service': service,
                'endpoint': endpoint
            }
        })


# Global instance
sentry = SentryIntegration()
