from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class LocationData(BaseModel):
    """Location data from IP geolocation API"""
    city: str = Field(..., description="City name")
    region: str = Field(..., description="Region/state name")
    country_name: str = Field(..., description="Full country name")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    utc_offset: str = Field(..., description="UTC offset (e.g., '+05:30')")
    timezone: str = Field(..., description="Timezone identifier")

class CurrentWeatherUnits(BaseModel):
    """Units for current weather data"""
    time: str = Field(..., description="Time format")
    temperature: str = Field(..., description="Temperature unit")
    windspeed: str = Field(..., description="Wind speed unit")
    winddirection: str = Field(..., description="Wind direction unit")
    weathercode: str = Field(..., description="Weather code format")

class CurrentWeather(BaseModel):
    """Current weather conditions"""
    time: str = Field(..., description="Current time in ISO8601 format")
    temperature: float = Field(..., description="Current temperature")
    windspeed: float = Field(..., description="Current wind speed")
    winddirection: int = Field(..., description="Wind direction in degrees")
    is_day: bool = Field(..., description="1 if day, 0 if night")
    weathercode: int = Field(..., description="WMO weather code")

class WeatherData(BaseModel):
    """Complete weather response from Open-Meteo API"""
    latitude: float = Field(..., description="Latitude")
    longitude: float = Field(..., description="Longitude")
    timezone: str = Field(..., description="Timezone")
    utc_offset_seconds: int = Field(..., description="UTC offset in seconds")
    current_weather_units: CurrentWeatherUnits = Field(..., description="Units for weather data")
    current_weather: CurrentWeather = Field(..., description="Current weather conditions")