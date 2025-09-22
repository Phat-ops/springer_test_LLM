# graph.py
from typing import Any, Dict

from components.nodes import (
    fetch_location_data,
    fetch_weather_data,
    generate_weather_info,
)

# Fallback app nếu không có LangGraph
class FallbackApp:
    def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        state = fetch_location_data(state)
        state = fetch_weather_data(state)
        state = generate_weather_info(state)
        return state


def build_graph():
    """
    Nếu LangGraph có sẵn, xây đồ thị; nếu không, trả về FallbackApp.
    """
    try:
        from langgraph.graph import StateGraph, END

        g = StateGraph(dict)  # state là dict (TypedDict vẫn ok)
        g.add_node("fetch_location_data", fetch_location_data)
        g.add_node("fetch_weather_data", fetch_weather_data)
        g.add_node("generate_weather_info", generate_weather_info)

        g.set_entry_point("fetch_location_data")
        g.add_edge("fetch_location_data", "fetch_weather_data")
        g.add_edge("fetch_weather_data", "generate_weather_info")
        g.add_edge("generate_weather_info", END)

        return g.compile()
    except Exception:
        # Không tìm thấy langgraph hoặc lỗi build => dùng fallback
        return FallbackApp()
