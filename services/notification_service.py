"""
Notification Service

Central service for routing notifications to configured channels.
Supports Discord, Slack, Email, Telegram, and Webhook notifications.
"""

import logging
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
from urllib.parse import urlparse

from database.settings_models import UserSettings, NotificationChannel, NotificationPreference
from services.notification_types import NotificationType, NotificationCategory


logger = logging.getLogger(__name__)


def validate_webhook_url(url: str) -> bool:
    """
    Validate webhook URL to prevent SSRF attacks.
    
    SECURITY NOTE: This function mitigates SSRF (Server-Side Request Forgery)
    risks by validating user-provided webhook URLs. It enforces:
    - HTTPS-only connections
    - Blocks localhost and private IP ranges (RFC 1918)
    - Validates URL format and hostname
    
    While CodeQL may still report SSRF warnings for requests.post() calls
    using these URLs, the risk is mitigated through this validation.
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL is valid and safe
    """
    try:
        parsed = urlparse(url)
        
        # Must use HTTPS
        if parsed.scheme != 'https':
            logger.warning(f"Webhook URL must use HTTPS: {url}")
            return False
        
        # Must have a valid hostname
        if not parsed.netloc:
            logger.warning(f"Invalid webhook URL (no hostname): {url}")
            return False
        
        # Block private IP ranges and localhost
        hostname = parsed.hostname or parsed.netloc
        if hostname:
            hostname_lower = hostname.lower()
            # Block localhost and private IPs
            blocked_hosts = [
                'localhost', '127.0.0.1', '::1',
                '169.254.', '10.', '172.16.', '172.17.', '172.18.',
                '172.19.', '172.20.', '172.21.', '172.22.', '172.23.',
                '172.24.', '172.25.', '172.26.', '172.27.', '172.28.',
                '172.29.', '172.30.', '172.31.', '192.168.'
            ]
            
            for blocked in blocked_hosts:
                if hostname_lower.startswith(blocked):
                    logger.warning(f"Webhook URL uses blocked hostname: {url}")
                    return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating webhook URL: {e}")
        return False


class NotificationService:
    """
    Central notification service.
    
    Routes notifications to all configured and enabled channels.
    """
    
    # Color codes for Discord embeds
    CATEGORY_COLORS = {
        NotificationCategory.OPPORTUNITIES: 0x00FF00,  # Green
        NotificationCategory.TRADES: 0x0099FF,         # Blue
        NotificationCategory.PRICE_ALERTS: 0xFFAA00,   # Orange
        NotificationCategory.SYSTEM: 0x888888,         # Gray
        NotificationCategory.RISK: 0xFF0000,           # Red
        NotificationCategory.PERFORMANCE: 0x9900FF,    # Purple
    }
    
    def __init__(self):
        """Initialize notification service."""
        self.logger = logging.getLogger(__name__)
    
    def send_notification(
        self,
        notification_type: str,
        data: Dict[str, Any],
        user_id: int = 1
    ) -> bool:
        """
        Send a notification to all enabled channels.
        
        Args:
            notification_type: Type of notification (from NotificationType)
            data: Notification data
            user_id: User ID
            
        Returns:
            True if sent to at least one channel successfully
        """
        try:
            # Check if notifications are globally enabled
            settings = UserSettings.get(user_id)
            if not settings.get('notifications_enabled'):
                self.logger.debug(f"Notifications disabled for user {user_id}")
                return False
            
            # Get preferences for this notification type
            preferences = NotificationPreference.get_for_type(notification_type, user_id)
            
            if not preferences:
                # No specific preferences, send to all enabled channels
                channels = NotificationChannel.get_all(user_id)
                channels = [c for c in channels if c.get('enabled')]
            else:
                # Use channels from preferences
                channel_ids = [p['channel_id'] for p in preferences if p.get('enabled') and p.get('channel_id')]
                channels = [NotificationChannel.get(cid) for cid in channel_ids]
                channels = [c for c in channels if c and c.get('enabled')]
                
                # Apply filters
                channels = [c for c in channels if self._passes_filters(data, preferences, c)]
            
            if not channels:
                self.logger.debug(f"No enabled channels for {notification_type}")
                return False
            
            # Send to each channel
            success_count = 0
            for channel in channels:
                try:
                    if self._send_to_channel(channel, notification_type, data):
                        success_count += 1
                except Exception as e:
                    self.logger.error(f"Error sending to channel {channel['id']}: {e}")
            
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"Error in send_notification: {e}")
            return False
    
    def _passes_filters(
        self,
        data: Dict[str, Any],
        preferences: List[Dict[str, Any]],
        channel: Dict[str, Any]
    ) -> bool:
        """
        Check if notification data passes preference filters.
        
        Args:
            data: Notification data
            preferences: List of preferences
            channel: Channel config
            
        Returns:
            True if passes all filters
        """
        # Find preference for this channel
        pref = next((p for p in preferences if p.get('channel_id') == channel['id']), None)
        if not pref:
            return True  # No specific filters
        
        # Check profit threshold
        min_profit = pref.get('min_profit_threshold')
        if min_profit is not None:
            profit = data.get('profit', 0)
            if profit < min_profit:
                return False
        
        # Check confidence level
        min_confidence = pref.get('min_confidence')
        if min_confidence:
            confidence = data.get('confidence', '')
            confidence_order = ['low', 'medium', 'high', 'very_high']
            if confidence not in confidence_order or min_confidence not in confidence_order:
                return False
            data_conf_idx = confidence_order.index(confidence)
            min_conf_idx = confidence_order.index(min_confidence)
            if data_conf_idx < min_conf_idx:
                return False
        
        # Check strategies
        strategies = pref.get('strategies')
        if strategies:
            strategy_list = [s.strip() for s in strategies.split(',')]
            data_strategy = data.get('strategy', '')
            if data_strategy and data_strategy not in strategy_list:
                return False
        
        return True
    
    def _send_to_channel(
        self,
        channel: Dict[str, Any],
        notification_type: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        Send notification to a specific channel.
        
        Args:
            channel: Channel configuration
            notification_type: Type of notification
            data: Notification data
            
        Returns:
            True if successful
        """
        channel_type = channel['channel_type']
        
        if channel_type == 'discord':
            return self._send_discord(channel, notification_type, data)
        elif channel_type == 'slack':
            return self._send_slack(channel, notification_type, data)
        elif channel_type == 'email':
            return self._send_email(channel, notification_type, data)
        elif channel_type == 'telegram':
            return self._send_telegram(channel, notification_type, data)
        elif channel_type == 'webhook':
            return self._send_webhook(channel, notification_type, data)
        else:
            self.logger.warning(f"Unknown channel type: {channel_type}")
            return False
    
    def _send_discord(
        self,
        channel: Dict[str, Any],
        notification_type: str,
        data: Dict[str, Any]
    ) -> bool:
        """Send notification to Discord via webhook."""
        webhook_url = channel.get('webhook_url')
        if not webhook_url:
            self.logger.warning("Discord webhook URL not configured")
            return False
        
        # Validate URL for security
        if not validate_webhook_url(webhook_url):
            self.logger.error("Discord webhook URL failed security validation")
            return False
        
        try:
            # Get category for color
            category = NotificationType.get_category(notification_type)
            color = self.CATEGORY_COLORS.get(category, 0x0099FF)
            
            # Build embed
            embed = {
                'title': NotificationType.get_display_name(notification_type),
                'color': color,
                'timestamp': datetime.utcnow().isoformat(),
                'fields': []
            }
            
            # Add fields from data
            if 'market' in data:
                embed['fields'].append({'name': 'Market', 'value': data['market'], 'inline': False})
            if 'profit' in data:
                embed['fields'].append({'name': 'Profit', 'value': f"${data['profit']:.2f}", 'inline': True})
            if 'confidence' in data:
                embed['fields'].append({'name': 'Confidence', 'value': data['confidence'].replace('_', ' ').title(), 'inline': True})
            if 'strategy' in data:
                embed['fields'].append({'name': 'Strategy', 'value': data['strategy'], 'inline': True})
            if 'arbitrage_type' in data:
                embed['fields'].append({'name': 'Type', 'value': data['arbitrage_type'], 'inline': True})
            if 'reason' in data:
                embed['fields'].append({'name': 'Reason', 'value': data['reason'], 'inline': False})
            if 'message' in data:
                embed['description'] = data['message']
            
            payload = {
                'embeds': [embed]
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            self.logger.debug(f"Discord notification sent: {notification_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Discord notification failed: {e}")
            return False
    
    def _send_slack(
        self,
        channel: Dict[str, Any],
        notification_type: str,
        data: Dict[str, Any]
    ) -> bool:
        """Send notification to Slack via webhook."""
        webhook_url = channel.get('webhook_url')
        if not webhook_url:
            self.logger.warning("Slack webhook URL not configured")
            return False
        
        # Validate URL for security
        if not validate_webhook_url(webhook_url):
            self.logger.error("Slack webhook URL failed security validation")
            return False
        
        try:
            # Build message
            title = NotificationType.get_display_name(notification_type)
            
            blocks = [
                {
                    'type': 'header',
                    'text': {
                        'type': 'plain_text',
                        'text': title
                    }
                }
            ]
            
            # Add fields
            fields = []
            if 'market' in data:
                fields.append({'type': 'mrkdwn', 'text': f"*Market:*\n{data['market']}"})
            if 'profit' in data:
                fields.append({'type': 'mrkdwn', 'text': f"*Profit:*\n${data['profit']:.2f}"})
            if 'confidence' in data:
                fields.append({'type': 'mrkdwn', 'text': f"*Confidence:*\n{data['confidence'].replace('_', ' ').title()}"})
            if 'strategy' in data:
                fields.append({'type': 'mrkdwn', 'text': f"*Strategy:*\n{data['strategy']}"})
            
            if fields:
                blocks.append({
                    'type': 'section',
                    'fields': fields
                })
            
            if 'message' in data:
                blocks.append({
                    'type': 'section',
                    'text': {
                        'type': 'mrkdwn',
                        'text': data['message']
                    }
                })
            
            payload = {'blocks': blocks}
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            self.logger.debug(f"Slack notification sent: {notification_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Slack notification failed: {e}")
            return False
    
    def _send_email(
        self,
        channel: Dict[str, Any],
        notification_type: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        Send notification via email with HTML formatting.
        
        Requires email configuration in channel config:
        - smtp_server: SMTP server address
        - smtp_port: SMTP port (usually 587 for TLS)
        - smtp_username: SMTP username
        - smtp_password: SMTP password/app password
        - from_email: Sender email address
        - to_email: Recipient email address
        """
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        try:
            # Get email config
            config = channel.get('config', {})
            smtp_server = config.get('smtp_server')
            smtp_port = config.get('smtp_port', 587)
            smtp_username = config.get('smtp_username')
            smtp_password = config.get('smtp_password')
            from_email = config.get('from_email', smtp_username)
            to_email = channel.get('email_address') or config.get('to_email')
            
            if not all([smtp_server, smtp_username, smtp_password, to_email]):
                self.logger.warning("Email configuration incomplete")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = NotificationType.get_display_name(notification_type)
            msg['From'] = from_email
            msg['To'] = to_email
            
            # Generate HTML body
            html_body = self._format_email_html(notification_type, data)
            
            # Attach HTML
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            self.logger.debug(f"Email notification sent: {notification_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Email notification failed: {e}")
            return False
    
    def _format_email_html(self, notification_type: str, data: Dict[str, Any]) -> str:
        """
        Format notification data as beautiful HTML email.
        
        Args:
            notification_type: Type of notification
            data: Notification data
            
        Returns:
            HTML string
        """
        title = NotificationType.get_display_name(notification_type)
        category = NotificationType.get_category(notification_type)
        
        # Choose color based on category
        colors = {
            NotificationCategory.OPPORTUNITIES: '#00FF00',
            NotificationCategory.TRADES: '#0099FF',
            NotificationCategory.PRICE_ALERTS: '#FFAA00',
            NotificationCategory.SYSTEM: '#888888',
            NotificationCategory.RISK: '#FF0000',
            NotificationCategory.PERFORMANCE: '#9900FF',
        }
        color = colors.get(category, '#0099FF')
        
        # Build field rows
        rows = []
        if 'market' in data:
            rows.append(f"<tr><td><strong>Market:</strong></td><td>{data['market']}</td></tr>")
        if 'profit' in data:
            rows.append(f"<tr><td><strong>Profit:</strong></td><td>${data['profit']:.2f}</td></tr>")
        if 'confidence' in data:
            conf = data['confidence'].replace('_', ' ').title()
            rows.append(f"<tr><td><strong>Confidence:</strong></td><td>{conf}</td></tr>")
        if 'strategy' in data:
            rows.append(f"<tr><td><strong>Strategy:</strong></td><td>{data['strategy']}</td></tr>")
        if 'arbitrage_type' in data:
            rows.append(f"<tr><td><strong>Type:</strong></td><td>{data['arbitrage_type']}</td></tr>")
        
        message = data.get('message', '')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 20px auto; padding: 20px; background: #f9f9f9; border-radius: 8px; }}
                .header {{ background: {color}; color: white; padding: 15px; border-radius: 8px 8px 0 0; }}
                .content {{ background: white; padding: 20px; border-radius: 0 0 8px 8px; }}
                table {{ width: 100%; margin: 15px 0; }}
                td {{ padding: 8px; }}
                .message {{ background: #f0f0f0; padding: 15px; border-left: 4px solid {color}; margin: 15px 0; }}
                .footer {{ text-align: center; color: #999; margin-top: 20px; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2 style="margin: 0;">{title}</h2>
                </div>
                <div class="content">
                    <table>
                        {''.join(rows)}
                    </table>
                    {f'<div class="message">{message}</div>' if message else ''}
                </div>
                <div class="footer">
                    Market Strategy Testing Bot • {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    def _send_telegram(
        self,
        channel: Dict[str, Any],
        notification_type: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        Send notification to Telegram using Bot API.
        
        Requires configuration:
        - bot_token: Telegram Bot API token
        - chat_id: Chat ID to send messages to
        """
        try:
            # Get Telegram config
            config = channel.get('config', {})
            bot_token = config.get('bot_token')
            chat_id = config.get('chat_id')
            
            if not bot_token or not chat_id:
                self.logger.warning("Telegram configuration incomplete")
                return False
            
            # Format message with Markdown
            message_text = self._format_telegram_text(notification_type, data)
            
            # Send via Telegram Bot API
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': message_text,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            self.logger.debug(f"Telegram notification sent: {notification_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Telegram notification failed: {e}")
            return False
    
    def _format_telegram_text(self, notification_type: str, data: Dict[str, Any]) -> str:
        """
        Format notification data as Telegram Markdown message.
        
        Args:
            notification_type: Type of notification
            data: Notification data
            
        Returns:
            Markdown formatted string
        """
        title = NotificationType.get_display_name(notification_type)
        
        lines = [f"*{title}*", ""]
        
        if 'market' in data:
            lines.append(f"📊 *Market:* {data['market']}")
        if 'profit' in data:
            lines.append(f"💰 *Profit:* ${data['profit']:.2f}")
        if 'confidence' in data:
            conf = data['confidence'].replace('_', ' ').title()
            lines.append(f"🎯 *Confidence:* {conf}")
        if 'strategy' in data:
            lines.append(f"⚡ *Strategy:* {data['strategy']}")
        if 'arbitrage_type' in data:
            lines.append(f"🔄 *Type:* {data['arbitrage_type']}")
        
        if 'message' in data:
            lines.append("")
            lines.append(data['message'])
        
        lines.append("")
        lines.append(f"_📅 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC_")
        
        return "\n".join(lines)
    
    def _send_webhook(
        self,
        channel: Dict[str, Any],
        notification_type: str,
        data: Dict[str, Any]
    ) -> bool:
        """Send notification to generic webhook."""
        webhook_url = channel.get('webhook_url')
        if not webhook_url:
            self.logger.warning("Webhook URL not configured")
            return False
        
        # Validate URL for security
        if not validate_webhook_url(webhook_url):
            self.logger.error("Webhook URL failed security validation")
            return False
        
        try:
            payload = {
                'notification_type': notification_type,
                'timestamp': datetime.utcnow().isoformat(),
                'data': data
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            self.logger.debug(f"Webhook notification sent: {notification_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Webhook notification failed: {e}")
            return False
    
    def test_channel(self, channel_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test a notification channel.
        
        Args:
            channel_type: Type of channel
            config: Channel configuration
            
        Returns:
            Dictionary with success status and message
        """
        test_data = {
            'message': 'This is a test notification from Market Strategy Testing Bot',
            'market': 'Test Market',
            'profit': 100.00,
            'confidence': 'high',
            'strategy': 'Test Strategy'
        }
        
        channel = {
            'channel_type': channel_type,
            **config
        }
        
        try:
            success = self._send_to_channel(channel, NotificationType.SYSTEM_HEALTH_CHECK, test_data)
            
            if success:
                return {
                    'success': True,
                    'message': f'Test notification sent successfully to {channel_type}'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to send test notification'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


# Global instance
notification_service = NotificationService()
