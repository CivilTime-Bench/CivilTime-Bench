#!/usr/bin/env python3
"""
generate_data.py

Generator for CivilTime-Benchmark dataset covering:
OFFSET, DATE_LINE, DST_SKIP, DST_REPEAT, DST_AMBIG, BUSINESS_DAY,
CONSTRAINTS, RELATIVE_DAY, INTERVAL, ISO_WEEK, WEEKSTART.

Usage:
  python generate_data.py --output dataset.jsonl --total 2000 --seed 42
"""
import argparse
import json
import math
import random
from datetime import datetime, timedelta, date
import pytz
import calendar
from pathlib import Path

# --------------------- Helpers ---------------------

def fmt_iso(dt):
    """Canonical ISO with ±HH:MM offsets or 'Z' for UTC."""
    dt = dt.replace(microsecond=0)
    s = dt.isoformat()
    if s.endswith("+0000") or s.endswith("-0000"):
        s = s[:-5] + "Z"
    return s

def safe_localize(tz_obj, naive_dt, is_dst=None):
    """Localize using pytz. Handles NonExistentTimeError and AmbiguousTimeError."""
    try:
        if is_dst is None:
            return tz_obj.localize(naive_dt)
        else:
            return tz_obj.localize(naive_dt, is_dst=is_dst)
    except pytz.NonExistentTimeError:
        # Shift forward until valid
        for i in range(1, 180):
            try:
                return tz_obj.localize(naive_dt + timedelta(minutes=i))
            except pytz.NonExistentTimeError:
                continue
        raise
    except pytz.AmbiguousTimeError:
        if is_dst is None:
            dt_a = tz_obj.localize(naive_dt, is_dst=True)
            dt_b = tz_obj.localize(naive_dt, is_dst=False)
            return (dt_a, dt_b)
        else:
            return tz_obj.localize(naive_dt, is_dst=is_dst)

def add_business_days(d, n):
    step = 1 if n >= 0 else -1
    left = abs(n)
    cur = d
    while left:
        cur = cur + timedelta(days=step)
        if cur.weekday() < 5:
            left -= 1
    return cur

def iso_week_str(d):
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"

def safe_day(year, month, start=1, end=31):
    """Return a random valid day of month within [start,end]."""
    last = calendar.monthrange(year, month)[1]
    if end > last:
        end = last
    if start > end:
        start = end
    return random.randint(start, end)

# --------------------- Generator class ---------------------

class TimeDatasetGenerator:
    def __init__(self, seed=42):
        random.seed(seed)
        self.counter = 0
        self.timezones = {
            'Asia': ['Asia/Kathmandu', 'Asia/Tokyo', 'Asia/Dubai', 'Asia/Seoul'],
            'Europe': ['Europe/London', 'Europe/Paris', 'Europe/Moscow', 'Europe/Berlin'],
            'America': ['America/New_York', 'America/Los_Angeles', 'America/Chicago', 'America/Sao_Paulo'],
            'Australia': ['Australia/Sydney', 'Australia/Melbourne', 'Australia/Perth', 'Australia/Lord_Howe'],
            'Pacific': ['Pacific/Chatham', 'Pacific/Honolulu', 'Pacific/Auckland', 'Pacific/Kiritimati']
        }
        self.dst_candidates = ['Europe/London', 'America/New_York', 'Australia/Sydney', 'Australia/Lord_Howe']
        self.sample_years = [2024, 2025, 2026]

    def _next_id(self, prefix):
        self.counter += 1
        return f"{prefix}_{self.counter:06d}"

    def gen_offset(self):
        region = random.choice(list(self.timezones.keys()))
        tz = random.choice(self.timezones[region])
        year = random.choice(self.sample_years)
        month = random.choice([3, 4, 10])
        day = safe_day(year, month, 1, 31)
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        minutes_to_add = random.choice([15, 30, 45, 60, 90, 120, 180])
        naive = datetime(year, month, day, hour, minute)
        input_text = f"Start {naive.strftime('%Y-%m-%d %H:%M')} in {tz}, add {minutes_to_add} minutes. Return ISO-8601 with offset."
        tzobj = pytz.timezone(tz)
        start = safe_localize(tzobj, naive, is_dst=None)
        if isinstance(start, tuple):
            start = start[0]
        end = start + timedelta(minutes=minutes_to_add)
        return {"id": self._next_id("OFFSET"), "type": "OFFSET", "tz": tz, "input_text": input_text, "gold": fmt_iso(end)}

    def gen_date_line(self):
        src = random.choice(['Pacific/Honolulu', 'Pacific/Apia', 'Pacific/Tongatapu'])
        dst = random.choice(['Pacific/Kiritimati', 'Pacific/Tarawa', 'Pacific/Fakaofo'])
        year = 2025
        month = 12
        day = safe_day(year, month, 28, 31)
        hour = random.randint(22, 23)
        minute = random.randint(0, 59)
        minutes_to_add = random.choice([60, 70, 90, 120, 200])
        naive = datetime(year, month, day, hour, minute)
        input_text = f"From {src} at {naive.strftime('%Y-%m-%d %H:%M')}, add {minutes_to_add} minutes and give the ISO-8601 time in {dst}."
        tz_src = pytz.timezone(src)
        tz_dst = pytz.timezone(dst)
        start_utc = tz_src.localize(naive).astimezone(pytz.UTC)
        end_utc = start_utc + timedelta(minutes=minutes_to_add)
        end_local = end_utc.astimezone(tz_dst)
        return {"id": self._next_id("DATE_LINE"), "type": "DATE_LINE", "tz_src": src, "tz_dst": dst, "input_text": input_text, "gold": fmt_iso(end_local)}

    def gen_dst_skip(self):
        tz = random.choice(self.dst_candidates)
        year = random.choice(self.sample_years)
        month = random.choice([3, 4, 10])
        day = safe_day(year, month, 25, 31)
        hour = random.choice([1, 2])
        minute = random.randint(0, 59)
        minutes_to_add = random.choice([30, 60, 90])
        naive = datetime(year, month, day, hour, minute)
        input_text = f"Start {naive.strftime('%Y-%m-%d %H:%M')} in {tz}, add {minutes_to_add} minutes. Return ISO-8601 with offset."
        tzobj = pytz.timezone(tz)
        start = safe_localize(tzobj, naive, is_dst=None)
        if isinstance(start, tuple):
            start = start[0]
        end = start + timedelta(minutes=minutes_to_add)
        return {"id": self._next_id("DST_SKIP"), "type": "DST_SKIP", "tz": tz, "input_text": input_text, "gold": fmt_iso(end)}

    def gen_dst_repeat(self, occurrence=None):
        tz = random.choice(['Europe/London', 'America/New_York', 'Australia/Lord_Howe'])
        year = random.choice(self.sample_years)
        month = 10 if ('London' in tz or 'New_York' in tz) else 4
        day = safe_day(year, month, 25, 27)
        hour = 1
        minute = random.randint(0, 59)
        minutes_to_add = random.choice([60, 120, 180])
        naive = datetime(year, month, day, hour, minute)
        occ_text = 'occurrence unspecified' if occurrence is None else ('first' if occurrence == 1 else 'second')
        input_text = f"Start {naive.strftime('%Y-%m-%d %H:%M')} ({occ_text}) in {tz}, add {minutes_to_add} minutes. Return ISO-8601."
        tzobj = pytz.timezone(tz)
        if occurrence == 1:
            start = tzobj.localize(naive, is_dst=True)
        elif occurrence == 2:
            start = tzobj.localize(naive, is_dst=False)
        else:
            start = tzobj.localize(naive, is_dst=False)
        end = start + timedelta(minutes=minutes_to_add)
        return {"id": self._next_id("DST_REPEAT"), "type": "DST_REPEAT", "tz": tz, "input_text": input_text, "gold": fmt_iso(end)}

    def gen_dst_ambig(self, policy="A||B"):
        tz = random.choice(['Europe/London', 'America/New_York'])
        year = random.choice(self.sample_years)
        month = 10
        day = safe_day(year, month, 25, 26)
        hour = 1
        minute = random.randint(15, 59)
        naive = datetime(year, month, day, hour, minute)
        input_text = f"Start {naive.strftime('%Y-%m-%d %H:%M')} in {tz}. If ambiguous, return BOTH valid instants as A||B (ISO-8601); for ABSTAIN policy return ABSTAIN."
        tzobj = pytz.timezone(tz)
        dt_dst = tzobj.localize(naive, is_dst=True)
        dt_std = tzobj.localize(naive, is_dst=False)
        gold = f"{fmt_iso(dt_dst)}||{fmt_iso(dt_std)}" if policy == "A||B" else "ABSTAIN"
        return {"id": self._next_id("DST_AMBIG"), "type": "DST_AMBIG", "tz": tz, "input_text": input_text, "gold": gold}

    def gen_business_day(self):
        tz = random.choice(['America/New_York', 'Europe/London', 'Asia/Tokyo'])
        year = random.choice(self.sample_years)
        month = random.randint(1, 12)
        day = safe_day(year, month, 1, 28)
        hour = random.randint(16, 18)
        minute = random.randint(0, 59)
        business_days_to_add = random.randint(5, 15)
        naive = datetime(year, month, day, hour, minute)
        input_text = f"Next business day after {naive.strftime('%Y-%m-%d %H:%M')} in {tz}, then add {business_days_to_add} business days, set 09:00 local; return ISO."
        tzobj = pytz.timezone(tz)
        start = tzobj.localize(naive)
        dt_date = start.date()
        next_bd = dt_date + timedelta(days=1)
        while next_bd.weekday() >= 5:
            next_bd += timedelta(days=1)
        target_date = add_business_days(next_bd, business_days_to_add - 1)
        target_dt = datetime(target_date.year, target_date.month, target_date.day, 9, 0)
        target_dt = tzobj.localize(target_dt)
        return {"id": self._next_id("BUSINESS"), "type": "BUSINESS_DAY", "tz": tz, "input_text": input_text, "gold": fmt_iso(target_dt)}

    def gen_relative_day(self):
        tz = random.choice(['Europe/London', 'America/New_York', 'Asia/Tokyo'])
        anchor_year = random.choice(self.sample_years)
        anchor_month = random.randint(1, 12)
        anchor_day = safe_day(anchor_year, anchor_month, 1, 28)
        anchor = date(anchor_year, anchor_month, anchor_day)
        phrase = random.choice(["next Monday", "this Monday", "the Monday after next", "two Fridays from now"])
        def nth_weekday_after(anchor_date, weekday, n):
            cur = anchor_date
            count = 0
            while True:
                cur += timedelta(days=1)
                if cur.weekday() == weekday:
                    count += 1
                    if count == n:
                        return cur
        if phrase == "next Monday":
            target = nth_weekday_after(anchor, 0, 1)
        elif phrase == "this Monday":
            monday_of_week = anchor - timedelta(days=anchor.weekday())
            target = monday_of_week if monday_of_week >= anchor else monday_of_week + timedelta(days=7)
        elif phrase == "the Monday after next":
            target = nth_weekday_after(anchor, 0, 2)
        else:
            target = nth_weekday_after(anchor, 4, 2)
        local_dt = datetime(target.year, target.month, target.day, 9, 0)
        tzobj = pytz.timezone(tz)
        aware = tzobj.localize(local_dt)
        input_text = f"Anchor {anchor.strftime('%Y-%m-%d')}. Schedule '{phrase}' at 09:00 in {tz}. Return ISO-8601."
        return {"id": self._next_id("RELATIVE"), "type": "RELATIVE_DAY", "tz": tz, "input_text": input_text, "gold": fmt_iso(aware)}

    def gen_constraints(self):
        tz = random.choice(['Europe/London', 'America/New_York', 'Asia/Tokyo', 'Australia/Sydney'])
        year = random.choice(self.sample_years)
        month = random.randint(1, 11)
        target_month = month + 1 if month < 12 else 1
        target_year = year if month < 12 else year + 1
        base = date(target_year, target_month, 15)
        cur = base + timedelta(days=1)
        while cur.weekday() >= 5:
            cur += timedelta(days=1)
        local_dt = datetime(cur.year, cur.month, cur.day, 9, 0)
        tzobj = pytz.timezone(tz)
        aware = tzobj.localize(local_dt)
        input_text = f"In {tz}, schedule the first weekday after the 15th of {target_year}-{target_month:02d} at 09:00. If DST changes that day, honor the new offset. Return ISO."
        return {"id": self._next_id("CONSTRAINTS"), "type": "CONSTRAINTS", "tz": tz, "input_text": input_text, "gold": fmt_iso(aware)}

    def gen_interval(self):
        tz = random.choice(['America/New_York', 'Europe/London'])
        year = random.choice(self.sample_years)
        month = random.randint(1, 12)
        day = safe_day(year, month, 1, 28)
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        duration = random.choice([90, 135, 165, 195, 240])
        naive = datetime(year, month, day, hour, minute)
        input_text = f"Create a half-open interval [start,end) for a {duration}-minute event starting {naive.strftime('%Y-%m-%d %H:%M')} in {tz}. Return 'start||end' (ISO-8601 with offsets)."
        tzobj = pytz.timezone(tz)
        start = safe_localize(tzobj, naive, is_dst=None)
        if isinstance(start, tuple):
            start = start[0]
        end = start + timedelta(minutes=duration)
        return {"id": self._next_id("INTERVAL"), "type": "INTERVAL", "tz": tz, "input_text": input_text, "gold": f"{fmt_iso(start)}||{fmt_iso(end)}"}

    def gen_iso_week(self):
        candidate_dates = [date(2018, 12, 31), date(2020, 12, 31), date(2025, 1, 1), date(2015, 1, 1)]
        d = random.choice(candidate_dates)
        input_text = f"What is the ISO week number and week-year for {d.strftime('%Y-%m-%d')}? Return 'YYYY-Www'."
        return {"id": self._next_id("ISO_WEEK"), "type": "ISO_WEEK", "input_text": input_text, "gold": iso_week_str(d)}

    def gen_weekstart(self):
        d = date(2025, 6, 1)
        input_text = f"From {d.strftime('%Y-%m-%d')}, with week_start=Sunday, return the start_of_week date (YYYY-MM-DD)."
        return {"id": self._next_id("WEEKSTART"), "type": "WEEKSTART", "input_text": input_text, "gold": d.strftime('%Y-%m-%d')}

# --------------------- Orchestration ---------------------

def generate_counts(counts, seed=42, outpath="dataset.jsonl"):
    gen = TimeDatasetGenerator(seed=seed)
    total = sum(counts.values())
    print(f"Generating {total} items -> {outpath}")
    
    outpath = Path(outpath)
    outpath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(outpath, "w", encoding="utf-8") as fout:
        for typ, cnt in counts.items():
            for _ in range(cnt):
                if typ == "OFFSET":
                    q = gen.gen_offset()
                elif typ == "DATE_LINE":
                    q = gen.gen_date_line()
                elif typ == "DST_SKIP":
                    q = gen.gen_dst_skip()
                elif typ == "DST_REPEAT_occ1":
                    q = gen.gen_dst_repeat(occurrence=1)
                elif typ == "DST_REPEAT_occ2":
                    q = gen.gen_dst_repeat(occurrence=2)
                elif typ == "DST_AMBIG_AorB":
                    q = gen.gen_dst_ambig(policy="A||B")
                elif typ == "DST_AMBIG_ABSTAIN":
                    q = gen.gen_dst_ambig(policy="ABSTAIN")
                elif typ == "BUSINESS_DAY":
                    q = gen.gen_business_day()
                elif typ == "RELATIVE_DAY":
                    q = gen.gen_relative_day()
                elif typ == "CONSTRAINTS":
                    q = gen.gen_constraints()
                elif typ == "INTERVAL":
                    q = gen.gen_interval()
                elif typ == "ISO_WEEK":
                    q = gen.gen_iso_week()
                elif typ == "WEEKSTART":
                    q = gen.gen_weekstart()
                else:
                    raise ValueError(f"Unknown type: {typ}")
                fout.write(json.dumps(q, ensure_ascii=False) + "\n")
    print("Done.")

# --------------------- CLI ---------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate CivilTime Benchmark Dataset")
    parser.add_argument("--output", type=str, required=True, help="Output JSONL path")
    parser.add_argument("--total", type=int, default=2000, help="Total number of samples")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    target_proportions = {
        "OFFSET": 0.24,
        "DATE_LINE": 0.06,
        "DST_SKIP": 0.06,
        "DST_REPEAT_occ1": 0.06,
        "DST_REPEAT_occ2": 0.06,
        "DST_AMBIG_AorB": 0.08,
        "DST_AMBIG_ABSTAIN": 0.02,
        "BUSINESS_DAY": 0.08,
        "CONSTRAINTS": 0.08,
        "RELATIVE_DAY": 0.03,
        "INTERVAL": 0.02,
        "ISO_WEEK": 0.01,
        "WEEKSTART": 0.01
    }

    total = args.total
    counts = {k: max(1, int(math.floor(v * total))) for k, v in target_proportions.items()}
    diff = total - sum(counts.values())
    keys = list(counts.keys())
    i = 0
    while diff > 0:
        counts[keys[i % len(keys)]] += 1
        diff -= 1
        i += 1

    print("Counts per type:", counts)
    generate_counts(counts, seed=args.seed, outpath=args.output)
