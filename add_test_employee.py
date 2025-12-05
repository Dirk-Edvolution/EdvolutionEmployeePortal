#!/usr/bin/env python3
"""
Script to add a test employee to the Firestore database
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app.services.firestore_service import FirestoreService
from backend.app.models.employee import Employee
from datetime import datetime

def add_test_employee(email: str):
    """Add a test employee to the database"""
    print(f"Adding test employee: {email}")

    # Create Firestore service
    firestore_service = FirestoreService()

    # Check if employee already exists
    existing = firestore_service.get_employee(email)
    if existing:
        print(f"✓ Employee {email} already exists in the database!")
        print(f"  Name: {existing.full_name}")
        print(f"  Active: {existing.is_active}")
        print(f"  Admin: {existing.is_admin}")
        return

    # Create test employee
    test_employee = Employee(
        email=email,
        workspace_id='test-' + email.split('@')[0],
        given_name='Dirk',
        family_name='Rosquillas',
        full_name='Dirk Rosquillas',
        photo_url=None,
        manager_email='dirk@edvolution.io',  # Reports to admin
        organizational_unit='Engineering',
        department='Engineering',
        job_title='Test Employee',
        location='Remote',
        country='US',
        region='North America',
        vacation_days_per_year=20,
        is_admin=False,  # Not an admin, regular employee for testing
        is_active=True,
        contract_type='temporary',
        contract_start_date=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    # Save to Firestore
    firestore_service.create_employee(test_employee)
    print(f"✓ Successfully added test employee: {email}")
    print(f"  Name: {test_employee.full_name}")
    print(f"  Department: {test_employee.department}")
    print(f"  Manager: {test_employee.manager_email}")
    print(f"  Vacation days: {test_employee.vacation_days_per_year}")
    print(f"\nYou can now login at: http://localhost:8080/auth/login")

if __name__ == '__main__':
    # Add test employee - must use edvolution.io domain for OAuth
    test_email = 'test@edvolution.io'

    # Allow command line argument
    if len(sys.argv) > 1:
        test_email = sys.argv[1]

    add_test_employee(test_email)
