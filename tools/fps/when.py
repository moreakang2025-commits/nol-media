"""Publish times (US Eastern) for a given US date.  usage: when.py 2026-11-12 long|s1|s2|s3|s4  -> RFC3339 UTC
Long-form 10:00 ET (seniors' morning), Shorts spread through the afternoon and evening."""
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
SLOTS = {"long": "10:00", "s1": "12:30", "s2": "15:30", "s3": "18:30", "s4": "20:30"}

def at(date, slot):
    if not date or date == "-": return ""
    t = datetime.strptime(f"{date} {SLOTS[slot]}", "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo("America/New_York"))
    return t.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")

if __name__ == "__main__":
    print(at(sys.argv[1], sys.argv[2]))
