"""
Binance API Client - Free, unlimited crypto price data

Provides:
- Real-time crypto prices via REST API
- WebSocket streaming for live updates
- No API key required for public endpoints
- 1200 requests/minute rate limit
"""

import requests
import json
import time
import threading
from typing import Dict, Optional, List, Callable
from datetime import datetime


class BinanceClient:
    """
    Free Binance API client for crypto prices

    Features:
    - REST API for spot prices
    - WebSocket for real-time streaming
    - No authentication required
    - Automatic reconnection
    """

    BASE_URL = "https://api.binance.com"
    WS_URL = "wss://stream.binance.com:9443/ws"

    def __init__(self, logger=None):
        """
        Initialize Binance client

        Args:
            logger: Optional logger instance
        """
        self.logger = logger
        self.session = requests.Session()
        self.ws_connection = None
        self.ws_thread = None
        self.ws_running = False

    def get_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for a trading pair

        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT', 'ETHUSDT')

        Returns:
            Current price as float, or None on error

        Example:
            >>> client = BinanceClient()
            >>> price = client.get_price('BTCUSDT')
            >>> print(f"BTC Price: ${price:,.2f}")
        """
        try:
            url = f"{self.BASE_URL}/api/v3/ticker/price"
            params = {"symbol": symbol.upper()}

            response = self.session.get(url, params=params, timeout=5)

            if response.status_code == 200:
                data = response.json()
                price = float(data["price"])

                if self.logger:
                    self.logger.log_info(f"Binance: {symbol} = ${price:,.2f}")

                return price
            else:
                if self.logger:
                    self.logger.log_error(
                        f"Binance API error: HTTP {response.status_code}"
                    )
                return None

        except requests.exceptions.RequestException as e:
            if self.logger:
                self.logger.log_error(f"Binance connection error: {str(e)}")
            return None
        except (KeyError, ValueError) as e:
            if self.logger:
                self.logger.log_error(f"Binance response parsing error: {str(e)}")
            return None

    def get_multiple_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        Get prices for multiple trading pairs in one request

        Args:
            symbols: List of trading pair symbols

        Returns:
            Dictionary mapping symbols to prices

        Example:
            >>> client = BinanceClient()
            >>> prices = client.get_multiple_prices(['BTCUSDT', 'ETHUSDT'])
            >>> print(f"BTC: ${prices['BTCUSDT']:,.2f}")
            >>> print(f"ETH: ${prices['ETHUSDT']:,.2f}")
        """
        try:
            url = f"{self.BASE_URL}/api/v3/ticker/price"

            response = self.session.get(url, timeout=5)

            if response.status_code == 200:
                all_prices = response.json()

                # Filter to requested symbols
                result = {}
                for item in all_prices:
                    symbol = item["symbol"]
                    if symbol.upper() in [s.upper() for s in symbols]:
                        result[symbol] = float(item["price"])

                if self.logger:
                    self.logger.log_info(f"Binance: Fetched {len(result)} prices")

                return result
            else:
                if self.logger:
                    self.logger.log_error(
                        f"Binance API error: HTTP {response.status_code}"
                    )
                return {}

        except requests.exceptions.RequestException as e:
            if self.logger:
                self.logger.log_error(f"Binance connection error: {str(e)}")
            return {}
        except (KeyError, ValueError) as e:
            if self.logger:
                self.logger.log_error(f"Binance response parsing error: {str(e)}")
            return {}

    def get_24h_stats(self, symbol: str) -> Optional[Dict]:
        """
        Get 24-hour statistics for a trading pair

        Args:
            symbol: Trading pair symbol

        Returns:
            Dictionary with price, volume, and change data
        """
        try:
            url = f"{self.BASE_URL}/api/v3/ticker/24hr"
            params = {"symbol": symbol.upper()}

            response = self.session.get(url, params=params, timeout=5)

            if response.status_code == 200:
                data = response.json()

                return {
                    "symbol": data["symbol"],
                    "price": float(data["lastPrice"]),
                    "price_change": float(data["priceChange"]),
                    "price_change_percent": float(data["priceChangePercent"]),
                    "volume": float(data["volume"]),
                    "quote_volume": float(data["quoteVolume"]),
                    "high": float(data["highPrice"]),
                    "low": float(data["lowPrice"]),
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                if self.logger:
                    self.logger.log_error(
                        f"Binance API error: HTTP {response.status_code}"
                    )
                return None

        except Exception as e:
            if self.logger:
                self.logger.log_error(f"Binance stats error: {str(e)}")
            return None

    def stream_prices(
        self,
        symbols: List[str],
        callback: Callable[[Dict], None],
        reconnect: bool = True,
    ) -> bool:
        """
        Stream real-time prices via WebSocket

        Args:
            symbols: List of trading pairs to stream
            callback: Function to call with price updates
            reconnect: Whether to automatically reconnect on disconnect

        Returns:
            True if stream started successfully

        Example:
            >>> def on_price(data):
            ...     print(f"{data['symbol']}: ${data['price']:,.2f}")
            >>>
            >>> client = BinanceClient()
            >>> client.stream_prices(['BTCUSDT'], on_price)
        """
        try:
            import websocket
        except ImportError:
            if self.logger:
                self.logger.log_error(
                    "websocket-client not installed. Run: pip install websocket-client"
                )
            return False

        # Stop existing stream if running
        if self.ws_running:
            self.stop_stream()

        # Build stream URL
        streams = [f"{symbol.lower()}@ticker" for symbol in symbols]
        stream_url = f"{self.WS_URL}/{'/'.join(streams)}"

        def on_message(ws, message):
            try:
                data = json.loads(message)

                # Parse ticker data
                if "c" in data:  # Current price
                    price_data = {
                        "symbol": data["s"],
                        "price": float(data["c"]),
                        "timestamp": datetime.fromtimestamp(
                            data["E"] / 1000
                        ).isoformat(),
                    }
                    callback(price_data)

            except Exception as e:
                if self.logger:
                    self.logger.log_error(f"WebSocket message error: {str(e)}")

        def on_error(ws, error):
            if self.logger:
                self.logger.log_error(f"WebSocket error: {str(error)}")

        def on_close(ws, close_status_code, close_msg):
            if self.logger:
                self.logger.log_warning("WebSocket connection closed")

            # Reconnect if enabled
            if reconnect and self.ws_running:
                if self.logger:
                    self.logger.log_info("Reconnecting WebSocket in 5 seconds...")
                time.sleep(5)
                if self.ws_running:  # Check if still running
                    self.stream_prices(symbols, callback, reconnect)

        def on_open(ws):
            if self.logger:
                self.logger.log_info(
                    f"WebSocket connected - streaming {len(symbols)} symbols"
                )

        # Create WebSocket connection
        self.ws_connection = websocket.WebSocketApp(
            stream_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open,
        )

        # Run in background thread
        self.ws_running = True
        self.ws_thread = threading.Thread(
            target=self.ws_connection.run_forever, daemon=True
        )
        self.ws_thread.start()

        return True

    def stop_stream(self) -> None:
        """Stop WebSocket price stream"""
        self.ws_running = False

        if self.ws_connection:
            self.ws_connection.close()
            self.ws_connection = None

        if self.ws_thread:
            self.ws_thread.join(timeout=2)
            self.ws_thread = None

        if self.logger:
            self.logger.log_info("WebSocket stream stopped")

    def health_check(self) -> bool:
        """
        Check if Binance API is accessible

        Returns:
            True if API is healthy
        """
        try:
            url = f"{self.BASE_URL}/api/v3/ping"
            response = self.session.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False

    def get_server_time(self) -> Optional[int]:
        """
        Get Binance server time

        Returns:
            Server timestamp in milliseconds
        """
        try:
            url = f"{self.BASE_URL}/api/v3/time"
            response = self.session.get(url, timeout=5)

            if response.status_code == 200:
                return response.json()["serverTime"]
            return None
        except:
            return None
