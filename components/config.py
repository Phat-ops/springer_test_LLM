import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from typing import ClassVar, Dict

load_dotenv()

class Config(BaseSettings):
    """
    Configuration for the Weather Agent.
    """
    
    # API Endpoints
    LOCATION_API_URL: str = "https://ipapi.co/json/"
    WEATHER_API_BASE_URL: str = "https://api.open-meteo.com/v1/forecast"
    
    # Request timeout settings
    REQUEST_TIMEOUT: int = 10  # seconds
    MAX_RETRIES: int = 3
    
    # Temperature classification thresholds (Celsius)
    TEMP_COLD: float = 10.0
    TEMP_COOL: float = 18.0
    TEMP_COMFORTABLE: float = 26.0
    TEMP_WARM: float = 32.0
    # Above TEMP_WARM is considered HOT
    
    # Weather code mappings (WMO codes)
    WEATHER_CODE_DESCRIPTIONS: ClassVar[Dict[int, str]] = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy", 
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow fall",
        73: "Moderate snow fall",
        75: "Heavy snow fall",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail"
    }



    #TEMP_MIN = str = "Needs Debugging"

    
    # TEMP_MIN: str = "Needs Debugging"

    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"
    }

# Instantiate global config object
config = Config()