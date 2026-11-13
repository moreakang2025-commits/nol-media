"""Publish times (US Eastern) for a given US date.  usage: when.py 2026-11-12 long|s1|s2|s3|s4  -> RFC3339 UTC
Long-form 10:00 ET (seniors' morning), Shorts spread through the afternoon and evening.
Slot experiment (from 2026-11-15): the four Shorts rotate through the four afternoon/evening times day by day,
so the stats can tell "which Short content works" apart from "which time works" (tools/fps/analyze.py)."""
import sys
from datetime import date as D, datetime
from zoneinfo import ZoneInfo
LONG = "10:00"
SHORT_TIMES = ["12:30", "15:30", "18:30", "20:30"]
ROTATE_FROM = D(2026, 11, 15)


def clock(date, slot):
    if slot == "long": return LONG
    i = int(slot[1]) - 1; d = D.fromisoformat(date)
    off = ((d - ROTATE_FROM).days + 1) % 4 if d >= ROTATE_FROM else 0
    return SHORT_TIMES[(i + off) % 4]


def at(date, slot):
    if not date or date == "-": return ""
    t = datetime.strptime(f"{date} {clock(date, slot)}", "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo("America/New_York"))
    return t.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")


if __name__ == "__main__":
    print(at(sys.argv[1], sys.argv[2]))
