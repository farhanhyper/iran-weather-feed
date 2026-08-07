#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Fetch current weather for all 31 Iranian provinces and write weather.json.

Designed to run on GitHub Actions. It intentionally uses only Python's standard
library so the workflow has no pip dependency.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

PROVINCES = [
    ("آذربایجان شرقی", 38.0800, 46.2919),
    ("آذربایجان غربی", 37.5527, 45.0761),
    ("اردبیل", 38.2498, 48.2933),
    ("اصفهان", 32.6546, 51.6680),
    ("البرز", 35.8400, 50.9391),
    ("ایلام", 33.6374, 46.4227),
    ("بوشهر", 28.9234, 50.8203),
    ("تهران", 35.6892, 51.3890),
    ("چهارمحال و بختیاری", 32.3256, 50.8644),
    ("خراسان جنوبی", 32.8663, 59.2211),
    ("خراسان رضوی", 36.2605, 59.6168),
    ("خراسان شمالی", 37.4747, 57.3290),
    ("خوزستان", 31.3183, 48.6706),
    ("زنجان", 36.6736, 48.4787),
    ("سمنان", 35.5769, 53.3921),
    ("سیستان و بلوچستان", 29.4963, 60.8629),
    ("فارس", 29.5918, 52.5837),
    ("قزوین", 36.2688, 50.0041),
    ("قم", 34.6416, 50.8746),
    ("کردستان", 35.3219, 46.9862),
    ("کرمان", 30.2839, 57.0834),
    ("کرمانشاه", 34.3142, 47.0650),
    ("کهگیلویه و بویراحمد", 30.6682, 51.5870),
    ("گلستان", 36.8456, 54.4393),
    ("گیلان", 37.2808, 49.5832),
    ("لرستان", 33.4878, 48.3558),
    ("مازندران", 36.5633, 53.0601),
    ("مرکزی", 34.0917, 49.6892),
    ("هرمزگان", 27.1832, 56.2666),
    ("همدان", 34.7989, 48.5150),
    ("یزد", 31.8974, 54.3569),
]


def weather_description(code: int) -> str:
    if code == 0:
        return "صاف"
    if code == 1:
        return "عمدتاً صاف"
    if code == 2:
        return "نیمه ابری"
    if code == 3:
        return "ابری"
    if code in (45, 48):
        return "مه‌آلود"
    if code in (51, 53, 55):
        return "نم‌نم باران"
    if code in (56, 57, 66, 67):
        return "بارش یخ‌زن"
    if code == 61:
        return "باران خفیف"
    if code == 63:
        return "باران"
    if code == 65:
        return "باران شدید"
    if code == 71:
        return "برف خفیف"
    if code == 73:
        return "برف"
    if code in (75, 77):
        return "برف شدید"
    if code == 80:
        return "رگبار خفیف"
    if code == 81:
        return "رگبار"
    if code == 82:
        return "رگبار شدید"
    if code in (85, 86):
        return "رگبار برف"
    if code == 95:
        return "رعد و برق"
    if code in (96, 99):
        return "رعد و برق و تگرگ"
    return "نامشخص"


def finite_number(value, label: str) -> float:
    if not isinstance(value, (int, float)):
        raise ValueError(f"{label} is not numeric: {value!r}")
    return round(float(value), 1)


def build_url() -> str:
    latitudes = ",".join(str(p[1]) for p in PROVINCES)
    longitudes = ",".join(str(p[2]) for p in PROVINCES)
    current = "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
    return (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={quote(latitudes, safe=',.-')}"
        f"&longitude={quote(longitudes, safe=',.-')}"
        f"&current={quote(current, safe=',_')}"
        "&temperature_unit=celsius"
        "&wind_speed_unit=kmh"
        "&timezone=Asia%2FTehran"
    )


def fetch_json(url: str) -> object:
    req = Request(
        url,
        headers={
            "User-Agent": "ECOGaming-IranWeather-GitHubAction/1.0",
            "Accept": "application/json",
        },
    )
    with urlopen(req, timeout=30) as response:
        if response.status < 200 or response.status >= 300:
            raise RuntimeError(f"Open-Meteo returned HTTP {response.status}")
        return json.loads(response.read().decode("utf-8"))


def build_payload(raw: object) -> dict:
    if isinstance(raw, dict) and "current" in raw:
        locations = [raw]
    elif isinstance(raw, list):
        locations = raw
    else:
        raise ValueError("Unexpected Open-Meteo JSON structure")

    if len(locations) != len(PROVINCES):
        raise ValueError(
            f"Expected {len(PROVINCES)} locations, got {len(locations)}"
        )

    rows = []
    for index, ((name, lat, lon), location) in enumerate(zip(PROVINCES, locations)):
        if not isinstance(location, dict) or not isinstance(location.get("current"), dict):
            raise ValueError(f"Location #{index + 1} has no current weather")
        current = location["current"]
        code = int(current.get("weather_code", -1))
        rows.append(
            {
                "name": name,
                "latitude": lat,
                "longitude": lon,
                "condition_fa": weather_description(code),
                "weather_code": code,
                "temperature_c": finite_number(current.get("temperature_2m"), "temperature"),
                "humidity_percent": finite_number(current.get("relative_humidity_2m"), "humidity"),
                "wind_kmh": finite_number(current.get("wind_speed_10m"), "wind"),
                "observed_at": str(current.get("time", "")),
            }
        )

    now_utc = datetime.now(timezone.utc).replace(microsecond=0)
    now_iran = now_utc.astimezone(ZoneInfo("Asia/Tehran"))
    return {
        "schema_version": 1,
        "source": "Open-Meteo via GitHub Actions",
        "generated_at_utc": now_utc.isoformat().replace("+00:00", "Z"),
        "generated_at_iran": now_iran.strftime("%Y-%m-%d %H:%M"),
        "province_count": len(rows),
        "provinces": rows,
    }


def main() -> int:
    url = build_url()
    print(f"Fetching {len(PROVINCES)} provinces from Open-Meteo...")
    raw = fetch_json(url)
    payload = build_payload(raw)

    target = Path(__file__).resolve().parent / "weather.json"
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {target} with {len(payload['provinces'])} provinces")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
