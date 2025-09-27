#!/usr/bin/env python3
"""
Weather MCP Server - Get current weather and forecasts using OpenWeather API
"""
import os
import sys
import logging
from datetime import datetime, timezone
import httpx
from mcp.server.fastmcp import FastMCP

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("weather-server")

# Initialize MCP server - NO PROMPT PARAMETER!
mcp = FastMCP("weather")

# Configuration
API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
BASE_URL = "https://api.openweathermap.org/data/2.5"

# === UTILITY FUNCTIONS ===

def format_temperature(temp_k, unit="celsius"):
    """Convert temperature from Kelvin to specified unit."""
    if unit.lower() == "fahrenheit":
        return round((temp_k - 273.15) * 9/5 + 32, 1)
    else:  # celsius
        return round(temp_k - 273.15, 1)

def format_weather_data(data, unit="celsius"):
    """Format weather data for display."""
    temp_symbol = "°F" if unit.lower() == "fahrenheit" else "°C"
    
    main = data.get("main", {})
    weather = data.get("weather", [{}])[0]
    wind = data.get("wind", {})
    
    temp = format_temperature(main.get("temp", 0), unit)
    feels_like = format_temperature(main.get("feels_like", 0), unit)
    temp_min = format_temperature(main.get("temp_min", 0), unit)
    temp_max = format_temperature(main.get("temp_max", 0), unit)
    
    return f"""🌤️ Weather for {data.get("name", "Unknown")}:
- Condition: {weather.get("description", "").title()}
- Temperature: {temp}{temp_symbol} (feels like {feels_like}{temp_symbol})
- Range: {temp_min}{temp_symbol} - {temp_max}{temp_symbol}
- Humidity: {main.get("humidity", 0)}%
- Wind: {wind.get("speed", 0)} m/s
- Pressure: {main.get("pressure", 0)} hPa"""

def format_forecast_data(data, unit="celsius"):
    """Format 5-day forecast data for display."""
    temp_symbol = "°F" if unit.lower() == "fahrenheit" else "°C"
    
    city_name = data.get("city", {}).get("name", "Unknown")
    forecasts = data.get("list", [])
    
    result = f"📅 5-Day Forecast for {city_name}:\n\n"
    
    current_date = ""
    for forecast in forecasts:
        dt = datetime.fromtimestamp(forecast.get("dt", 0))
        date_str = dt.strftime("%Y-%m-%d")
        time_str = dt.strftime("%H:%M")
        
        if date_str != current_date:
            if current_date:  # Add separator between days
                result += "\n"
            result += f"📆 {dt.strftime('%A, %B %d')}:\n"
            current_date = date_str
        
        main = forecast.get("main", {})
        weather = forecast.get("weather", [{}])[0]
        
        temp = format_temperature(main.get("temp", 0), unit)
        condition = weather.get("description", "").title()
        
        result += f"  {time_str}: {temp}{temp_symbol} - {condition}\n"
    
    return result.strip()

# === MCP TOOLS ===

@mcp.tool()
async def get_current_weather(city: str = "", unit: str = "celsius") -> str:
    """Get current weather for a city (unit can be celsius or fahrenheit)."""
    logger.info(f"Getting current weather for {city} in {unit}")
    
    if not API_KEY:
        return "❌ Error: OpenWeather API key not configured. Please set OPENWEATHER_API_KEY."
    
    if not city.strip():
        return "❌ Error: City name is required"
    
    if unit.lower() not in ["celsius", "fahrenheit"]:
        return "❌ Error: Unit must be 'celsius' or 'fahrenheit'"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/weather",
                params={
                    "q": city.strip(),
                    "appid": API_KEY
                },
                timeout=10
            )
            
            if response.status_code == 404:
                return f"❌ Error: City '{city}' not found"
            elif response.status_code == 401:
                return "❌ Error: Invalid API key"
            
            response.raise_for_status()
            data = response.json()
            
            return format_weather_data(data, unit)
            
    except httpx.HTTPStatusError as e:
        return f"❌ API Error: {e.response.status_code}"
    except Exception as e:
        logger.error(f"Error getting weather: {e}")
        return f"❌ Error: {str(e)}"

@mcp.tool()
async def get_weather_forecast(city: str = "", unit: str = "celsius") -> str:
    """Get 5-day weather forecast for a city (unit can be celsius or fahrenheit)."""
    logger.info(f"Getting forecast for {city} in {unit}")
    
    if not API_KEY:
        return "❌ Error: OpenWeather API key not configured. Please set OPENWEATHER_API_KEY."
    
    if not city.strip():
        return "❌ Error: City name is required"
    
    if unit.lower() not in ["celsius", "fahrenheit"]:
        return "❌ Error: Unit must be 'celsius' or 'fahrenheit'"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/forecast",
                params={
                    "q": city.strip(),
                    "appid": API_KEY
                },
                timeout=10
            )
            
            if response.status_code == 404:
                return f"❌ Error: City '{city}' not found"
            elif response.status_code == 401:
                return "❌ Error: Invalid API key"
            
            response.raise_for_status()
            data = response.json()
            
            return format_forecast_data(data, unit)
            
    except httpx.HTTPStatusError as e:
        return f"❌ API Error: {e.response.status_code}"
    except Exception as e:
        logger.error(f"Error getting forecast: {e}")
        return f"❌ Error: {str(e)}"

@mcp.tool()
async def convert_temperature(temperature: str = "", from_unit: str = "celsius", to_unit: str = "fahrenheit") -> str:
    """Convert temperature between Celsius and Fahrenheit."""
    logger.info(f"Converting {temperature} from {from_unit} to {to_unit}")
    
    if not temperature.strip():
        return "❌ Error: Temperature value is required"
    
    if from_unit.lower() not in ["celsius", "fahrenheit"]:
        return "❌ Error: from_unit must be 'celsius' or 'fahrenheit'"
    
    if to_unit.lower() not in ["celsius", "fahrenheit"]:
        return "❌ Error: to_unit must be 'celsius' or 'fahrenheit'"
    
    try:
        temp_value = float(temperature.strip())
        
        if from_unit.lower() == to_unit.lower():
            return f"🌡️ {temp_value}°{to_unit[0].upper()} = {temp_value}°{to_unit[0].upper()} (same unit)"
        
        if from_unit.lower() == "celsius" and to_unit.lower() == "fahrenheit":
            result = (temp_value * 9/5) + 32
            return f"🌡️ {temp_value}°C = {result:.1f}°F"
        
        elif from_unit.lower() == "fahrenheit" and to_unit.lower() == "celsius":
            result = (temp_value - 32) * 5/9
            return f"🌡️ {temp_value}°F = {result:.1f}°C"
            
    except ValueError:
        return f"❌ Error: Invalid temperature value: {temperature}"
    except Exception as e:
        logger.error(f"Error converting temperature: {e}")
        return f"❌ Error: {str(e)}"

# === SERVER STARTUP ===
if __name__ == "__main__":
    logger.info("Starting Weather MCP server...")
    
    if not API_KEY:
        logger.warning("OPENWEATHER_API_KEY not set - weather functions will not work")
    
    try:
        mcp.run(transport='stdio')
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)