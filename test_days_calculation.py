#!/usr/bin/env python3
"""
Test script to verify working days calculation for Mexico holiday region
Example: Dec 23, 2025 - Jan 1, 2026
"""
from datetime import date, timedelta
import sys

# Simplified version of HolidayService for testing (no dependencies)
class HolidayService:
    YEAR_SPECIFIC_HOLIDAYS = {
        'mexico': {
            2025: [
                ('2025-01-01', 'Año Nuevo', None),
                ('2025-02-03', 'Día de la Constitución', 'Feriado puente'),
                ('2025-03-17', 'Natalicio de Benito Juárez', 'Feriado puente'),
                ('2025-05-01', 'Día del Trabajo', None),
                ('2025-09-16', 'Día de la Independencia Mexicana', None),
                ('2025-11-17', 'Día de la Revolución Mexicana', 'Feriado puente'),
                ('2025-12-25', 'Navidad', None),
            ],
            2026: [
                ('2026-01-01', 'Año Nuevo', None),
                ('2026-02-02', 'Día de la Constitución', 'Feriado puente'),
                ('2026-03-16', 'Natalicio de Benito Juárez', 'Feriado puente'),
                ('2026-05-01', 'Día del Trabajo', 'Feriado puente'),
                ('2026-09-16', 'Día de la Independencia Mexicana', None),
                ('2026-11-16', 'Día de la Revolución Mexicana', 'Feriado puente'),
                ('2026-12-25', 'Navidad', 'Feriado puente'),
            ]
        }
    }

    @classmethod
    def is_weekend(cls, date_obj):
        """Check if a date is a weekend (Saturday or Sunday)"""
        return date_obj.weekday() in [5, 6]  # 5=Saturday, 6=Sunday

    @classmethod
    def is_public_holiday(cls, date_obj, region):
        """Check if a date is a public holiday"""
        if region in cls.YEAR_SPECIFIC_HOLIDAYS:
            year_data = cls.YEAR_SPECIFIC_HOLIDAYS[region].get(date_obj.year)
            if year_data:
                date_str = date_obj.isoformat()
                for holiday_date_str, name, note in year_data:
                    if holiday_date_str == date_str:
                        return True
        return False

    @classmethod
    def is_working_day(cls, date_obj, region):
        """Check if a date is a working day"""
        if cls.is_weekend(date_obj):
            return False
        if region and cls.is_public_holiday(date_obj, region):
            return False
        return True

    @classmethod
    def count_working_days(cls, start_date, end_date, region):
        """Count working days between two dates"""
        if start_date > end_date:
            return 0

        working_days = 0
        current_date = start_date

        while current_date <= end_date:
            if cls.is_working_day(current_date, region):
                working_days += 1
            current_date += timedelta(days=1)

        return working_days


def test_working_days_calculation():
    """Test the working days calculation for the example date range"""

    # Example from user: Dec 23, 2025 - Jan 1, 2026
    start_date = date(2025, 12, 23)
    end_date = date(2026, 1, 1)
    region = 'mexico'

    print("=" * 60)
    print("Working Days Calculation Test")
    print("=" * 60)
    print(f"Date Range: {start_date} to {end_date}")
    print(f"Region: {region}")
    print(f"Calendar Days: {(end_date - start_date).days + 1}")
    print()

    # Calculate working days
    working_days = HolidayService.count_working_days(start_date, end_date, region)

    print("Day-by-day breakdown:")
    print("-" * 60)
    current = start_date
    while current <= end_date:
        is_weekend = HolidayService.is_weekend(current)
        is_holiday = HolidayService.is_public_holiday(current, region)
        is_working = HolidayService.is_working_day(current, region)

        day_name = current.strftime('%A')
        status = "WORKING DAY" if is_working else "NON-WORKING"
        reason = ""

        if is_weekend:
            reason = f"(Weekend - {day_name})"
        elif is_holiday:
            # Get holiday name
            year_data = HolidayService.YEAR_SPECIFIC_HOLIDAYS.get(region, {}).get(current.year, [])
            for date_str, name, note in year_data:
                if date_str == current.isoformat():
                    reason = f"(Public Holiday: {name})"
                    break

        print(f"{current} - {day_name:9s} - {status:12s} {reason}")
        current += timedelta(days=1)

    print("-" * 60)
    print(f"\nRESULT: {working_days} working days will be deducted")
    print(f"Expected: 4 working days (Dec 23, 26, 27, 30)")
    print()

    # Verify each expected working day
    print("Verification:")
    print("-" * 60)
    dec_23 = HolidayService.is_working_day(date(2025, 12, 23), region)
    dec_24 = HolidayService.is_working_day(date(2025, 12, 24), region)
    dec_25 = HolidayService.is_working_day(date(2025, 12, 25), region)
    dec_26 = HolidayService.is_working_day(date(2025, 12, 26), region)
    dec_27 = HolidayService.is_working_day(date(2025, 12, 27), region)
    dec_28 = HolidayService.is_working_day(date(2025, 12, 28), region)
    dec_29 = HolidayService.is_working_day(date(2025, 12, 29), region)
    dec_30 = HolidayService.is_working_day(date(2025, 12, 30), region)
    dec_31 = HolidayService.is_working_day(date(2025, 12, 31), region)
    jan_01 = HolidayService.is_working_day(date(2026, 1, 1), region)

    print(f"Dec 23 (Mon): {'✓ Working' if dec_23 else '✗ Non-working'}")
    print(f"Dec 24 (Tue): {'✓ Working (Dec 24 is not a holiday in Mexico)' if dec_24 else '✗ Non-working'}")
    print(f"Dec 25 (Wed): {'✗ Non-working (Navidad)' if not dec_25 else '✓ Working (ERROR!)'}")
    print(f"Dec 26 (Thu): {'✓ Working' if dec_26 else '✗ Non-working'}")
    print(f"Dec 27 (Fri): {'✓ Working' if dec_27 else '✗ Non-working'}")
    print(f"Dec 28 (Sat): {'✗ Non-working (Weekend)' if not dec_28 else '✓ Working (ERROR!)'}")
    print(f"Dec 29 (Sun): {'✗ Non-working (Weekend)' if not dec_29 else '✓ Working (ERROR!)'}")
    print(f"Dec 30 (Mon): {'✓ Working' if dec_30 else '✗ Non-working'}")
    print(f"Dec 31 (Tue): {'✓ Working (Dec 31 is not a holiday in Mexico)' if dec_31 else '✗ Non-working'}")
    print(f"Jan 01 (Wed): {'✗ Non-working (Año Nuevo)' if not jan_01 else '✓ Working (ERROR!)'}")

    print()
    print("=" * 60)

    # Expected: Dec 23, 24, 26, 27, 30, 31 = 6 working days
    # Non-working: Dec 25 (Navidad), Dec 28 (Sat), Dec 29 (Sun), Jan 1 (Año Nuevo)
    expected_working_days = 6

    if working_days == expected_working_days:
        print(f"✓ TEST PASSED: Calculation is CORRECT! ({working_days} working days)")
    else:
        print(f"✗ TEST FAILED: Expected {expected_working_days} working days, got {working_days}")

    print("=" * 60)

    return working_days == expected_working_days

if __name__ == '__main__':
    success = test_working_days_calculation()
    sys.exit(0 if success else 1)
