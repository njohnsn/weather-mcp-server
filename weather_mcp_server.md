# Weather MCP Server - Complete Implementation

## SECTION 1: FILES TO CREATE

### File 1: Dockerfile

```dockerfile
# Use Python slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set Python unbuffered mode
ENV PYTHONUNBUFFERED=1

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server code
COPY weather_server.py .

# Create non-root user
RUN useradd -m -u 1000 mcpuser && \
    chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Run the server
CMD ["python", "weather_server.py"]
```

### File 2: requirements.txt

```
mcp[cli]>=1.2.0
httpx
```

### File 3: weather_server.py

```python
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
• Condition: {weather.get("description", "").title()}
• Temperature: {temp}{temp_symbol} (feels like {feels_like}{temp_symbol})
• Range: {temp_min}{temp_symbol} - {temp_max}{temp_symbol}
• Humidity: {main.get("humidity", 0)}%
• Wind: {wind.get("speed", 0)} m/s
• Pressure: {main.get("pressure", 0)} hPa"""

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
```

### File 4: readme.txt

```markdown
# Weather MCP Server

A Model Context Protocol (MCP) server that provides weather information using the OpenWeather API.

## Purpose

This MCP server provides a secure interface for AI assistants to get current weather conditions, 5-day forecasts, and perform temperature conversions.

## Features

### Current Implementation

- **`get_current_weather`** - Get current weather conditions for any city with temperature, humidity, wind, and pressure
- **`get_weather_forecast`** - Get detailed 5-day weather forecast with 3-hour intervals
- **`convert_temperature`** - Convert temperatures between Celsius and Fahrenheit

## Prerequisites

- Docker Desktop with MCP Toolkit enabled
- Docker MCP CLI plugin (`docker mcp` command)
- OpenWeather API key (free at https://openweathermap.org/api)

## Installation

See the step-by-step instructions provided with the files.

## Usage Examples

In Claude Desktop, you can ask:

- "What's the weather like in New York?"
- "Show me the 5-day forecast for London in Fahrenheit"
- "Convert 25 degrees Celsius to Fahrenheit"
- "What's the current temperature in Tokyo?"
- "Give me the weather forecast for Paris this week"

## Architecture

```
Claude Desktop → MCP Gateway → Weather MCP Server → OpenWeather API
                     ↓
           Docker Desktop Secrets
              (OPENWEATHER_API_KEY)
```

## Development

### Local Testing

```bash
# Set environment variables for testing
export OPENWEATHER_API_KEY="your-api-key-here"

# Run directly
python weather_server.py

# Test MCP protocol
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python weather_server.py
```

### Adding New Tools

1. Add the function to `weather_server.py`
2. Decorate with `@mcp.tool()`
3. Update the catalog entry with the new tool name
4. Rebuild the Docker image

## Troubleshooting

### Tools Not Appearing

- Verify Docker image built successfully
- Check catalog and registry files
- Ensure Claude Desktop config includes custom catalog
- Restart Claude Desktop

### Authentication Errors

- Verify API key with `docker mcp secret list`
- Ensure secret name matches in code and catalog
- Test API key at https://openweathermap.org/api

### API Errors

- 401: Invalid API key
- 404: City not found
- Rate limits: Free tier allows 60 calls/minute, 1,000,000 calls/month

## Security Considerations

- API key stored in Docker Desktop secrets
- Never hardcode credentials
- Running as non-root user
- Sensitive data never logged

## License

MIT License
```

### File 5: CLAUDE.md

```markdown
# Weather MCP Server Implementation Guide

## Overview

This Weather MCP server provides three main weather-related tools for Claude Desktop using the OpenWeather API.

## Tool Specifications

### get_current_weather
- **Purpose**: Get current weather conditions for any city
- **Parameters**: 
  - `city` (required): City name (e.g., "New York", "London, UK")
  - `unit` (optional): "celsius" or "fahrenheit" (default: celsius)
- **Returns**: Current temperature, conditions, humidity, wind, pressure
- **Example**: "What's the weather in Paris?"

### get_weather_forecast  
- **Purpose**: Get detailed 5-day weather forecast
- **Parameters**:
  - `city` (required): City name
  - `unit` (optional): "celsius" or "fahrenheit" (default: celsius)
- **Returns**: 5-day forecast with 3-hour intervals
- **Example**: "Show me the forecast for Tokyo in Fahrenheit"

### convert_temperature
- **Purpose**: Convert between Celsius and Fahrenheit
- **Parameters**:
  - `temperature` (required): Numeric temperature value
  - `from_unit` (optional): "celsius" or "fahrenheit" (default: celsius)  
  - `to_unit` (optional): "celsius" or "fahrenheit" (default: fahrenheit)
- **Returns**: Converted temperature with both values shown
- **Example**: "Convert 25 degrees Celsius to Fahrenheit"

## Implementation Details

### Error Handling
- Missing API key detection
- Invalid city names (404 responses)
- Network timeouts and connection errors
- Invalid temperature values for conversion
- Rate limiting (OpenWeather free tier: 60/min, 1M/month)

### Data Formatting
- Temperatures displayed with appropriate units (°C/°F)
- Weather conditions capitalized properly
- Forecast organized by day with time intervals
- Emojis used for visual clarity (🌤️, 📅, 🌡️)

### Security Features
- API key stored in Docker secrets, never hardcoded
- Input validation and sanitization
- Non-root container execution
- Proper error messages without exposing internals

## Natural Language Examples

Users can interact with the weather server naturally:

- "What's it like outside in Seattle?"
- "Will it rain in London tomorrow?"  
- "How hot is 30 Celsius in Fahrenheit?"
- "Give me the week's weather for Miami"
- "Is it cold in Moscow right now?"

The server handles various city name formats:
- "New York" or "New York, NY" or "New York, US"
- "London" or "London, UK" 
- International cities: "Tokyo", "Paris", "Sydney"

## API Integration

Uses OpenWeather API endpoints:
- Current weather: `/weather`
- 5-day forecast: `/forecast` 
- Free tier provides sufficient usage for most applications
- Responses include comprehensive weather data in JSON format

## Deployment Notes

- Container runs on port-agnostic stdio transport
- Logging configured to stderr for proper Docker integration
- Graceful error handling prevents server crashes
- Timezone-aware forecast formatting using local system time
```

---

## SECTION 2: INSTALLATION INSTRUCTIONS FOR THE USER

### Step 1: Save the Files

```bash
# Create project directory
mkdir weather-mcp-server
cd weather-mcp-server

# Save all 5 files in this directory:
# - Dockerfile
# - requirements.txt  
# - weather_server.py
# - readme.txt
# - CLAUDE.md
```

### Step 2: Build Docker Image

```bash
docker build -t weather-mcp-server .
```

### Step 3: Set Up Secrets

```bash
# Set your OpenWeather API key (get free key at https://openweathermap.org/api)
docker mcp secret set OPENWEATHER_API_KEY="your-api-key-here"

# Verify secrets
docker mcp secret list
```

### Step 4: Create Custom Catalog

```bash
# Create catalogs directory if it doesn't exist
mkdir -p ~/.docker/mcp/catalogs

# Create or edit custom.yaml
nano ~/.docker/mcp/catalogs/custom.yaml
```

Add this entry to custom.yaml:

```yaml
version: 2
name: custom
displayName: Custom MCP Servers
registry:
  weather:
    description: "Get current weather, forecasts, and convert temperatures using OpenWeather API"
    title: "Weather API"
    type: server
    dateAdded: "2025-09-23T00:00:00Z"
    image: weather-mcp-server:latest
    ref: ""
    readme: ""
    toolsUrl: ""
    source: ""
    upstream: ""
    icon: ""
    tools:
      - name: get_current_weather
      - name: get_weather_forecast
      - name: convert_temperature
    secrets:
      - name: OPENWEATHER_API_KEY
        env: OPENWEATHER_API_KEY
        example: "your-openweather-api-key"
    metadata:
      category: productivity
      tags:
        - weather
        - api
        - forecast
      license: MIT
      owner: local
```

### Step 5: Update Registry

```bash
# Edit registry file
nano ~/.docker/mcp/registry.yaml
```

Add this entry under the existing `registry:` key:

```yaml
registry:
  # ... existing servers ...
  weather:
    ref: ""
```

**IMPORTANT**: The entry must be under the `registry:` key, not at the root level.

### Step 6: Configure Claude Desktop

Find your Claude Desktop config file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`  
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

Edit the file and add your custom catalog to the args array:

```json
{
  "mcpServers": {
    "mcp-toolkit-gateway": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v", "/var/run/docker.sock:/var/run/docker.sock",
        "-v", "/Users/your_username/.docker/mcp:/mcp",
        "docker/mcp-gateway",
        "--catalog=/mcp/catalogs/docker-mcp.yaml",
        "--catalog=/mcp/catalogs/custom.yaml",
        "--config=/mcp/config.yaml",
        "--registry=/mcp/registry.yaml",
        "--tools-config=/mcp/tools.yaml",
        "--transport=stdio"
      ]
    }
  }
}
```

Replace `/Users/your_username` with:
- **macOS**: `/Users/your_username`
- **Windows**: `C:\\Users\\your_username` (use double backslashes)
- **Linux**: `/home/your_username`

### Step 7: Restart Claude Desktop

1. Quit Claude Desktop completely
2. Start Claude Desktop again  
3. Your weather tools should appear!

### Step 8: Test Your Server

```bash
# Verify it appears in the list
docker mcp server list

# If you don't see your server, check logs:
docker logs [container_name]
```

Now you can ask Claude things like:
- "What's the weather in New York?"
- "Show me the 5-day forecast for London"
- "Convert 25 degrees Celsius to Fahrenheit"

Your Weather MCP server is ready to use!