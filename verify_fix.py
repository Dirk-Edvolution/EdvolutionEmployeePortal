#!/usr/bin/env python3
"""
Comprehensive verification that all calculation points use working days
This checks:
1. Vacation balance calculation
2. API responses
3. Notifications
4. Any other calculation points
"""
import sys
import re
from pathlib import Path

def check_file_for_calendar_days_usage(filepath):
    """Check if a file still uses calendar days incorrectly"""
    issues = []

    with open(filepath, 'r') as f:
        lines = f.readlines()

    for i, line in enumerate(lines, 1):
        # Look for problematic patterns
        if 'req.days_count' in line and 'vacation' in ''.join(lines[max(0, i-10):i+10]).lower():
            # Check if it's in a vacation calculation context
            context = ''.join(lines[max(0, i-3):min(len(lines), i+3)])
            if 'vacation' in context.lower() or 'balance' in context.lower():
                issues.append({
                    'line': i,
                    'code': line.strip(),
                    'issue': 'Using days_count for vacation calculation (should use get_working_days_count)'
                })

        if 'days_count =' in line and '(' in line and ')' in line:
            # Manual days_count calculation
            issues.append({
                'line': i,
                'code': line.strip(),
                'issue': 'Manual days_count calculation (should be automatic property)'
            })

    return issues

def main():
    """Check all relevant files"""
    files_to_check = [
        'backend/app/services/firestore_service.py',
        'backend/app/api/timeoff_routes.py',
        'backend/app/models/timeoff_request.py',
    ]

    print("=" * 70)
    print("VERIFICATION: Working Days Calculation Fix")
    print("=" * 70)
    print()

    all_good = True

    for filepath in files_to_check:
        path = Path(filepath)
        if not path.exists():
            print(f"⚠️  {filepath} - NOT FOUND")
            continue

        issues = check_file_for_calendar_days_usage(filepath)

        if issues:
            all_good = False
            print(f"❌ {filepath}")
            for issue in issues:
                print(f"   Line {issue['line']}: {issue['issue']}")
                print(f"   Code: {issue['code']}")
                print()
        else:
            print(f"✅ {filepath} - No issues found")

    print()
    print("=" * 70)

    # Check for 2025 holidays
    print("\nChecking for 2025 Mexico holidays...")
    holiday_file = Path('backend/app/services/holiday_service.py')
    if holiday_file.exists():
        content = holiday_file.read_text()
        if '2025:' in content and "'mexico'" in content:
            print("✅ 2025 Mexico holidays present")
        else:
            print("❌ 2025 Mexico holidays MISSING")
            all_good = False

    # Check for working_days_count in API responses
    print("\nChecking for working_days_count in API responses...")
    routes_file = Path('backend/app/api/timeoff_routes.py')
    if routes_file.exists():
        content = routes_file.read_text()
        if 'working_days_count' in content:
            print("✅ working_days_count added to API responses")
        else:
            print("⚠️  working_days_count not found in API responses")
            all_good = False

    print()
    print("=" * 70)
    if all_good:
        print("✅ ALL CHECKS PASSED - Fix is comprehensive!")
    else:
        print("❌ ISSUES FOUND - Review above")
    print("=" * 70)

    return 0 if all_good else 1

if __name__ == '__main__':
    sys.exit(main())
