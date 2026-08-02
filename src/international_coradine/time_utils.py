from __future__ import annotations

from datetime import datetime, timedelta

from .models import EM_DASH


def parse_duration_minutes(value: str | None) -> int | None:
    if not value or value == EM_DASH:
        return None
    text = str(value).strip()
    if ":" not in text:
        return None
    try:
        hours, minutes = text.split(":", 1)
        total = int(hours) * 60 + int(minutes)
    except (TypeError, ValueError):
        return None
    return total if total >= 0 and 0 <= int(minutes) < 60 else None


def format_duration(minutes: int | None) -> str:
    if minutes is None:
        return EM_DASH
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def parse_clock(value: str | None) -> int | None:
    if not value or value == EM_DASH:
        return None
    text = str(value).strip().replace(".", ":")
    if ":" not in text:
        return None
    try:
        hour, minute = text.split(":", 1)
        hour_i, minute_i = int(hour), int(minute)
    except (TypeError, ValueError):
        return None
    if not (0 <= hour_i <= 23 and 0 <= minute_i <= 59):
        return None
    return hour_i * 60 + minute_i


def format_clock(minutes: int | None) -> str:
    if minutes is None:
        return EM_DASH
    minutes %= 24 * 60
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def elapsed_minutes(out_time: str, in_time: str) -> int | None:
    out_m, in_m = parse_clock(out_time), parse_clock(in_time)
    if out_m is None or in_m is None:
        return None
    if in_m < out_m:
        in_m += 24 * 60
    return in_m - out_m


def add_minutes(clock: str | None, duration: int) -> str:
    parsed = parse_clock(clock)
    return format_clock(parsed + duration) if parsed is not None else EM_DASH


def subtract_minutes(clock: str | None, duration: int) -> str:
    parsed = parse_clock(clock)
    return format_clock(parsed - duration) if parsed is not None else EM_DASH


def excel_duration(minutes: int | None) -> float | str:
    return minutes / (24 * 60) if minutes is not None else EM_DASH


def today_iso() -> str:
    return datetime.now().date().isoformat()
