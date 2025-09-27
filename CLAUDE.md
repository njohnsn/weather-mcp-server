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