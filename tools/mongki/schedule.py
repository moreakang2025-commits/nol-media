"""Publish slots (US audience). Long form 05:00 ET; Shorts 12:00, 17:00, 21:00 ET on the same US day.
usage: schedule.py <US date YYYY-MM-DD> long|short1|short2|short3 -> RFC3339 UTC (empty if in the past)"""
import datetime as dt, sys
from zoneinfo import ZoneInfo
SLOTS = {"long": 5, "short1": 12, "short2": 17, "short3": 21}

def slot(day, which):
    tz = ZoneInfo("America/New_York"); now = dt.datetime.now(dt.timezone.utc)
    t = dt.datetime.fromisoformat(day).replace(hour=SLOTS[which], tzinfo=tz)
    if t < now + dt.timedelta(minutes=30):
        if which != "long": return ""
        # missed the 05:00 ET slot: next full hour (>= 45 min ahead) on the same US day, before the first Short
        n = (now + dt.timedelta(minutes=45)).astimezone(tz)
        t = n.replace(minute=0, second=0, microsecond=0) + dt.timedelta(hours=1)
        if t.date().isoformat() != day or t.hour >= SLOTS["short1"]: return ""
    return t.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

if __name__ == "__main__":
    print(slot(sys.argv[1], sys.argv[2]))
