"""
Market Name Parser

Parse crypto information from prediction market names.
Extracts symbol, price threshold, and direction from market descriptions.
"""

import re
from typing import Dict, Optional, List


class MarketParser:
    """Parse crypto information from prediction market names"""
    
    # Regex pattern for matching prices with optional $ and k suffix
    PRICE_PATTERN = r'\$?([\d,]+(?:\.\d+)?)\s*k?'
    
    # Symbol patterns for matching crypto names in market descriptions
    SYMBOL_PATTERNS = {
        'BTC': ['bitcoin', 'btc'],
        'ETH': ['ethereum', 'eth', 'ether'],
        'SOL': ['solana', 'sol'],
        'XRP': ['ripple', 'xrp'],
        'ADA': ['cardano', 'ada'],
        'DOT': ['polkadot', 'dot'],
        'AVAX': ['avalanche', 'avax'],
        'MATIC': ['polygon', 'matic'],
        'LINK': ['chainlink', 'link'],
        'UNI': ['uniswap', 'uni'],
        'ATOM': ['cosmos', 'atom'],
        'LTC': ['litecoin', 'ltc'],
        'BCH': ['bitcoin cash', 'bch'],
        'XLM': ['stellar', 'xlm'],
        'ALGO': ['algorand', 'algo'],
        'VET': ['vechain', 'vet'],
        'ICP': ['internet computer', 'icp'],
        'FIL': ['filecoin', 'fil'],
        'TRX': ['tron', 'trx'],
        'ETC': ['ethereum classic', 'etc']
    }
    
    # Keywords indicating price should be above threshold
    ABOVE_KEYWORDS = ['above', 'over', 'exceed', 'more than', 'greater than', '>']
    
    # Keywords indicating price should be below threshold
    BELOW_KEYWORDS = ['below', 'under', 'less than', '<']
    
    @classmethod
    def extract_crypto_info(cls, market_name: str) -> Dict:
        """
        Extract crypto information from market name.
        
        Args:
            market_name: Prediction market description/question
            
        Returns:
            Dictionary with:
                - valid (bool): Whether extraction was successful
                - symbol (str): Crypto symbol (e.g., 'BTC')
                - threshold (float): Price threshold in USD
                - direction (str): 'above' or 'below'
                - raw_price (str): Original price string from market
        """
        result = {
            'valid': False,
            'symbol': None,
            'threshold': None,
            'direction': None,
            'raw_price': None
        }
        
        market_lower = market_name.lower()
        
        # Extract symbol
        symbol = cls._extract_symbol(market_lower)
        if not symbol:
            return result
        result['symbol'] = symbol
        
        # Extract price threshold
        price_info = cls._extract_price(market_name)
        if not price_info:
            return result
        result['threshold'] = price_info['value']
        result['raw_price'] = price_info['raw']
        
        # Determine direction
        direction = cls._extract_direction(market_lower)
        if not direction:
            return result
        result['direction'] = direction
        
        result['valid'] = True
        return result
    
    @classmethod
    def is_crypto_market(cls, market_name: str) -> bool:
        """
        Check if market name appears to be about cryptocurrency prices.
        
        Args:
            market_name: Market description to check
            
        Returns:
            True if market appears to be about crypto prices
        """
        info = cls.extract_crypto_info(market_name)
        return info['valid']
    
    @classmethod
    def _extract_symbol(cls, market_lower: str) -> Optional[str]:
        """
        Extract crypto symbol from market name.
        
        Args:
            market_lower: Lowercase market name
            
        Returns:
            Crypto symbol or None if not found
        """
        for symbol, patterns in cls.SYMBOL_PATTERNS.items():
            for pattern in patterns:
                if pattern in market_lower:
                    return symbol
        return None
    
    @classmethod
    def _extract_price(cls, market_name: str) -> Optional[Dict]:
        """
        Extract price threshold from market name.
        
        Args:
            market_name: Market description
            
        Returns:
            Dictionary with 'value' (float) and 'raw' (str), or None if not found
        """
        # Find all price matches
        matches = re.finditer(cls.PRICE_PATTERN, market_name, re.IGNORECASE)
        
        for match in matches:
            raw_price = match.group(0)
            price_str = match.group(1)
            
            # Remove commas
            price_str = price_str.replace(',', '')
            
            try:
                value = float(price_str)
                
                # Check if 'k' suffix is present (multiply by 1000)
                if 'k' in raw_price.lower():
                    value *= 1000
                
                return {
                    'value': value,
                    'raw': raw_price
                }
            except ValueError:
                continue
        
        return None
    
    @classmethod
    def _extract_direction(cls, market_lower: str) -> Optional[str]:
        """
        Extract price direction (above/below) from market name.
        
        Args:
            market_lower: Lowercase market name
            
        Returns:
            'above' or 'below', or None if not found
        """
        # Check for above keywords
        for keyword in cls.ABOVE_KEYWORDS:
            if keyword in market_lower:
                return 'above'
        
        # Check for below keywords
        for keyword in cls.BELOW_KEYWORDS:
            if keyword in market_lower:
                return 'below'
        
        return None
    
    @classmethod
    def format_threshold(cls, threshold: float) -> str:
        """
        Format price threshold for display.
        
        Args:
            threshold: Price value
            
        Returns:
            Formatted string (e.g., '$100,000' or '$100k')
        """
        if threshold >= 1000:
            # Use k notation for large numbers
            if threshold % 1000 == 0:
                return f"${int(threshold/1000)}k"
        
        # Format with commas
        return f"${threshold:,.0f}"
    
    @classmethod
    def get_supported_symbols(cls) -> List[str]:
        """
        Get list of supported crypto symbols.
        
        Returns:
            List of supported symbols
        """
        return list(cls.SYMBOL_PATTERNS.keys())
