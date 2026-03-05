#!/usr/bin/env python3
import requests

def get_weather(city):
    # 1. Get coordinates for the city
    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    geo_params = {"name": city, "count": 1, "language": "en", "format": "json"}

    geo_response = requests.get(geo_url, params=geo_params).json()

    if "results" not in geo_response:
        return f"Error: Could not find location for '{city}'."

    location = geo_response["results"][0]
    lat, lon = location["latitude"], location["longitude"]
    location_name = f"{location['name']}, {location.get('admin1', '')}, {location.get('country', '')}"

    # 2. Get current weather using coordinates
    weather_url = "https://api.open-meteo.com/v1/forecast"
    weather_params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        "temperature_unit": "fahrenheit",  # Change to "celsius" if preferred
        "wind_speed_unit": "mph",  # Change to "kmh" if preferred
    }

    weather_response = requests.get(weather_url, params=weather_params).json()

    if "current_weather" in weather_response:
        current = weather_response["current_weather"]
        temp = current["temperature"]
        wind = current["windspeed"]
        return f"Weather in {location_name}:\nTemperature: {temp}°F\nWind Speed: {wind} mph"
    else:
        return "Error: Could not retrieve weather data."


if __name__ == "__main__":
    city_input = input("Enter a city name:")
    print("\n" + get_weather(city_input))
