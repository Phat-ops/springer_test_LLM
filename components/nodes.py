import time
import requests
from datetime import datetime
from typing import Dict, Any

from components.state import WeatherAgentState
from components.config import config
from components.helper_functions import (
    classify_temperature,
    get_weather_description,
    get_greeting,
    format_local_time,
    parse_utc_offset,
    seconds_to_utc_offset_str,
)


def _get_json_with_retry(url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Gọi HTTP GET với retry + exponential backoff (xử lý 429/5xx).
    """
    params = params or {}
    delay = 0.5  # giây
    last_err = None
    for attempt in range(1, config.MAX_RETRIES + 1):
        try:
            resp = requests.get(url, params=params, timeout=config.REQUEST_TIMEOUT)
            # Nếu dính 429 (rate limit) → thử backoff rồi retry
            if resp.status_code == 429:
                last_err = requests.HTTPError(f"429 Too Many Requests: {url}")
                time.sleep(delay)
                delay *= 2
                continue
            resp.raise_for_status()
            return resp.json()
        except (requests.HTTPError, requests.ConnectionError, requests.Timeout) as e:
            last_err = e
            time.sleep(delay)
            delay *= 2
        except Exception as e:
            # Lỗi khác -> dừng sớm
            raise e
    # Hết số lần retry
    raise Exception(f"HTTP failed after retries: {last_err}")


def _normalize_ipapi(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Chuẩn hóa dữ liệu từ ipapi.co về schema dùng chung.
    """
    required = ['city', 'region', 'country_name', 'latitude', 'longitude', 'utc_offset', 'timezone']
    for f in required:
        if f not in payload:
            raise ValueError(f"Missing required field: {f}")
    return {
        "city": payload["city"],
        "region": payload["region"],
        "country_name": payload["country_name"],
        "latitude": payload["latitude"],
        "longitude": payload["longitude"],
        "utc_offset": payload["utc_offset"],
        "timezone": payload["timezone"],
    }


def _normalize_ipwho(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Chuẩn hóa dữ liệu từ ipwho.is về schema dùng chung.
    ipwho.is trả 'country' (tên quốc gia đầy đủ), 'latitude', 'longitude',
    'timezone' có thể là string hoặc object { 'id': 'Asia/Ho_Chi_Minh', ... }.
    'utc_offset' có thể không có -> cho phép rỗng, sẽ fallback bằng weather_data.
    """
    if not payload.get("success", True):  # ipwho.is có trường 'success'
        msg = payload.get("message") or payload.get("reason") or "Unknown error from ipwho.is"
        raise ValueError(f"ipwho.is error: {msg}")

    city = payload.get("city")
    region = payload.get("region") or payload.get("region_name") or payload.get("state") or ""
    country_name = payload.get("country") or payload.get("country_name") or ""
    latitude = payload.get("latitude") or payload.get("lat")
    longitude = payload.get("longitude") or payload.get("lon")

    tz = payload.get("timezone")
    if isinstance(tz, dict):
        timezone_id = tz.get("id") or tz.get("name") or ""
        utc_offset = tz.get("utc") or tz.get("offset")  # có thể là '+07:00' hoặc số giờ
        if isinstance(utc_offset, (int, float)):
            # chuyển số giờ -> '+HH:MM'
            utc_offset = seconds_to_utc_offset_str(int(utc_offset * 3600))
    else:
        timezone_id = tz or ""
        utc_offset = payload.get("utc_offset")  # hi vọng có, nếu không sẽ để rỗng

    # Cho phép thiếu utc_offset -> sẽ fallback sang weather_data.utc_offset_seconds
    for k in ("city", "region", "country_name", "latitude", "longitude"):
        if not locals()[k]:
            raise ValueError(f"Missing required field from ipwho.is: {k}")

    return {
        "city": city,
        "region": region,
        "country_name": country_name,
        "latitude": latitude,
        "longitude": longitude,
        "utc_offset": utc_offset or "",  # có thể rỗng
        "timezone": timezone_id or "",
    }


def fetch_location_data(state: WeatherAgentState) -> WeatherAgentState:
    """
    Lấy vị trí dựa trên IP:
      1) ipapi.co (retry+backoff)
      2) fallback ipwho.is nếu ipapi.co gặp 429/lỗi
    """
    # Thử ipapi.co trước
    try:
        payload = _get_json_with_retry(config.LOCATION_API_URL)
        state["location_data"] = _normalize_ipapi(payload)
        return state
    except Exception as e_primary:
        # Fallback sang ipwho.is
        try:
            payload = _get_json_with_retry("https://ipwho.is/")
            state["location_data"] = _normalize_ipwho(payload)
            return state
        except Exception as e_fallback:
            raise Exception(
                f"Failed to fetch location data. Primary(ipapi.co): {e_primary}. "
                f"Fallback(ipwho.is): {e_fallback}"
            )


def fetch_weather_data(state: WeatherAgentState) -> WeatherAgentState:
    """
    Lấy thời tiết hiện tại từ Open-Meteo theo toạ độ.
    """
    if not state.get("location_data"):
        raise Exception("Location data not available for weather fetch")
    location = state["location_data"]
    try:
        params = {
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "current_weather": "true",
        }
        response = _get_json_with_retry(config.WEATHER_API_BASE_URL, params=params)

        if "current_weather" not in response:
            raise ValueError("Missing current_weather data in response")

        required_weather_fields = ['time', 'temperature', 'windspeed', 'winddirection', 'is_day', 'weathercode']
        current_weather = response['current_weather']
        for field in required_weather_fields:
            if field not in current_weather:
                raise ValueError(f"Missing required weather field: {field}")

        state["weather_data"] = response
        return state
    except Exception as e:
        raise Exception(f"Failed to fetch weather data: {e}")


def generate_weather_info(state: WeatherAgentState) -> WeatherAgentState:
    """
    Ghép thông tin vị trí + thời tiết thành chuỗi báo cáo.
    """
    if not state.get("location_data") or not state.get("weather_data"):
        raise Exception("Location or weather data not available for info generation")

    location = state["location_data"]
    weather = state["weather_data"]["current_weather"]
    units = state["weather_data"].get("current_weather_units", {})
    utc_offset_seconds = state["weather_data"].get("utc_offset_seconds", 0)

    try:
        name = state.get("name") or "Friend"
        city = location["city"]
        region = location["region"]
        country = location["country_name"]

        temperature = weather["temperature"]
        temp_unit = units.get("temperature", "°C")
        windspeed = weather["windspeed"]
        wind_unit = units.get("windspeed", "km/h")
        is_day = weather["is_day"]
        weather_code = weather["weathercode"]
        utc_time = weather["time"]

        # offset ưu tiên lấy từ location; nếu không có -> dùng utc_offset_seconds từ weather
        if location.get("utc_offset"):
            offset_str = location["utc_offset"]
        else:
            offset_str = seconds_to_utc_offset_str(int(utc_offset_seconds))

        # Tính giờ địa phương để lời chào tự nhiên hơn
        try:
            utc_dt = datetime.fromisoformat(utc_time.replace("Z", "+00:00"))
            local_dt = utc_dt + parse_utc_offset(offset_str)
            local_hour = local_dt.hour
        except Exception:
            local_hour = None

        greeting = get_greeting(is_day, local_hour)
        temp_classification = classify_temperature(temperature)
        weather_description = get_weather_description(weather_code)
        time_info = format_local_time(utc_time, offset_str)

        weather_info_parts = [
            f"Time: {time_info}",
            "",
            f"{greeting}, {name}!",
            "",
            f"Your current location: {city}, {region}, {country}",
            "",
            "Current weather conditions:",
            f"- {weather_description}",
            f"- Temperature: {temperature}{temp_unit} ({temp_classification})",
            f"- Wind: {windspeed} {wind_unit}",
        ]
        state["weather_info"] = "\n".join(weather_info_parts)
        return state
    except KeyError as e:
        raise Exception(f"Missing data field for weather info generation: {str(e)}")
    except Exception as e:
        raise Exception(f"Error generating weather info: {str(e)}")
