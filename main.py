# main.py
from components.state import WeatherAgentState
from graph import build_graph

# Fallback chạy tuần tự nếu graph không tạo weather_info
from components.nodes import (
    fetch_location_data,
    fetch_weather_data,
    generate_weather_info,
)

def banner(title: str = "WEATHER INFORMATION") -> str:
    line = "=" * 60
    return f"\n{line}\n{title}\n{line}\n"

def run_cli() -> None:
    try:
        name = input("Enter your name: ").strip() or "Friend"

        state: WeatherAgentState = {
            "name": name,
            "location_data": None,
            "weather_data": None,
            "weather_info": None,
        }

        app = build_graph()

        # Gọi invoke/run tùy phiên bản
        new_state = None
        if hasattr(app, "invoke"):
            new_state = app.invoke(state)
        elif hasattr(app, "run"):
            new_state = app.run(state)

        # Nếu graph không trả state hợp lệ -> fallback
        if not isinstance(new_state, dict):
            new_state = state

        state = new_state

        # Nếu vẫn chưa có weather_info -> chạy tuần tự các node
        if not state.get("weather_info"):
            state = fetch_location_data(state)
            state = fetch_weather_data(state)
            state = generate_weather_info(state)

        print(banner())
        print(state.get("weather_info"))
        print("=" * 60)

    except KeyboardInterrupt:
        print("\nCanceled by user.")
    except Exception as e:
        print(banner("ERROR"))
        print(f"{type(e).__name__}: {e}")
        print("=" * 60)

if __name__ == "__main__":
    run_cli()
