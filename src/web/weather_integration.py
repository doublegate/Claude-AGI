"""
Weather API Integration for Claude-AGI
=======================================

Integrates with weather APIs to provide environmental context including:
- Current weather conditions
- Weather forecasts
- Historical weather data
- Alerts and warnings
- Climate data
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class WeatherCondition(Enum):
    """Weather condition types"""
    CLEAR = "clear"
    PARTLY_CLOUDY = "partly_cloudy"
    CLOUDY = "cloudy"
    RAIN = "rain"
    SNOW = "snow"
    THUNDERSTORM = "thunderstorm"
    FOG = "fog"
    WINDY = "windy"


class AlertSeverity(Enum):
    """Weather alert severity levels"""
    ADVISORY = "advisory"
    WATCH = "watch"
    WARNING = "warning"
    EXTREME = "extreme"


@dataclass
class WeatherData:
    """Current weather data"""
    location: str
    temperature: float  # Celsius
    feels_like: float
    condition: WeatherCondition
    description: str
    humidity: int  # Percentage
    pressure: float  # hPa
    wind_speed: float  # m/s
    wind_direction: int  # Degrees
    cloud_cover: int  # Percentage
    visibility: float  # km
    uv_index: float
    timestamp: datetime = field(default_factory=datetime.now)
    sunrise: Optional[datetime] = None
    sunset: Optional[datetime] = None


@dataclass
class WeatherForecast:
    """Weather forecast data"""
    date: datetime
    temp_high: float
    temp_low: float
    condition: WeatherCondition
    description: str
    precipitation_probability: int  # Percentage
    precipitation_amount: float  # mm
    wind_speed: float
    humidity: int


@dataclass
class WeatherAlert:
    """Weather alert/warning"""
    alert_id: str
    event: str
    severity: AlertSeverity
    description: str
    start_time: datetime
    end_time: datetime
    affected_areas: List[str] = field(default_factory=list)


class WeatherIntegration:
    """Weather API integration for environmental context"""

    def __init__(self, api_key: Optional[str] = None, units: str = "metric"):
        self.api_key = api_key
        self.units = units  # metric, imperial, standard
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.cache: Dict[str, WeatherData] = {}
        self.cache_expiry: Dict[str, datetime] = {}
        self.cache_duration = timedelta(minutes=10)

    async def get_current_weather(
        self,
        location: str,
        country_code: Optional[str] = None
    ) -> Optional[WeatherData]:
        """Get current weather for a location"""

        cache_key = f"current_{location}_{country_code}"

        # Check cache
        if self._is_cached(cache_key):
            logger.info(f"Retrieved weather from cache: {location}")
            return self.cache[cache_key]

        query = f"{location},{country_code}" if country_code else location

        params = {
            'q': query,
            'units': self.units,
            'appid': self.api_key or 'demo'
        }

        logger.info(f"Fetching current weather for: {location}")

        # Mock implementation
        weather = self._generate_mock_weather(location)

        # Cache result
        self.cache[cache_key] = weather
        self.cache_expiry[cache_key] = datetime.now() + self.cache_duration

        return weather

    async def get_forecast(
        self,
        location: str,
        days: int = 5,
        country_code: Optional[str] = None
    ) -> List[WeatherForecast]:
        """Get weather forecast"""

        query = f"{location},{country_code}" if country_code else location

        params = {
            'q': query,
            'cnt': days,
            'units': self.units,
            'appid': self.api_key or 'demo'
        }

        logger.info(f"Fetching {days}-day forecast for: {location}")

        # Mock implementation
        forecasts = []
        for i in range(days):
            forecasts.append(WeatherForecast(
                date=datetime.now() + timedelta(days=i),
                temp_high=22.0 + i,
                temp_low=15.0 + i,
                condition=WeatherCondition.PARTLY_CLOUDY,
                description="Partly cloudy",
                precipitation_probability=30,
                precipitation_amount=0.5,
                wind_speed=5.0,
                humidity=60
            ))

        return forecasts

    async def get_hourly_forecast(
        self,
        location: str,
        hours: int = 24,
        country_code: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get hourly weather forecast"""

        query = f"{location},{country_code}" if country_code else location

        logger.info(f"Fetching {hours}-hour forecast for: {location}")

        # Mock implementation
        hourly = []
        for i in range(hours):
            hourly.append({
                'time': datetime.now() + timedelta(hours=i),
                'temperature': 18.0 + (i % 12),
                'condition': WeatherCondition.CLEAR.value,
                'precipitation_probability': 10 + (i % 20),
                'wind_speed': 3.0 + (i % 5)
            })

        return hourly

    async def get_alerts(
        self,
        location: str,
        country_code: Optional[str] = None
    ) -> List[WeatherAlert]:
        """Get weather alerts for a location"""

        query = f"{location},{country_code}" if country_code else location

        logger.info(f"Fetching weather alerts for: {location}")

        # Mock implementation - normally would fetch from API
        alerts = []

        # Example alert
        if "storm" in location.lower():
            alerts.append(WeatherAlert(
                alert_id="alert_001",
                event="Thunderstorm Watch",
                severity=AlertSeverity.WATCH,
                description="Thunderstorms possible in the area",
                start_time=datetime.now(),
                end_time=datetime.now() + timedelta(hours=12),
                affected_areas=[location]
            ))

        return alerts

    async def get_air_quality(
        self,
        latitude: float,
        longitude: float
    ) -> Dict[str, Any]:
        """Get air quality index"""

        logger.info(f"Fetching air quality for: {latitude}, {longitude}")

        # Mock implementation
        return {
            'aqi': 45,  # Air Quality Index (0-500)
            'category': 'Good',
            'pollutants': {
                'pm2.5': 12.5,
                'pm10': 25.0,
                'o3': 30.0,
                'no2': 15.0,
                'so2': 5.0,
                'co': 0.5
            },
            'timestamp': datetime.now()
        }

    async def get_historical_weather(
        self,
        location: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[WeatherData]:
        """Get historical weather data"""

        logger.info(f"Fetching historical weather: {location}, {start_date} to {end_date}")

        # Mock implementation
        historical = []
        current_date = start_date

        while current_date <= end_date:
            historical.append(WeatherData(
                location=location,
                temperature=20.0,
                feels_like=19.0,
                condition=WeatherCondition.CLEAR,
                description="Clear sky",
                humidity=55,
                pressure=1013.0,
                wind_speed=3.5,
                wind_direction=180,
                cloud_cover=10,
                visibility=10.0,
                uv_index=5.0,
                timestamp=current_date
            ))
            current_date += timedelta(days=1)

        return historical

    async def compare_climates(
        self,
        location1: str,
        location2: str,
        months: int = 12
    ) -> Dict[str, Any]:
        """Compare climate data between locations"""

        logger.info(f"Comparing climates: {location1} vs {location2}")

        # Mock implementation
        return {
            'locations': [location1, location2],
            'period_months': months,
            'comparison': {
                'average_temperature': {
                    location1: 18.5,
                    location2: 22.3
                },
                'average_precipitation': {
                    location1: 800,  # mm/year
                    location2: 600
                },
                'average_humidity': {
                    location1: 65,  # percentage
                    location2: 55
                },
                'sunny_days_per_year': {
                    location1: 200,
                    location2: 280
                }
            }
        }

    async def get_weather_summary(
        self,
        location: str
    ) -> Dict[str, Any]:
        """Get comprehensive weather summary"""

        current = await self.get_current_weather(location)
        forecast = await self.get_forecast(location, days=3)
        alerts = await self.get_alerts(location)

        summary = {
            'location': location,
            'current': current,
            'forecast_3day': forecast,
            'active_alerts': len(alerts),
            'alerts': alerts,
            'timestamp': datetime.now()
        }

        return summary

    async def is_weather_suitable(
        self,
        location: str,
        activity: str
    ) -> Dict[str, Any]:
        """Check if weather is suitable for an activity"""

        current = await self.get_current_weather(location)

        # Simple rules for different activities
        activity_requirements = {
            'outdoor_sports': {
                'max_temp': 35.0,
                'min_temp': 5.0,
                'max_wind': 15.0,
                'no_rain': True
            },
            'hiking': {
                'max_temp': 30.0,
                'min_temp': 10.0,
                'max_wind': 20.0,
                'visibility': 5.0
            },
            'picnic': {
                'max_temp': 32.0,
                'min_temp': 15.0,
                'no_rain': True,
                'max_wind': 10.0
            }
        }

        requirements = activity_requirements.get(
            activity,
            activity_requirements['outdoor_sports']
        )

        suitable = True
        reasons = []

        if current:
            if current.temperature > requirements.get('max_temp', 40):
                suitable = False
                reasons.append("Too hot")
            if current.temperature < requirements.get('min_temp', 0):
                suitable = False
                reasons.append("Too cold")
            if current.wind_speed > requirements.get('max_wind', 50):
                suitable = False
                reasons.append("Too windy")
            if requirements.get('no_rain') and current.condition == WeatherCondition.RAIN:
                suitable = False
                reasons.append("Raining")

        return {
            'suitable': suitable,
            'activity': activity,
            'current_conditions': current,
            'reasons': reasons if not suitable else ['Conditions are suitable']
        }

    def _is_cached(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self.cache:
            return False
        if key not in self.cache_expiry:
            return False
        return datetime.now() < self.cache_expiry[key]

    def _generate_mock_weather(self, location: str) -> WeatherData:
        """Generate mock weather data"""
        return WeatherData(
            location=location,
            temperature=20.5,
            feels_like=19.0,
            condition=WeatherCondition.PARTLY_CLOUDY,
            description="Partly cloudy",
            humidity=60,
            pressure=1013.25,
            wind_speed=4.5,
            wind_direction=180,
            cloud_cover=40,
            visibility=10.0,
            uv_index=5.0,
            sunrise=datetime.now().replace(hour=6, minute=30),
            sunset=datetime.now().replace(hour=18, minute=45)
        )

    def clear_cache(self):
        """Clear the weather cache"""
        self.cache.clear()
        self.cache_expiry.clear()
        logger.info("Weather cache cleared")
