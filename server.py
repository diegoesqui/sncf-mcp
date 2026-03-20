"""
Navitia MCP Server — French train search (SNCF data)
Compatible with any MCP client: Claude, Cursor, Copilot, etc.

Usage:
    python server.py

Requires NAVITIA_TOKEN environment variable (get it free at navitia.io/inscription)
"""

import os
import httpx
from datetime import datetime
from typing import Optional
from fastmcp import FastMCP

# ── Init ──────────────────────────────────────────────────────────────────────
mcp = FastMCP(
    name="sncf-trains",
    description="Search French train schedules (SNCF/TGV/TER) via the SNCF API",
)

SNCF_BASE = "https://api.sncf.com/v1/coverage/sncf"


def get_token() -> str:
    token = os.getenv("NAVITIA_TOKEN", "")
    if not token:
        raise ValueError(
            "NAVITIA_TOKEN not set. Get a free token at https://navitia.io/inscription"
        )
    return token


def navitia_get(path: str, params: dict = {}) -> dict:
    """Make an authenticated GET request to the Navitia API (Basic Auth)."""
    # El token se usa como nombre de usuario, con contraseña vacía.
    auth = (get_token(), "")
    url = f"{SNCF_BASE}{path}"
    response = httpx.get(url, auth=auth, params=params, timeout=15)
    response.raise_for_status()
    return response.json()


# ── Helpers ───────────────────────────────────────────────────────────────────

def fmt_duration(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h}h{m:02d}" if h else f"{m} min"


def fmt_navitia_time(dt_str: str) -> str:
    """Convert Navitia datetime (20260813T090000) to readable HH:MM."""
    if not dt_str:
        return "?"
    try:
        return datetime.strptime(dt_str, "%Y%m%dT%H%M%S").strftime("%H:%M")
    except Exception:
        return dt_str


def fmt_navitia_datetime(dt_str: str) -> str:
    """Convert Navitia datetime to readable DD/MM HH:MM."""
    if not dt_str:
        return "?"
    try:
        return datetime.strptime(dt_str, "%Y%m%dT%H%M%S").strftime("%d/%m %H:%M")
    except Exception:
        return dt_str


def parse_input_datetime(date_str: str, time_str: str) -> str:
    """Parse user date/time inputs to Navitia format YYYYMMDDTHHmmss."""
    # Accept: "2026-08-13", "13/08/2026", "13-08-2026"
    date_str = date_str.strip().replace("/", "-")
    parts = date_str.split("-")
    if len(parts[0]) == 4:  # YYYY-MM-DD
        year, month, day = parts
    else:                   # DD-MM-YYYY
        day, month, year = parts

    # Accept: "09:00", "9h00", "0900", "9"
    time_str = time_str.strip().replace("h", ":").replace("H", ":")
    if ":" in time_str:
        h, m = time_str.split(":")
    elif len(time_str) == 4:
        h, m = time_str[:2], time_str[2:]
    else:
        h, m = time_str, "00"

    return f"{year}{month.zfill(2)}{day.zfill(2)}T{h.zfill(2)}{m.zfill(2)}00"


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool()
def search_station(name: str) -> str:
    """
    Search for a French train station by name.
    Returns a list of matching stations with their IDs.

    Args:
        name: Station name to search (e.g. "Toulouse", "Marseille Saint-Charles")
    """
    data = navitia_get("/places", {"q": name, "type[]": "stop_area", "count": 8})
    places = data.get("places", [])

    if not places:
        return f"No station found for '{name}'. Try a different spelling."

    lines = [f"Stations matching '{name}':\n"]
    for p in places:
        sa = p.get("stop_area", {})
        station_name = sa.get("name") or p.get("name", "?")
        station_id = p.get("id", "?")
        lines.append(f"  • {station_name}\n    ID: {station_id}")

    return "\n".join(lines)


@mcp.tool()
def search_trains(
    from_station: str,
    to_station: str,
    date: str,
    time: str = "08:00",
    results: int = 6,
) -> str:
    """
    Search for trains between two French stations on a given date.
    Returns schedules with departure/arrival times, duration and train type.

    Args:
        from_station: Departure station name (e.g. "Toulouse") or Navitia ID
        to_station:   Arrival station name (e.g. "Marseille") or Navitia ID
        date:         Travel date. Formats accepted: "2026-08-13", "13/08/2026"
        time:         Earliest departure time. Formats: "09:00", "9h00". Default: "08:00"
        results:      Number of journeys to return (default: 6, max: 10)
    """

    # Resolve station names to IDs if needed
    def resolve_id(station: str) -> tuple[str, str]:
        """Returns (navitia_id, display_name)."""
        if station.startswith("stop_area:"):
            return station, station
        data = navitia_get("/places", {"q": station, "type[]": "stop_area", "count": 1})
        places = data.get("places", [])
        if not places:
            raise ValueError(f"Station not found: '{station}'")
        p = places[0]
        name = p.get("stop_area", {}).get("name") or p.get("name", station)
        return p["id"], name

    from_id, from_name = resolve_id(from_station)
    to_id, to_name = resolve_id(to_station)
    navitia_dt = parse_input_datetime(date, time)

    data = navitia_get(
        "/journeys",
        {
            "from": from_id,
            "to": to_id,
            "datetime": navitia_dt,
            "count": min(results, 10),
            "data_freshness": "realtime",
        },
    )

    journeys = data.get("journeys", [])
    if not journeys:
        return (
            f"No trains found from {from_name} to {to_name} on {date} after {time}.\n"
            "Try an earlier time or a different date."
        )

    lines = [
        f"🚄 Trains from {from_name} → {to_name}",
        f"📅 {date} · from {time}\n",
    ]

    for i, j in enumerate(journeys, 1):
        dep = fmt_navitia_datetime(j.get("departure_date_time", ""))
        arr = fmt_navitia_datetime(j.get("arrival_date_time", ""))
        dur = fmt_duration(j.get("duration", 0))
        transfers = j.get("nb_transfers", 0)
        transfer_label = "Direct" if transfers == 0 else f"{transfers} change(s)"

        # Collect train lines used
        train_modes = []
        for s in j.get("sections", []):
            if s.get("type") == "public_transport":
                di = s.get("display_informations", {})
                mode = di.get("commercial_mode") or di.get("physical_mode", "Train")
                label = di.get("label") or di.get("code", "")
                from_stop = s.get("from", {}).get("name", "")
                to_stop = s.get("to", {}).get("name", "")
                train_modes.append(f"{mode}{' '+label if label else ''} ({from_stop} → {to_stop})")

        trains_str = " + ".join(train_modes) if train_modes else "Train"

        lines.append(
            f"  {i}. {dep} → {arr}  [{dur}]  {transfer_label}\n"
            f"     {trains_str}"
        )

    lines.append(
        "\n💡 Tip: Use search_trains_detailed() for full section-by-section breakdown."
    )
    return "\n".join(lines)


@mcp.tool()
def search_trains_detailed(
    from_station: str,
    to_station: str,
    date: str,
    time: str = "08:00",
    journey_index: int = 1,
) -> str:
    """
    Get full step-by-step details of a specific train journey,
    including all stops, platform info, and connections.

    Args:
        from_station:   Departure station name or Navitia ID
        to_station:     Arrival station name or Navitia ID
        date:           Travel date (e.g. "2026-08-13" or "13/08/2026")
        time:           Earliest departure time (e.g. "09:00")
        journey_index:  Which journey to detail (1 = first result, etc.)
    """

    def resolve_id(station: str) -> tuple[str, str]:
        if station.startswith("stop_area:"):
            return station, station
        data = navitia_get("/places", {"q": station, "type[]": "stop_area", "count": 1})
        places = data.get("places", [])
        if not places:
            raise ValueError(f"Station not found: '{station}'")
        p = places[0]
        name = p.get("stop_area", {}).get("name") or p.get("name", station)
        return p["id"], name

    from_id, from_name = resolve_id(from_station)
    to_id, to_name = resolve_id(to_station)
    navitia_dt = parse_input_datetime(date, time)

    data = navitia_get(
        "/journeys",
        {
            "from": from_id,
            "to": to_id,
            "datetime": navitia_dt,
            "count": journey_index + 1,
            "data_freshness": "realtime",
        },
    )

    journeys = data.get("journeys", [])
    if not journeys or journey_index > len(journeys):
        return f"Journey #{journey_index} not found. Try a lower index."

    j = journeys[journey_index - 1]
    dep = fmt_navitia_datetime(j.get("departure_date_time", ""))
    arr = fmt_navitia_datetime(j.get("arrival_date_time", ""))
    dur = fmt_duration(j.get("duration", 0))

    lines = [
        f"🚄 Journey #{journey_index}: {from_name} → {to_name}",
        f"   Departs {dep} · Arrives {arr} · Total: {dur}\n",
        "── Itinerary ─────────────────────────────────────",
    ]

    for s in j.get("sections", []):
        stype = s.get("type", "")

        if stype == "public_transport":
            di = s.get("display_informations", {})
            mode = di.get("commercial_mode") or di.get("physical_mode", "Train")
            label = di.get("label") or di.get("code", "")
            direction = di.get("direction", "")
            dep_stop = s.get("from", {}).get("name", "?")
            arr_stop = s.get("to", {}).get("name", "?")
            dep_t = fmt_navitia_time(s.get("departure_date_time", ""))
            arr_t = fmt_navitia_time(s.get("arrival_date_time", ""))
            dur_s = fmt_duration(s.get("duration", 0))
            headsign = di.get("headsign", "")

            lines.append(
                f"\n🚆 {mode} {label}\n"
                f"   Direction: {direction or headsign or '—'}\n"
                f"   {dep_t} {dep_stop}\n"
                f"   {arr_t} {arr_stop}  [{dur_s}]"
            )

            # Intermediate stops (if available)
            stop_times = s.get("stop_date_times", [])
            if len(stop_times) > 2:
                lines.append(f"   Stops ({len(stop_times)-2} intermediate):")
                for st in stop_times[1:-1]:
                    t = fmt_navitia_time(st.get("departure_date_time", ""))
                    n = st.get("stop_point", {}).get("name", "?")
                    lines.append(f"     · {t} {n}")

        elif stype == "transfer":
            dur_s = fmt_duration(s.get("duration", 0))
            lines.append(f"\n🔄 Correspondance / Transfer  [{dur_s}]")

        elif stype == "street_network":
            dur_s = fmt_duration(s.get("duration", 0))
            mode = s.get("mode", "walking")
            lines.append(f"\n🚶 {mode.capitalize()}  [{dur_s}]")

    return "\n".join(lines)


@mcp.tool()
def next_departures(
    from_station: str,
    to_station: str,
    date: str,
    count: int = 8,
) -> str:
    """
    List the next departures for an entire day between two stations.
    Useful to get a full day overview of available trains.

    Args:
        from_station: Departure station (e.g. "Toulouse")
        to_station:   Arrival station (e.g. "Marseille")
        date:         Date (e.g. "2026-08-13" or "13/08/2026")
        count:        Number of results (default: 8)
    """
    return search_trains(
        from_station=from_station,
        to_station=to_station,
        date=date,
        time="05:00",
        results=count,
    )


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run(transport="stdio")
