"""
Weather API Module

Provides integration with NOAA Weather API for fetching real-time and
historical weather data, forecasts, and weather condition analysis.
"""

import requests
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from logger import get_logger
import time


class WeatherAPI:
    """
    Interface to NOAA Weather API for weather data retrieval

    Provides methods to fetch current weather, forecasts, and historical data
    with built-in error handling and retry logic.
    """

    def __init__(self, api_key: str, cache_duration: int = 3600):
        """
        Initialize Weather API client

        Args:
            api_key: NOAA API key for authentication
            cache_duration: Cache duration in seconds (default: 1 hour)
        """
        self.api_key = api_key
        self.base_url = "https://api.weather.gov"
        self.logger = get_logger()
        self.cache: Dict[str, Tuple[datetime, Any]] = {}
        self.cache_duration = cache_duration
        self.max_retries = 3
        self.retry_delay = 2  # seconds

    def _get_cached(self, key: str) -> Optional[Any]:
        """
        Get cached data if it exists and is fresh

        Args:
            key: Cache key

        Returns:
            Cached data or None if expired/not found
        """
        if key in self.cache:
            cached_time, data = self.cache[key]
            if datetime.now() - cached_time < timedelta(seconds=self.cache_duration):
                return data
        return None

    def _set_cache(self, key: str, data: Any) -> None:
        """
        Store data in cache

        Args:
            key: Cache key
            data: Data to cache
        """
        self.cache[key] = (datetime.now(), data)

    def _make_request(
        self, endpoint: str, params: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Make HTTP request to NOAA API with retry logic

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            Response JSON or None on failure
        """
        url = f"{self.base_url}{endpoint}"
        headers = {
            "User-Agent": "(PolymarketTradingBot, contact@example.com)",  # NOAA requires User-Agent
        }

        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, headers=headers, params=params, timeout=10)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                self.logger.log_error(
                    f"Weather API request failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    return None
        return None

    def get_location_coordinates(self, location: str) -> Optional[Tuple[float, float]]:
        """
        Get latitude and longitude for a location name

        Args:
            location: Location name (e.g., "New York", "Los Angeles")

        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        # Simple location mapping (in production, use geocoding service)
        location_map = {
            "New York": (40.7128, -74.0060),
            "Los Angeles": (34.0522, -118.2437),
            "Chicago": (41.8781, -87.6298),
            "Houston": (29.7604, -95.3698),
            "Phoenix": (33.4484, -112.0740),
            "Philadelphia": (39.9526, -75.1652),
            "San Antonio": (29.4241, -98.4936),
            "San Diego": (32.7157, -117.1611),
            "Dallas": (32.7767, -96.7970),
            "San Jose": (37.3382, -121.8863),
        }

        return location_map.get(location)

    def get_current_weather(self, location: str) -> Optional[Dict[str, Any]]:
        """
        Get current weather conditions for a location

        Args:
            location: Location name

        Returns:
            Dictionary with weather data or None on failure
        """
        cache_key = f"current_{location}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        coords = self.get_location_coordinates(location)
        if not coords:
            self.logger.log_error(f"Location not found: {location}")
            return None

        lat, lon = coords

        # Get weather station data from NOAA
        # First, get the grid point
        point_url = f"/points/{lat},{lon}"
        point_data = self._make_request(point_url)

        if not point_data:
            return None

        try:
            # Get observation station
            stations_url = point_data["properties"]["observationStations"]
            stations_data = self._make_request(stations_url.replace(self.base_url, ""))

            if not stations_data or not stations_data.get("features"):
                return None

            # Get latest observation from first station
            station_id = stations_data["features"][0]["properties"]["stationIdentifier"]
            obs_url = f"/stations/{station_id}/observations/latest"
            obs_data = self._make_request(obs_url)

            if not obs_data:
                return None

            props = obs_data["properties"]

            weather_data = {
                "location": location,
                "temperature_c": props.get("temperature", {}).get("value"),
                "temperature_f": self._celsius_to_fahrenheit(
                    props.get("temperature", {}).get("value")
                ),
                "humidity": props.get("relativeHumidity", {}).get("value"),
                "wind_speed": props.get("windSpeed", {}).get("value"),
                "precipitation": props.get("precipitationLastHour", {}).get("value", 0),
                "conditions": props.get("textDescription", "Unknown"),
                "timestamp": props.get("timestamp"),
            }

            self._set_cache(cache_key, weather_data)
            return weather_data

        except (KeyError, IndexError, TypeError) as e:
            self.logger.log_error(f"Error parsing weather data: {e}")
            return None

    def get_forecast(
        self, location: str, days: int = 7
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get weather forecast for a location

        Args:
            location: Location name
            days: Number of days to forecast (default: 7)

        Returns:
            List of forecast periods or None on failure
        """
        cache_key = f"forecast_{location}_{days}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        coords = self.get_location_coordinates(location)
        if not coords:
            self.logger.log_error(f"Location not found: {location}")
            return None

        lat, lon = coords

        # Get forecast data
        point_url = f"/points/{lat},{lon}"
        point_data = self._make_request(point_url)

        if not point_data:
            return None

        try:
            forecast_url = point_data["properties"]["forecast"]
            forecast_data = self._make_request(forecast_url.replace(self.base_url, ""))

            if not forecast_data or not forecast_data.get("properties", {}).get(
                "periods"
            ):
                return None

            periods = forecast_data["properties"]["periods"][
                : days * 2
            ]  # Each day has 2 periods

            forecasts = []
            for period in periods:
                forecast = {
                    "name": period.get("name"),
                    "temperature": period.get("temperature"),
                    "temperature_unit": period.get("temperatureUnit"),
                    "precipitation_probability": period.get(
                        "probabilityOfPrecipitation", {}
                    ).get("value", 0),
                    "wind_speed": period.get("windSpeed"),
                    "short_forecast": period.get("shortForecast"),
                    "detailed_forecast": period.get("detailedForecast"),
                    "start_time": period.get("startTime"),
                    "end_time": period.get("endTime"),
                }
                forecasts.append(forecast)

            self._set_cache(cache_key, forecasts)
            return forecasts

        except (KeyError, IndexError, TypeError) as e:
            self.logger.log_error(f"Error parsing forecast data: {e}")
            return None

    def get_temperature_forecast(
        self, location: str, target_date: datetime
    ) -> Optional[Dict[str, float]]:
        """
        Get temperature forecast for a specific date

        Args:
            location: Location name
            target_date: Target date for forecast

        Returns:
            Dictionary with high/low temperatures or None
        """
        forecasts = self.get_forecast(location, days=7)
        if not forecasts:
            return None

        # Find forecasts matching target date
        target_date_str = target_date.strftime("%Y-%m-%d")
        matching_forecasts = []

        for forecast in forecasts:
            start_time = datetime.fromisoformat(
                forecast["start_time"].replace("Z", "+00:00")
            )
            if start_time.strftime("%Y-%m-%d") == target_date_str:
                matching_forecasts.append(forecast)

        if not matching_forecasts:
            return None

        temps = [f["temperature"] for f in matching_forecasts]
        return {
            "high": max(temps),
            "low": min(temps),
            "avg": sum(temps) / len(temps),
            "unit": matching_forecasts[0]["temperature_unit"],
        }

    def get_precipitation_probability(
        self, location: str, target_date: datetime
    ) -> Optional[float]:
        """
        Get precipitation probability for a specific date

        Args:
            location: Location name
            target_date: Target date for forecast

        Returns:
            Precipitation probability (0-100) or None
        """
        forecasts = self.get_forecast(location, days=7)
        if not forecasts:
            return None

        # Find forecasts matching target date
        target_date_str = target_date.strftime("%Y-%m-%d")
        matching_forecasts = []

        for forecast in forecasts:
            start_time = datetime.fromisoformat(
                forecast["start_time"].replace("Z", "+00:00")
            )
            if start_time.strftime("%Y-%m-%d") == target_date_str:
                matching_forecasts.append(forecast)

        if not matching_forecasts:
            return None

        # Return highest precipitation probability for the day
        probs = [
            f["precipitation_probability"]
            for f in matching_forecasts
            if f["precipitation_probability"]
        ]
        return max(probs) if probs else 0.0

    def _celsius_to_fahrenheit(self, celsius: Optional[float]) -> Optional[float]:
        """Convert Celsius to Fahrenheit"""
        if celsius is None:
            return None
        return (celsius * 9 / 5) + 32

    def check_health(self) -> bool:
        """
        Check if API is accessible

        Returns:
            True if API is healthy, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}", timeout=5)
            return response.status_code == 200 or response.status_code == 301
        except:
            return False
