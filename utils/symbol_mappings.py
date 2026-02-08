"""
Symbol Mappings for Crypto APIs

Centralized symbol mapping for all crypto price APIs.
Converts standard symbols (BTC, ETH, etc.) to API-specific formats.
"""

from typing import Dict, List, Optional


class SymbolMapper:
    """Maps standard crypto symbols to API-specific formats"""
    
    # CoinGecko uses coin IDs
    COINGECKO_MAP = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'SOL': 'solana',
        'XRP': 'ripple',
        'ADA': 'cardano',
        'DOT': 'polkadot',
        'AVAX': 'avalanche-2',
        'MATIC': 'matic-network',
        'LINK': 'chainlink',
        'UNI': 'uniswap',
        'ATOM': 'cosmos',
        'LTC': 'litecoin',
        'BCH': 'bitcoin-cash',
        'XLM': 'stellar',
        'ALGO': 'algorand',
        'VET': 'vechain',
        'ICP': 'internet-computer',
        'FIL': 'filecoin',
        'TRX': 'tron',
        'ETC': 'ethereum-classic'
    }
    
    # Binance uses trading pairs with USDT
    BINANCE_MAP = {
        'BTC': 'BTCUSDT',
        'ETH': 'ETHUSDT',
        'SOL': 'SOLUSDT',
        'XRP': 'XRPUSDT',
        'ADA': 'ADAUSDT',
        'DOT': 'DOTUSDT',
        'AVAX': 'AVAXUSDT',
        'MATIC': 'MATICUSDT',
        'LINK': 'LINKUSDT',
        'UNI': 'UNIUSDT',
        'ATOM': 'ATOMUSDT',
        'LTC': 'LTCUSDT',
        'BCH': 'BCHUSDT',
        'XLM': 'XLMUSDT',
        'ALGO': 'ALGOUSDT',
        'VET': 'VETUSDT',
        'ICP': 'ICPUSDT',
        'FIL': 'FILUSDT',
        'TRX': 'TRXUSDT',
        'ETC': 'ETCUSDT'
    }
    
    # Coinbase uses trading pairs with USD
    COINBASE_MAP = {
        'BTC': 'BTC-USD',
        'ETH': 'ETH-USD',
        'SOL': 'SOL-USD',
        'XRP': 'XRP-USD',
        'ADA': 'ADA-USD',
        'DOT': 'DOT-USD',
        'AVAX': 'AVAX-USD',
        'MATIC': 'MATIC-USD',
        'LINK': 'LINK-USD',
        'UNI': 'UNI-USD',
        'ATOM': 'ATOM-USD',
        'LTC': 'LTC-USD',
        'BCH': 'BCH-USD',
        'XLM': 'XLM-USD',
        'ALGO': 'ALGO-USD',
        'VET': 'VET-USD',
        'ICP': 'ICP-USD',
        'FIL': 'FIL-USD',
        'TRX': 'TRX-USD',
        'ETC': 'ETC-USD'
    }
    
    # Full names for display
    FULL_NAMES = {
        'BTC': 'Bitcoin',
        'ETH': 'Ethereum',
        'SOL': 'Solana',
        'XRP': 'Ripple',
        'ADA': 'Cardano',
        'DOT': 'Polkadot',
        'AVAX': 'Avalanche',
        'MATIC': 'Polygon',
        'LINK': 'Chainlink',
        'UNI': 'Uniswap',
        'ATOM': 'Cosmos',
        'LTC': 'Litecoin',
        'BCH': 'Bitcoin Cash',
        'XLM': 'Stellar',
        'ALGO': 'Algorand',
        'VET': 'VeChain',
        'ICP': 'Internet Computer',
        'FIL': 'Filecoin',
        'TRX': 'TRON',
        'ETC': 'Ethereum Classic'
    }
    
    # Reverse mappings (cached)
    _COINGECKO_REVERSE = None
    _BINANCE_REVERSE = None
    _COINBASE_REVERSE = None
    
    @classmethod
    def to_coingecko(cls, symbol: str) -> str:
        """
        Convert standard symbol to CoinGecko coin ID.
        
        Args:
            symbol: Standard crypto symbol (e.g., 'BTC')
            
        Returns:
            CoinGecko coin ID (e.g., 'bitcoin')
            
        Raises:
            ValueError: If symbol is not supported
        """
        symbol = symbol.upper()
        if symbol not in cls.COINGECKO_MAP:
            raise ValueError(f"Symbol '{symbol}' not supported for CoinGecko")
        return cls.COINGECKO_MAP[symbol]
    
    @classmethod
    def to_binance(cls, symbol: str) -> str:
        """
        Convert standard symbol to Binance trading pair.
        
        Args:
            symbol: Standard crypto symbol (e.g., 'BTC')
            
        Returns:
            Binance trading pair (e.g., 'BTCUSDT')
            
        Raises:
            ValueError: If symbol is not supported
        """
        symbol = symbol.upper()
        if symbol not in cls.BINANCE_MAP:
            raise ValueError(f"Symbol '{symbol}' not supported for Binance")
        return cls.BINANCE_MAP[symbol]
    
    @classmethod
    def to_coinbase(cls, symbol: str) -> str:
        """
        Convert standard symbol to Coinbase trading pair.
        
        Args:
            symbol: Standard crypto symbol (e.g., 'BTC')
            
        Returns:
            Coinbase trading pair (e.g., 'BTC-USD')
            
        Raises:
            ValueError: If symbol is not supported
        """
        symbol = symbol.upper()
        if symbol not in cls.COINBASE_MAP:
            raise ValueError(f"Symbol '{symbol}' not supported for Coinbase")
        return cls.COINBASE_MAP[symbol]
    
    @classmethod
    def from_coingecko(cls, coin_id: str) -> Optional[str]:
        """
        Convert CoinGecko coin ID to standard symbol.
        
        Args:
            coin_id: CoinGecko coin ID (e.g., 'bitcoin')
            
        Returns:
            Standard symbol (e.g., 'BTC') or None if not found
        """
        if cls._COINGECKO_REVERSE is None:
            cls._COINGECKO_REVERSE = {v: k for k, v in cls.COINGECKO_MAP.items()}
        return cls._COINGECKO_REVERSE.get(coin_id)
    
    @classmethod
    def from_binance(cls, pair: str) -> Optional[str]:
        """
        Convert Binance trading pair to standard symbol.
        
        Args:
            pair: Binance trading pair (e.g., 'BTCUSDT')
            
        Returns:
            Standard symbol (e.g., 'BTC') or None if not found
        """
        if cls._BINANCE_REVERSE is None:
            cls._BINANCE_REVERSE = {v: k for k, v in cls.BINANCE_MAP.items()}
        return cls._BINANCE_REVERSE.get(pair)
    
    @classmethod
    def from_coinbase(cls, pair: str) -> Optional[str]:
        """
        Convert Coinbase trading pair to standard symbol.
        
        Args:
            pair: Coinbase trading pair (e.g., 'BTC-USD')
            
        Returns:
            Standard symbol (e.g., 'BTC') or None if not found
        """
        if cls._COINBASE_REVERSE is None:
            cls._COINBASE_REVERSE = {v: k for k, v in cls.COINBASE_MAP.items()}
        return cls._COINBASE_REVERSE.get(pair)
    
    @classmethod
    def get_full_name(cls, symbol: str) -> str:
        """
        Get full name for display.
        
        Args:
            symbol: Standard crypto symbol (e.g., 'BTC')
            
        Returns:
            Full name (e.g., 'Bitcoin')
            
        Raises:
            ValueError: If symbol is not supported
        """
        symbol = symbol.upper()
        if symbol not in cls.FULL_NAMES:
            raise ValueError(f"Symbol '{symbol}' not supported")
        return cls.FULL_NAMES[symbol]
    
    @classmethod
    def get_all_symbols(cls) -> List[str]:
        """
        Get list of all supported symbols.
        
        Returns:
            List of supported crypto symbols
        """
        return sorted(cls.FULL_NAMES.keys())
    
    @classmethod
    def is_supported(cls, symbol: str) -> bool:
        """
        Check if symbol is supported.
        
        Args:
            symbol: Crypto symbol to check
            
        Returns:
            True if supported, False otherwise
        """
        return symbol.upper() in cls.FULL_NAMES
