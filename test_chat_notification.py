#!/usr/bin/env python3
"""
Test script to verify Google Chat notification delivery
"""
import sys
import os
from datetime import date

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from google.auth import default
from google.oauth2.credentials import Credentials
from backend.app.services.notification_service import NotificationService
from backend.config.settings import ENABLE_CHAT_NOTIFICATIONS
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    print("=" * 60)
    print("GOOGLE CHAT NOTIFICATION TEST")
    print("=" * 60)
    print()

    # Check if Chat notifications are enabled
    print(f"1. Chat Notifications Enabled: {ENABLE_CHAT_NOTIFICATIONS}")
    if not ENABLE_CHAT_NOTIFICATIONS:
        print("   ⚠️  Chat notifications are disabled in settings!")
        print("   Set ENABLE_CHAT_NOTIFICATIONS=true in .env")
        return
    print()

    # Initialize with Application Default Credentials
    print("2. Initializing NotificationService...")
    try:
        # For testing, we'll use a dummy credential object
        # The actual Chat service will use ADC in _get_chat_service()
        credentials, project = default()
        notification_service = NotificationService(credentials)
        print("   ✓ NotificationService initialized")
    except Exception as e:
        print(f"   ✗ Failed to initialize: {e}")
        return
    print()

    # Test sending a simple direct message
    test_email = input("Enter your email to test DM (e.g., dirk@edvolution.io): ").strip()
    if not test_email:
        print("No email provided, exiting.")
        return

    print(f"\n3. Testing simple direct message to {test_email}...")
    try:
        success = notification_service.send_direct_message(
            user_email=test_email,
            message_text="🧪 **Test Message**\n\nThis is a test message from the Employee Portal notification system."
        )
        if success:
            print("   ✓ Direct message sent successfully!")
            print("   Check your Google Chat for the message.")
        else:
            print("   ✗ Failed to send direct message")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
    print()

    # Test sending an approval card
    print(f"4. Testing approval card to {test_email}...")
    try:
        success = notification_service.send_approval_chat_card(
            user_email=test_email,
            employee_name="Test Employee",
            employee_email="test@edvolution.io",
            start_date="2025-12-20",
            end_date="2025-12-27",
            days_count=7,
            timeoff_type="vacation",
            notes="This is a test approval notification",
            request_id="test-123",
            approval_level="manager",
            portal_url="https://rrhh.edvolution.io"
        )
        if success:
            print("   ✓ Approval card sent successfully!")
            print("   Check your Google Chat for the interactive card.")
        else:
            print("   ✗ Failed to send approval card")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
    print()

    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print("\nIf you received messages in Google Chat, the integration is working!")
    print("If not, check the error messages above and Cloud Run logs.")

if __name__ == "__main__":
    main()
