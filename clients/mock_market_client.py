"""
Mock Market Client

Generates fake Polymarket market data for testing without API keys.
"""

import random
from typing import Dict, List, Any
from .base_client import BaseClient


class MockMarketClient(BaseClient):
    """Client for generating mock Polymarket market data"""

    # Market templates for realistic fake data
    MARKET_TEMPLATES = [
        # Crypto markets
        "Will Bitcoin reach ${price}K by {month} {year}?",
        "Will Ethereum surpass ${price}K this {season}?",
        "Will Solana reach ${price} by end of {quarter}?",
        "Will XRP win SEC case by {month} {year}?",
        
        # Politics
        "Will {person} run for president in {year}?",
        "Will {party} win the {election} election?",
        "Will {policy} pass congress by {month}?",
        "Will {country} experience regime change in {year}?",
        
        # Sports
        "Will {team} win the {sport} championship?",
        "Will {athlete} break the {record} record?",
        "Will {team} make the playoffs this season?",
        "Will {sport} see a perfect season in {year}?",
        
        # Technology
        "Will {company} launch {product} in {quarter}?",
        "Will AI achieve AGI by {year}?",
        "Will {company} stock reach ${price} by {month}?",
        "Will {tech} become mainstream in {year}?",
        
        # Entertainment
        "Will {movie} win Best Picture at Oscars?",
        "Will {show} be renewed for season {number}?",
        "Will {artist} release new album in {quarter}?",
        "Will {game} be game of the year?",
    ]

    SUBSTITUTIONS = {
        "price": ["50", "100", "150", "200", "5", "10", "3"],
        "month": ["January", "February", "March", "April", "May", "June", 
                  "July", "August", "September", "October", "November", "December"],
        "year": ["2024", "2025", "2026"],
        "season": ["winter", "spring", "summer", "fall"],
        "quarter": ["Q1", "Q2", "Q3", "Q4"],
        "person": ["Biden", "Trump", "Harris", "DeSantis", "Newsom"],
        "party": ["Democrats", "Republicans"],
        "election": ["Senate", "House", "Gubernatorial"],
        "policy": ["Infrastructure Bill", "Healthcare Reform", "Tax Reform"],
        "country": ["Russia", "Iran", "Venezuela", "Myanmar"],
        "team": ["Lakers", "Warriors", "Heat", "Celtics", "Yankees", "Cowboys"],
        "sport": ["NBA", "NFL", "MLB", "NHL"],
        "athlete": ["LeBron", "Messi", "Ronaldo", "Mahomes"],
        "record": ["scoring", "rushing", "passing", "home run"],
        "company": ["Apple", "Google", "Tesla", "Meta", "Amazon"],
        "product": ["VR headset", "new iPhone", "electric car", "AI assistant"],
        "tech": ["Web3", "VR", "Quantum Computing", "Flying Cars"],
        "movie": ["Avatar 3", "Dune 3", "Marvel Movie", "Top Gun 3"],
        "show": ["Succession", "The Last of Us", "House of Dragon"],
        "artist": ["Taylor Swift", "Drake", "Beyonce", "The Weeknd"],
        "game": ["Starfield", "GTA 6", "Elder Scrolls 6"],
        "number": ["2", "3", "4", "5"],
    }

    def __init__(self):
        """Initialize mock market client"""
        super().__init__()
        self._markets = None

    def connect(self) -> bool:
        """
        Mock connection (always succeeds)

        Returns:
            Always True
        """
        self._connected = True
        return True

    def test_connection(self) -> Dict[str, Any]:
        """
        Test mock connection (always succeeds)

        Returns:
            Success response with mock message
        """
        return {
            "success": True,
            "message": "Mock market client ready (no API required)",
            "error": ""
        }

    def _generate_market_name(self) -> str:
        """Generate a random market name from templates"""
        template = random.choice(self.MARKET_TEMPLATES)
        
        # Replace placeholders with random substitutions
        result = template
        for key, values in self.SUBSTITUTIONS.items():
            placeholder = f"{{{key}}}"
            if placeholder in result:
                result = result.replace(placeholder, random.choice(values))
        
        return result

    def _generate_markets(self) -> List[Dict[str, Any]]:
        """Generate fake market data"""
        markets = []
        
        # Generate 50 markets
        for i in range(50):
            # 30% of markets should have arbitrage opportunities
            has_arb = random.random() < 0.3
            
            if has_arb:
                # Create arbitrage opportunity (YES + NO < 0.98)
                yes_price = random.uniform(0.40, 0.50)
                no_price = random.uniform(0.40, 0.50)
                # Ensure sum is less than 0.98
                total = yes_price + no_price
                if total >= 0.98:
                    yes_price = yes_price * 0.95 / total
                    no_price = no_price * 0.95 / total
            else:
                # Normal market (prices sum to ~1.0)
                yes_price = random.uniform(0.20, 0.80)
                no_price = 1.0 - yes_price + random.uniform(-0.02, 0.02)
                no_price = max(0.01, min(0.99, no_price))
            
            markets.append({
                "market_id": f"mock_market_{i+1}",
                "market_name": self._generate_market_name(),
                "yes_price": round(yes_price, 4),
                "no_price": round(no_price, 4),
                "volume_24h": round(random.uniform(5000, 50000), 2),
                "liquidity": round(random.uniform(10000, 100000), 2)
            })
        
        return markets

    def get_markets(
        self, min_volume: float = 1000, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get mock markets

        Args:
            min_volume: Minimum 24h volume filter
            limit: Maximum number of markets to return

        Returns:
            List of mock market dictionaries
        """
        if not self.is_connected():
            self.connect()
        
        # Generate markets if not already cached
        if self._markets is None:
            self._markets = self._generate_markets()
        
        # Filter by volume and limit
        filtered = [m for m in self._markets if m["volume_24h"] >= min_volume]
        return filtered[:limit]

    def disconnect(self) -> None:
        """Mock disconnect"""
        super().disconnect()
        self._markets = None
