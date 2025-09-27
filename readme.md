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