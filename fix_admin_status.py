#!/usr/bin/env python3
"""
Fix admin status in Firestore
Updates is_admin field for all users in ADMIN_USERS
"""

import sys
import os

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.services.firestore_service import FirestoreService
from backend.config.settings import ADMIN_USERS

def main():
    print("=" * 60)
    print("FIXING ADMIN STATUS IN FIRESTORE")
    print("=" * 60)
    print()

    db = FirestoreService()

    print(f"Admin users from config: {ADMIN_USERS}")
    print()

    for admin_email in ADMIN_USERS:
        print(f"Processing {admin_email}...")
        employee = db.get_employee(admin_email)

        if not employee:
            print(f"  ⚠️  Employee not found in Firestore")
            continue

        if employee.is_admin:
            print(f"  ✓ Already marked as admin")
        else:
            print(f"  Updating is_admin from {employee.is_admin} to True")
            employee.is_admin = True
            db.update_employee(employee)
            print(f"  ✓ Updated successfully")

        print()

    print("=" * 60)
    print("DONE!")
    print("=" * 60)

if __name__ == "__main__":
    main()
