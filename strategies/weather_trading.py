"""
Weather Trading Strategy Module

Implements weather-based prediction market trading using NOAA weather data
and Polymarket weather-related markets.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from logger import get_logger
from utils.weather_api import WeatherAPI
import re


@dataclass
class WeatherOpportunity:
    """Represents a weather-based trading opportunity"""

    market_id: str
    market_name: str
    market_type: str  # 'temperature' or 'precipitation'
    location: str
    target_date: datetime
    threshold_value: Optional[float]  # Temperature threshold or None for precipitation
    current_price: float
    weather_prediction: Dict[str, Any]
    confidence: float  # 0.0 to 1.0
    recommended_action: str  # 'buy_yes' or 'buy_no'
    bet_size: float
    reasoning: str


class WeatherTradingStrategy:
    """
    Weather-based trading strategy

    Identifies weather-related prediction markets and trades based on
    NOAA weather forecasts and historical data analysis.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize weather trading strategy

        Args:
            config: Configuration dictionary with weather trading settings
        """
        self.config = config
        self.logger = get_logger()

        # Extract configuration
        api_key = config.get("noaa_api_key", "")
        self.confidence_threshold = config.get("confidence_threshold", 0.7)
        self.max_bet_size = config.get("max_bet_size", 100)
        self.locations = config.get("locations", ["New York", "Los Angeles", "Chicago"])
        self.update_interval = config.get("update_interval_seconds", 3600)
        self.max_holding_time = config.get("max_holding_time", 86400)

        # Initialize weather API
        if not api_key or api_key == "${NOAA_API_KEY}":
            self.logger.log_warning(
                "NOAA API key not configured, weather trading disabled"
            )
            self.weather_api = None
        else:
            self.weather_api = WeatherAPI(api_key)

            # Test API connectivity
            if not self.weather_api.check_health():
                self.logger.log_error("NOAA API is not accessible")
                self.weather_api = None
            else:
                self.logger.log_info("Weather API initialized successfully")

        self.last_update = datetime.now()
        self.position_entry_times: Dict[str, datetime] = {}

    def is_enabled(self) -> bool:
        """Check if strategy is enabled and configured"""
        return self.weather_api is not None

    def find_opportunities(self, markets: List[Dict]) -> List[WeatherOpportunity]:
        """
        Find weather-based trading opportunities

        Args:
            markets: List of available markets

        Returns:
            List of identified opportunities
        """
        if not self.is_enabled():
            return []

        opportunities = []

        for market in markets:
            try:
                # Check if market is weather-related
                market_type, parsed_data = self._parse_weather_market(market)

                if market_type and parsed_data:
                    # Analyze the market
                    opportunity = self.analyze(market, parsed_data)

                    if (
                        opportunity
                        and opportunity.confidence >= self.confidence_threshold
                    ):
                        opportunities.append(opportunity)
                        self.logger.log_info(
                            f"Weather opportunity found: {opportunity.market_name} "
                            f"(confidence: {opportunity.confidence:.2%})"
                        )
            except Exception as e:
                self.logger.log_error(
                    f"Error analyzing market {market.get('question', 'Unknown')}: {e}"
                )
                continue

        return opportunities

    def _parse_weather_market(
        self, market: Dict
    ) -> Tuple[Optional[str], Optional[Dict]]:
        """
        Parse market to identify weather-related markets

        Args:
            market: Market data dictionary

        Returns:
            Tuple of (market_type, parsed_data) or (None, None) if not weather-related
        """
        question = market.get("question", "").lower()

        # Temperature market patterns
        temp_patterns = [
            r"temperature.*exceed.*?(\d+).*?degrees?.*?in\s+([a-z\s]+)",
            r"will it be.*?(\d+).*?degrees?.*?in\s+([a-z\s]+)",
            r"(\d+).*?degrees?.*?or\s+(?:higher|hotter).*?in\s+([a-z\s]+)",
            r"high temperature.*?(\d+).*?in\s+([a-z\s]+)",
        ]

        for pattern in temp_patterns:
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                try:
                    threshold = float(match.group(1))
                    location = match.group(2).strip().title()

                    # Extract target date if present
                    target_date = self._extract_date(question)

                    return "temperature", {
                        "location": location,
                        "threshold": threshold,
                        "target_date": target_date
                        or (datetime.now() + timedelta(days=1)),
                        "unit": "F",  # Assuming Fahrenheit
                    }
                except (ValueError, IndexError):
                    continue

        # Precipitation market patterns
        precip_patterns = [
            r"will it rain.*?in\s+([a-z\s]+)",
            r"precipitation.*?in\s+([a-z\s]+)",
            r"snow.*?in\s+([a-z\s]+)",
            r"chance of rain.*?in\s+([a-z\s]+)",
        ]

        for pattern in precip_patterns:
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                location = match.group(1).strip().title()
                target_date = self._extract_date(question)

                return "precipitation", {
                    "location": location,
                    "target_date": target_date or (datetime.now() + timedelta(days=1)),
                }

        return None, None

    def _extract_date(self, text: str) -> Optional[datetime]:
        """
        Extract date from market question text

        Args:
            text: Market question text

        Returns:
            Parsed datetime or None
        """
        # Simple date patterns
        date_patterns = [
            (r"on\s+(\w+\s+\d+,?\s+\d{4})", "%B %d, %Y"),
            (r"on\s+(\w+\s+\d+)", "%B %d"),
            (r"(\d{1,2}/\d{1,2}/\d{4})", "%m/%d/%Y"),
        ]

        for pattern, date_format in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    date_str = match.group(1)
                    parsed_date = datetime.strptime(date_str, date_format)

                    # If year not in pattern, assume current year
                    if "%Y" not in date_format:
                        parsed_date = parsed_date.replace(year=datetime.now().year)

                    return parsed_date
                except ValueError:
                    continue

        # Relative dates
        if "tomorrow" in text.lower():
            return datetime.now() + timedelta(days=1)
        elif "today" in text.lower():
            return datetime.now()

        return None

    def analyze(
        self, market_data: Dict, weather_params: Dict
    ) -> Optional[WeatherOpportunity]:
        """
        Analyze a weather market and determine trading opportunity

        Args:
            market_data: Market data dictionary
            weather_params: Parsed weather parameters

        Returns:
            WeatherOpportunity or None if no opportunity
        """
        if not self.is_enabled():
            return None

        market_type = (
            "temperature" if "threshold" in weather_params else "precipitation"
        )
        location = weather_params["location"]
        target_date = weather_params["target_date"]

        # Get weather forecast
        if market_type == "temperature":
            weather_data = self.weather_api.get_temperature_forecast(
                location, target_date
            )
            threshold = weather_params["threshold"]

            if not weather_data:
                return None

            # Calculate confidence based on how far forecast is from threshold
            forecast_high = weather_data["high"]

            # Determine action and confidence
            if forecast_high > threshold + 10:
                # Strong YES signal
                action = "buy_yes"
                confidence = min(0.9, 0.6 + (forecast_high - threshold) / 50)
                reasoning = f"Forecast high of {forecast_high}°F exceeds threshold of {threshold}°F by {forecast_high - threshold}°F"
            elif forecast_high > threshold + 5:
                # Moderate YES signal
                action = "buy_yes"
                confidence = 0.7
                reasoning = f"Forecast high of {forecast_high}°F likely exceeds threshold of {threshold}°F"
            elif forecast_high < threshold - 10:
                # Strong NO signal
                action = "buy_no"
                confidence = min(0.9, 0.6 + (threshold - forecast_high) / 50)
                reasoning = f"Forecast high of {forecast_high}°F well below threshold of {threshold}°F by {threshold - forecast_high}°F"
            elif forecast_high < threshold - 5:
                # Moderate NO signal
                action = "buy_no"
                confidence = 0.7
                reasoning = f"Forecast high of {forecast_high}°F likely below threshold of {threshold}°F"
            else:
                # Too close to call
                return None

            weather_prediction = weather_data

        else:  # precipitation
            precip_prob = self.weather_api.get_precipitation_probability(
                location, target_date
            )

            if precip_prob is None:
                return None

            # Determine action based on precipitation probability
            if precip_prob > 70:
                action = "buy_yes"
                confidence = min(0.9, precip_prob / 100)
                reasoning = f"High precipitation probability: {precip_prob}%"
            elif precip_prob < 30:
                action = "buy_no"
                confidence = min(0.9, (100 - precip_prob) / 100)
                reasoning = f"Low precipitation probability: {precip_prob}%"
            else:
                # Uncertain
                return None

            weather_prediction = {"precipitation_probability": precip_prob}

        # Get current market price
        current_price = market_data.get("yes_price", 0.5)

        # Calculate bet size based on confidence and Kelly criterion
        bet_size = self._calculate_bet_size(confidence, current_price)

        return WeatherOpportunity(
            market_id=market_data.get("id", ""),
            market_name=market_data.get("question", ""),
            market_type=market_type,
            location=location,
            target_date=target_date,
            threshold_value=weather_params.get("threshold"),
            current_price=current_price,
            weather_prediction=weather_prediction,
            confidence=confidence,
            recommended_action=action,
            bet_size=bet_size,
            reasoning=reasoning,
        )

    def _calculate_bet_size(self, confidence: float, price: float) -> float:
        """
        Calculate optimal bet size using Kelly criterion

        Args:
            confidence: Confidence in prediction (0.0 to 1.0)
            price: Current market price

        Returns:
            Recommended bet size
        """
        # Simple Kelly criterion: f = (p * b - q) / b
        # where p = probability of winning, q = 1-p, b = odds

        # Convert confidence to probability
        p = confidence
        q = 1 - p

        # Calculate odds from price
        if price >= 0.99:
            odds = 0.01
        elif price <= 0.01:
            odds = 99
        else:
            odds = (1 - price) / price

        # Kelly fraction
        if odds > 0:
            kelly_fraction = (p * odds - q) / odds
            kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25% of bankroll
        else:
            kelly_fraction = 0

        # Calculate bet size (use fraction of max bet size as "bankroll")
        bet_size = (
            kelly_fraction * self.max_bet_size * 4
        )  # Assuming max_bet_size is 25% of bankroll
        bet_size = max(10, min(bet_size, self.max_bet_size))  # Min $10, max configured

        return round(bet_size, 2)

    def should_exit(self, position: Dict, current_data: Dict) -> Tuple[bool, str]:
        """
        Determine if a position should be exited

        Args:
            position: Current position data
            current_data: Current market and weather data

        Returns:
            Tuple of (should_exit, reason)
        """
        market_id = position.get("market_id")

        # Check holding time
        if market_id in self.position_entry_times:
            entry_time = self.position_entry_times[market_id]
            holding_time = (datetime.now() - entry_time).total_seconds()

            if holding_time > self.max_holding_time:
                return True, "Maximum holding time exceeded"

        # Check if weather forecast has changed significantly
        current_weather = current_data.get("weather_prediction", {})
        original_weather = position.get("weather_prediction", {})

        if "high" in current_weather and "high" in original_weather:
            temp_change = abs(current_weather["high"] - original_weather["high"])
            if temp_change > 10:  # More than 10 degree change
                return True, f"Weather forecast changed significantly ({temp_change}°F)"

        if (
            "precipitation_probability" in current_weather
            and "precipitation_probability" in original_weather
        ):
            prob_change = abs(
                current_weather["precipitation_probability"]
                - original_weather["precipitation_probability"]
            )
            if prob_change > 30:  # More than 30% change
                return (
                    True,
                    f"Precipitation probability changed significantly ({prob_change}%)",
                )

        # Check profit target
        entry_price = position.get("entry_price", 0.5)
        current_price = current_data.get("current_price", 0.5)
        profit_pct = ((current_price - entry_price) / entry_price) * 100

        if profit_pct > 20:  # 20% profit target
            return True, f"Profit target reached ({profit_pct:.1f}%)"

        # Check stop loss
        if profit_pct < -10:  # 10% stop loss
            return True, f"Stop loss triggered ({profit_pct:.1f}%)"

        return False, ""

    def record_position_entry(self, market_id: str) -> None:
        """
        Record when a position was entered

        Args:
            market_id: Market identifier
        """
        self.position_entry_times[market_id] = datetime.now()

    def get_name(self) -> str:
        """Get strategy name"""
        return "weather_trading"

    def get_type(self) -> str:
        """Get strategy type"""
        return "weather"
