from datetime import datetime, timedelta


def parse_datetime(dt_str: str) -> datetime:
    """
    Safely parse datetime string from HTML input (datetime-local)
    Format: 'YYYY-MM-DDTHH:MM'
    """
    return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M")


def calculate_rebate(monthly_rate, downtime_start, downtime_end, month_length=30):
    """
    Calculate service rebate based on downtime duration.
    Normalizes edge cases where a "partial" day is effectively a full day.
    """
    # Ensure correct order
    if downtime_end < downtime_start:
        downtime_start, downtime_end = downtime_end, downtime_start

    # Rates
    daily_rate = monthly_rate / month_length
    hourly_rate = daily_rate / 24

    # If same-day downtime
    if downtime_start.date() == downtime_end.date():
        hours = (downtime_end - downtime_start).total_seconds() / 3600
        total_rebate = hours * hourly_rate
        return {
            "daily_rate": round(daily_rate, 2),
            "hourly_rate": round(hourly_rate, 3),
            "full_days": 0,
            "partial_start_hours": round(hours, 2),
            "partial_end_hours": 0,
            "rebate_partial_start": round(total_rebate, 2),
            "rebate_full_days": 0,
            "rebate_partial_end": 0,
            "total_rebate": round(total_rebate, 2),
            "total_rebate_rounded": round(total_rebate),
        }

    # Partial start day
    end_of_start_day = datetime.combine(downtime_start.date(), datetime.max.time())
    hours_start_day = (end_of_start_day - downtime_start).total_seconds() / 3600
    rebate_start_day = hours_start_day * hourly_rate

    # Partial end day
    start_of_end_day = datetime.combine(downtime_end.date(), datetime.min.time())
    hours_end_day = (downtime_end - start_of_end_day).total_seconds() / 3600
    rebate_end_day = hours_end_day * hourly_rate

    # Full days in between
    full_days = (downtime_end.date() - downtime_start.date()).days
    full_days = max(full_days, 0)

    # Normalize almost-full partial days
    TOL = 1e-9
    if hours_start_day + TOL >= 24.0:
        hours_start_day = 0.0
        rebate_start_day = 0.0
        full_days += 1

    if hours_end_day + TOL >= 24.0:
        hours_end_day = 0.0
        rebate_end_day = 0.0
        full_days += 1

    rebate_full_days = full_days * daily_rate
    total_rebate = rebate_start_day + rebate_full_days + rebate_end_day

    return {
        "daily_rate": round(daily_rate, 2),
        "hourly_rate": round(hourly_rate, 3),
        "full_days": full_days,
        "partial_start_hours": round(hours_start_day, 2),
        "partial_end_hours": round(hours_end_day, 2),
        "rebate_partial_start": round(rebate_start_day, 2),
        "rebate_full_days": round(rebate_full_days, 2),
        "rebate_partial_end": round(rebate_end_day, 2),
        "total_rebate": round(total_rebate, 2),
        "total_rebate_rounded": round(total_rebate),
    }


if __name__ == "__main__":
    start = parse_datetime("2025-09-16T00:00")
    end = parse_datetime("2025-09-30T11:00")
    result = calculate_rebate(999, start, end)

    print("\n--- Rebate Breakdown ---")
    for k, v in result.items():
        print(f"{k}: {v}")
