#!/usr/bin/env python3
"""
Debug script to check approval workflow issues
Investigates why dirk@edvolution.io doesn't see mayra@edvolution.io's pending request
"""

import sys
import os

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.services.firestore_service import FirestoreService
from backend.config.settings import ADMIN_USERS

def main():
    print("=" * 60)
    print("APPROVAL WORKFLOW DIAGNOSTIC")
    print("=" * 60)
    print()

    db = FirestoreService()

    # Check mayra's employee record
    print("1. Checking mayra@edvolution.io employee record:")
    print("-" * 60)
    mayra = db.get_employee('mayra@edvolution.io')
    if mayra:
        print(f"✓ Employee found")
        print(f"  Full Name: {mayra.full_name}")
        print(f"  Email: {mayra.email}")
        print(f"  Manager Email: {mayra.manager_email}")
        print(f"  Department: {mayra.department}")
        print(f"  Is Admin: {mayra.is_admin}")
    else:
        print("✗ Employee NOT FOUND in Firestore")
        return
    print()

    # Check dirk's employee record
    print("2. Checking dirk@edvolution.io employee record:")
    print("-" * 60)
    dirk = db.get_employee('dirk@edvolution.io')
    if dirk:
        print(f"✓ Employee found")
        print(f"  Full Name: {dirk.full_name}")
        print(f"  Email: {dirk.email}")
        print(f"  Manager Email: {dirk.manager_email}")
        print(f"  Is Admin: {dirk.is_admin}")
    else:
        print("✗ Employee NOT FOUND in Firestore")
    print()

    # Check manager relationship
    print("3. Manager Relationship Check:")
    print("-" * 60)
    if mayra.manager_email == 'dirk@edvolution.io':
        print(f"✓ Correct: mayra's manager is dirk")
    else:
        print(f"✗ ISSUE: mayra's manager is '{mayra.manager_email}', not 'dirk@edvolution.io'")
        print(f"  This is why dirk doesn't see the approval!")
    print()

    # Check all pending time-off requests for mayra
    print("4. Checking mayra's time-off requests:")
    print("-" * 60)
    mayra_requests = db.get_employee_timeoff_requests('mayra@edvolution.io')
    if mayra_requests:
        print(f"✓ Found {len(mayra_requests)} request(s)")
        for req_id, req in mayra_requests:
            print(f"\n  Request ID: {req_id}")
            print(f"  Status: {req.status}")
            print(f"  Start Date: {req.start_date}")
            print(f"  End Date: {req.end_date}")
            print(f"  Type: {req.timeoff_type}")
            print(f"  Days: {req.days_count}")
            print(f"  Manager Email (in request): {req.manager_email}")
            print(f"  Created: {req.created_at}")

            # Check if manager_email matches
            if req.manager_email != mayra.manager_email:
                print(f"  ⚠️  WARNING: Request manager_email doesn't match employee manager_email")
                print(f"     Request has: {req.manager_email}")
                print(f"     Employee has: {mayra.manager_email}")
    else:
        print("✗ No requests found for mayra")
    print()

    # Check pending requests for dirk as manager
    print("5. Checking pending requests for dirk@edvolution.io (as manager):")
    print("-" * 60)
    dirk_manager_requests = db.get_pending_requests_for_manager('dirk@edvolution.io')
    if dirk_manager_requests:
        print(f"✓ Found {len(dirk_manager_requests)} pending request(s) for dirk")
        for req_id, req in dirk_manager_requests:
            print(f"\n  Request ID: {req_id}")
            print(f"  Employee: {req.employee_email}")
            print(f"  Status: {req.status}")
            print(f"  Manager Email: {req.manager_email}")
            print(f"  Dates: {req.start_date} to {req.end_date}")
    else:
        print("✗ No pending requests found for dirk as manager")
        print("   This explains why dirk doesn't see any approvals in the dashboard")
    print()

    # Check pending requests for dirk as admin
    print("6. Checking pending requests for dirk@edvolution.io (as admin):")
    print("-" * 60)
    if dirk and dirk.is_admin:
        admin_requests = db.get_pending_requests_for_admin()
        if admin_requests:
            print(f"✓ Found {len(admin_requests)} admin pending request(s)")
            for req_id, req in admin_requests:
                print(f"\n  Request ID: {req_id}")
                print(f"  Employee: {req.employee_email}")
                print(f"  Status: {req.status}")
                print(f"  Manager Approved By: {req.manager_approved_by}")
                print(f"  Manager Approved At: {req.manager_approved_at}")
        else:
            print("  No manager_approved requests waiting for admin approval")
    else:
        print("  Dirk is not an admin")
    print()

    # Check admin users configuration
    print("7. Admin Users Configuration:")
    print("-" * 60)
    print(f"  ADMIN_USERS: {ADMIN_USERS}")
    print(f"  Dirk is admin: {'dirk@edvolution.io' in ADMIN_USERS}")
    print()

    # Summary and recommendations
    print("=" * 60)
    print("SUMMARY AND RECOMMENDATIONS")
    print("=" * 60)

    issues = []

    # Check if manager relationship is correct
    if mayra and mayra.manager_email != 'dirk@edvolution.io':
        issues.append({
            'severity': 'HIGH',
            'issue': f"Mayra's manager is set to '{mayra.manager_email}' instead of 'dirk@edvolution.io'",
            'fix': "Update mayra's manager_email in Firestore or Google Workspace"
        })

    # Check if request has manager_email set
    if mayra_requests:
        for req_id, req in mayra_requests:
            if req.status == 'pending' and req.manager_email != 'dirk@edvolution.io':
                issues.append({
                    'severity': 'HIGH',
                    'issue': f"Request {req_id} has manager_email='{req.manager_email}' instead of 'dirk@edvolution.io'",
                    'fix': f"Update request {req_id} manager_email field in Firestore"
                })

    # Check if dirk sees the requests
    if not dirk_manager_requests:
        issues.append({
            'severity': 'HIGH',
            'issue': "Dirk doesn't see any pending requests as manager",
            'fix': "This is caused by the manager_email mismatch above"
        })

    if issues:
        print("\n⚠️  ISSUES FOUND:")
        for i, issue in enumerate(issues, 1):
            print(f"\n{i}. [{issue['severity']}] {issue['issue']}")
            print(f"   Fix: {issue['fix']}")
    else:
        print("\n✓ No issues found! The approval workflow should be working correctly.")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
