#!/usr/bin/env python3
"""Salary normalization and conversion utilities."""
import re

# Constants
HOURS_PER_YEAR = 2080
MONTHS_PER_YEAR = 12

# Manual salary keywords to preserve as-is
SALARY_MANUAL_KEYWORDS = {
    "negotiable", "tbd", "tba", "n/a", "not specified", 
    "unspecified", "market", "dependent", "undisclosed", "competitive",
}

# Time markers for pattern matching
HOURLY_MARKERS = ["/hr", "/hour", "per hour", "an hour", "hourly", " hr"]
YEARLY_MARKERS = ["/yr", "/year", "per year", "a year", "yearly", " yr"]
MONTHLY_MARKERS = ["/mo", "/month", "per month", "a month", "monthly", " mo"]


def normalize_salary(s: str) -> str:
    """
    Convert hourly/monthly salaries to annual equivalents.
    Examples:
      - "$23/hr" → "$23.00/hr (~$47,840/yr)"
      - "$5000/mo" → "$5,000/mo (~$60,000/yr, ~$28.85/hr)"
      - "$120k/yr" → "$120,000/yr (~$57.69/hr)"
    """
    s = (s or "").strip()
    if not s:
        return ""
    
    lower = s.lower()
    
    # Preserve manual keywords as-is
    if lower in SALARY_MANUAL_KEYWORDS:
        return s
    
    # Check for time markers
    is_hourly = any(x in lower for x in HOURLY_MARKERS)
    is_yearly = any(x in lower for x in YEARLY_MARKERS)
    is_monthly = any(x in lower for x in MONTHLY_MARKERS)
    
    # If no currency/time markers, consider undetermined
    has_currency_marker = ("$" in s) or ("k" in lower)
    has_time_marker = is_hourly or is_yearly or is_monthly
    if not has_currency_marker and not has_time_marker:
        return s  # Return as-is if no clear salary pattern
    
    # Extract numbers near $ or k symbols
    salary_patterns = re.findall(
        r"\$\s*([\d,]+(?:\.\d+)?)\s*(?:k|K)?(?:\s*[-–]\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:k|K)?)?",
        s,
    )
    
    values = []
    if salary_patterns:
        for match in salary_patterns:
            for num_str in match:
                if num_str:
                    num = float(num_str.replace(",", ""))
                    # Convert k notation (e.g., 70k → 70000)
                    if "k" in s.lower() and num < 1000:
                        num *= 1000
                    values.append(num)
    
    # Fallback: catch '70k' or '70-90k' style without leading $
    if not values:
        if ("k" in s.lower()) and (is_hourly or is_yearly or is_monthly):
            k_matches = re.findall(r"([\d,]+)(?:\s*[-–]\s*([\d,]+))?\s*[kK]\b", s)
            for m in k_matches:
                n1, n2 = m[0], m[1]
                try:
                    v1 = float(n1.replace(",", "")) * 1000
                    values.append(v1)
                    if n2:
                        v2 = float(n2.replace(",", "")) * 1000
                        values.append(v2)
                except Exception:
                    pass
    
    if not values:
        return s  # No numbers found, return as-is
    
    def fmt_money(x, decimals=0):
        """Format number as currency."""
        return f"${x:,.0f}" if decimals == 0 else f"${x:,.2f}"
    
    # Convert hourly → yearly
    if is_hourly:
        if len(values) == 1:
            h = values[0]
            y = h * HOURS_PER_YEAR
            return f"{fmt_money(h, 2)}/hr (~{fmt_money(y)}/yr)"
        elif len(values) >= 2:
            h1, h2 = values[0], values[1]
            y1, y2 = h1 * HOURS_PER_YEAR, h2 * HOURS_PER_YEAR
            return (
                f"{fmt_money(h1, 2)}–{fmt_money(h2, 2)}/hr "
                f"(~{fmt_money(y1)}–{fmt_money(y2)}/yr)"
            )
    
    # Convert yearly → hourly
    if is_yearly:
        if len(values) == 1:
            y = values[0]
            h = y / HOURS_PER_YEAR
            return f"{fmt_money(y)}/yr (~{fmt_money(h, 2)}/hr)"
        elif len(values) >= 2:
            y1, y2 = values[0], values[1]
            h1, h2 = y1 / HOURS_PER_YEAR, y2 / HOURS_PER_YEAR
            return (
                f"{fmt_money(y1)}–{fmt_money(y2)}/yr "
                f"(~{fmt_money(h1, 2)}–{fmt_money(h2, 2)}/hr)"
            )
    
    # Convert monthly → yearly and hourly
    if is_monthly:
        if len(values) == 1:
            m = values[0]
            y = m * MONTHS_PER_YEAR
            h = y / HOURS_PER_YEAR
            return f"{fmt_money(m)}/mo (~{fmt_money(y)}/yr, ~{fmt_money(h, 2)}/hr)"
        elif len(values) >= 2:
            m1, m2 = values[0], values[1]
            y1, y2 = m1 * MONTHS_PER_YEAR, m2 * MONTHS_PER_YEAR
            h1, h2 = y1 / HOURS_PER_YEAR, y2 / HOURS_PER_YEAR
            return (
                f"{fmt_money(m1)}–{fmt_money(m2)}/mo "
                f"(~{fmt_money(y1)}–{fmt_money(y2)}/yr, ~{fmt_money(h1, 2)}–{fmt_money(h2, 2)}/hr)"
            )
    
    return s  # No conversion needed, return as-is
