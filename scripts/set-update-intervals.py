#!/usr/bin/env python3
"""Change Donut external-data refresh intervals without rebuilding the app."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def bounded(raw: str, name: str, minimum: int, maximum: int) -> int:
    try:
        value = int(raw)
    except ValueError as error:
        raise SystemExit(f"{name} must be an integer number of hours") from error
    if not minimum <= value <= maximum:
        raise SystemExit(f"{name} must be between {minimum} and {maximum} hours")
    return value


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: set-update-intervals.cmd <dns-hours> <geoip-hours>")

    dns_hours = bounded(sys.argv[1], "dns-hours", 1, 24 * 30)
    geoip_hours = bounded(sys.argv[2], "geoip-hours", 6, 24 * 30)
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        raise SystemExit("LOCALAPPDATA is not set")

    path = Path(local_app_data) / "DonutBrowser" / "data-update-policy.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(
            {
                "dns_refresh_hours": dns_hours,
                "geoip_refresh_hours": geoip_hours,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
    print(f"Updated {path}")
    print(f"DNS: {dns_hours}h; GeoIP: {geoip_hours}h")
    print("The running app will pick this up within 15 minutes; restart applies it immediately.")


if __name__ == "__main__":
    main()
