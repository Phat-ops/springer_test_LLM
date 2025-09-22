from datetime import datetime, timedelta
import math
from typing import Optional
from components.config import config


def classify_temperature(temp_celsius: Optional[float]) -> str:
    if temp_celsius is None:
        return "unknown"
    try:
        t = float(temp_celsius)
    except (TypeError, ValueError):
        return "unknown"
    if math.isnan(t):
        return "unknown"

    if t < config.TEMP_COLD:
        return "cold"
    elif t < config.TEMP_COOL:
        return "cool"
    elif t < config.TEMP_COMFORTABLE:
        return "comfortable"
    elif t < config.TEMP_WARM:
        return "warm"
    else:
        return "hot"


def get_weather_description(weather_code: int) -> str:
    return config.WEATHER_CODE_DESCRIPTIONS.get(
        int(weather_code), f"Weather code {weather_code}"
    )


def get_greeting(is_day: int, local_hour: Optional[int] = None) -> str:
    if local_hour is not None:
        if 5 <= local_hour < 12:
            return "Good morning"
        elif 12 <= local_hour < 18:
            return "Good afternoon"
        elif 18 <= local_hour < 22:
            return "Good evening"
        else:
            return "Good night"
    return "Good day" if int(is_day) == 1 else "Good evening"


def parse_utc_offset(utc_offset_str: str) -> timedelta:
    try:
        s = utc_offset_str.replace("+", "")
        sign = -1 if s.startswith("-") else 1
        s = s.replace("-", "")
        if ":" in s:
            hours, minutes = map(int, s.split(":"))
        else:
            if len(s) == 4:
                hours = int(s[:2]); minutes = int(s[2:])
            else:
                hours = int(s); minutes = 0
        return timedelta(hours=sign * hours, minutes=sign * minutes)
    except (ValueError, IndexError):
        return timedelta(0)


def seconds_to_utc_offset_str(offset_seconds: int) -> str:
    """Chuyển offset giây (vd: 25200) → '+07:00'."""
    sign = "+" if offset_seconds >= 0 else "-"
    s = abs(int(offset_seconds))
    h = s // 3600
    m = (s % 3600) // 60
    return f"{sign}{h:02d}:{m:02d}"


def format_local_time(utc_time_str: str, utc_offset_str: str) -> str:
    """
    Trả về: 'HH:MM UTC | HH:MM (UTC±HH:MM)'
    """
    try:
        utc_time = datetime.fromisoformat(utc_time_str.replace("Z", "+00:00"))
        offset = parse_utc_offset(utc_offset_str)
        local_time = utc_time + offset
        utc_formatted = utc_time.strftime("%H:%M UTC")
        local_formatted = local_time.strftime("%H:%M")
        return f"{utc_formatted} | {local_formatted} (UTC{utc_offset_str})"
    except Exception:
        return "Time unavailable"
