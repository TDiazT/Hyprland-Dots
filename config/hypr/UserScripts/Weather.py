#!/usr/bin/env python3
# /* ---- 💫 https://github.com/JaKooLit 💫 ---- */  #
# weather using python
#
# Fuente de datos: Open-Meteo (https://open-meteo.com) - gratis y sin API key.
# Antes esto scrapeaba weather.com, pero ese sitio pasó a renderizar los datos
# por JS: el HTML todavía llega, pero con los valores vacíos y sin #regionHeader,
# asi que no hay selector que arreglar. Los nombres de clase (sunnyDay,
# clearNight, ...) se mantienen porque el CSS de waybar los usa.

import json
import os

import requests

TIMEOUT = 20

# weather icons
weather_icons = {
    "sunnyDay": "󰖙",
    "clearNight": "󰖔",
    "cloudyFoggyDay": "",
    "cloudyFoggyNight": "",
    "rainyDay": "",
    "rainyNight": "",
    "snowyIcyDay": "",
    "snowyIcyNight": "",
    "severe": "",
    "default": "",
}

# WMO weather code -> (descripcion, familia de icono)
# https://open-meteo.com/en/docs -> "Weather variable documentation"
wmo_codes = {
    0: ("Clear", "sunny"),
    1: ("Mainly clear", "cloudyFoggy"),
    2: ("Partly cloudy", "cloudyFoggy"),
    3: ("Overcast", "cloudyFoggy"),
    45: ("Fog", "cloudyFoggy"),
    48: ("Rime fog", "cloudyFoggy"),
    51: ("Light drizzle", "rainy"),
    53: ("Drizzle", "rainy"),
    55: ("Heavy drizzle", "rainy"),
    56: ("Freezing drizzle", "snowyIcy"),
    57: ("Freezing drizzle", "snowyIcy"),
    61: ("Light rain", "rainy"),
    63: ("Rain", "rainy"),
    65: ("Heavy rain", "rainy"),
    66: ("Freezing rain", "snowyIcy"),
    67: ("Freezing rain", "snowyIcy"),
    71: ("Light snow", "snowyIcy"),
    73: ("Snow", "snowyIcy"),
    75: ("Heavy snow", "snowyIcy"),
    77: ("Snow grains", "snowyIcy"),
    80: ("Light showers", "rainy"),
    81: ("Showers", "rainy"),
    82: ("Violent showers", "rainy"),
    85: ("Snow showers", "snowyIcy"),
    86: ("Heavy snow showers", "snowyIcy"),
    95: ("Thunderstorm", "severe"),
    96: ("Thunderstorm, hail", "severe"),
    99: ("Thunderstorm, hail", "severe"),
}


def status_from_code(code, is_day):
    """Traduce el codigo WMO a (frase, clave de weather_icons)."""
    description, family = wmo_codes.get(code, ("Unknown", "default"))
    if family in ("sunny", "cloudyFoggy", "rainy", "snowyIcy"):
        suffix = "Day" if is_day else "Night"
        # no existe "sunnyNight": de noche el cielo despejado es clearNight
        key = "clearNight" if family == "sunny" and not is_day else family + suffix
    else:
        key = family
    return description, key if key in weather_icons else "default"


# Get current location based on IP address
def get_location():
    data = requests.get("https://ipinfo.io/json", timeout=TIMEOUT).json()
    latitude, longitude = data["loc"].split(",")
    return latitude, longitude


# NOTE: si preferis fijar la ubicacion a mano, reemplaza la llamada de abajo por
# tus coordenadas, p.ej.: latitude, longitude = "35.68", "139.69"


def get_weather(latitude, longitude):
    forecast = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,apparent_temperature,relative_humidity_2m,"
            "is_day,weather_code,wind_speed_10m",
            "hourly": "visibility,precipitation_probability",
            "daily": "temperature_2m_max,temperature_2m_min",
            "timezone": "auto",
            "forecast_days": 1,
        },
        timeout=TIMEOUT,
    ).json()

    # el AQI vive en otra API; si falla no queremos perder el resto del reporte
    try:
        air = requests.get(
            "https://air-quality-api.open-meteo.com/v1/air-quality",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": "european_aqi",
                "timezone": "auto",
            },
            timeout=TIMEOUT,
        ).json()
        aqi = air["current"]["european_aqi"]
    except Exception:
        aqi = None

    return forecast, aqi


def hourly_at_now(forecast, field):
    """Valor horario correspondiente a la hora actual (o el primero disponible)."""
    hourly = forecast.get("hourly", {})
    values = hourly.get(field) or []
    if not values:
        return None
    now = forecast.get("current", {}).get("time", "")[:13]  # YYYY-MM-DDTHH
    for index, stamp in enumerate(hourly.get("time", [])):
        if stamp[:13] == now:
            return values[index]
    return values[0]


def build_output():
    latitude, longitude = get_location()
    forecast, aqi = get_weather(latitude, longitude)

    current = forecast["current"]
    daily = forecast["daily"]

    is_day = bool(current["is_day"])
    status, status_code = status_from_code(current["weather_code"], is_day)
    icon = weather_icons[status_code]

    temp = f"{round(current['temperature_2m'])}°"
    temp_feel_text = f"Feels like {round(current['apparent_temperature'])}°"
    temp_min = f"{round(daily['temperature_2m_min'][0])}°"
    temp_max = f"{round(daily['temperature_2m_max'][0])}°"
    temp_min_max = f"  {temp_min}\t\t  {temp_max}"

    wind_text = f"  {round(current['wind_speed_10m'])} km/h"
    humidity_text = f"  {current['relative_humidity_2m']}%"

    visibility = hourly_at_now(forecast, "visibility")
    visibility_text = (
        f"  {round(visibility / 1000)} km" if visibility is not None else "  n/a"
    )

    air_quality_index = "n/a" if aqi is None else str(aqi)

    # probabilidad de lluvia en la hora actual
    chance = hourly_at_now(forecast, "precipitation_probability")
    prediction = f"\n\n (hourly) {chance}%" if chance else ""

    tooltip_text = str.format(
        "\t\t{}\t\t\n{}\n{}\n{}\n\n{}\n{}\n{}{}",
        f'<span size="xx-large">{temp}</span>',
        f"<big> {icon}</big>",
        f"<b>{status}</b>",
        f"<small>{temp_feel_text}</small>",
        f"<b>{temp_min_max}</b>",
        f"{wind_text}\t{humidity_text}",
        f"{visibility_text}\tAQI {air_quality_index}",
        f"<i> {prediction}</i>",
    )

    simple_weather = (
        f"{icon}  {status}\n"
        + f"  {temp} ({temp_feel_text})\n"
        + f"{wind_text} \n"
        + f"{humidity_text} \n"
        + f"{visibility_text} AQI{air_quality_index}\n"
    )

    out_data = {
        "text": f"{icon}  {temp}",
        "alt": status,
        "tooltip": tooltip_text,
        "class": status_code,
    }
    return out_data, simple_weather


# print waybar module data
# Ante un fallo de red o de la API imprimimos JSON valido igual: si el script
# revienta, waybar deja el modulo en blanco sin ninguna pista del motivo.
try:
    out_data, simple_weather = build_output()
except Exception as e:
    out_data = {
        "text": weather_icons["default"],
        "alt": "unavailable",
        "tooltip": f"Weather unavailable\n{e}",
        "class": "default",
    }
    simple_weather = None

print(json.dumps(out_data))

if simple_weather is not None:
    try:
        with open(os.path.expanduser("~/.cache/.weather_cache"), "w") as file:
            file.write(simple_weather)
    except Exception as e:
        print(f"Error writing to cache: {e}")
