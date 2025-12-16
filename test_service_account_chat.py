"""
Test script for Google Chat using service account with domain-wide delegation
"""
import os
from google.auth import default
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_service_account_delegation():
    """
    Test if service account can impersonate hola@edvolution.io for Google Chat
    """
    try:
        # Email to impersonate
        impersonate_email = os.getenv('NOTIFICATION_ACCOUNT_EMAIL', 'hola@edvolution.io')
        test_recipient = os.getenv('TEST_USER_EMAIL', 'dirk@edvolution.io')

        logger.info(f"Testing service account domain-wide delegation")
        logger.info(f"Impersonating: {impersonate_email}")
        logger.info(f"Sending test message to: {test_recipient}")

        # Get default credentials (should be service account in Cloud Run)
        credentials, project = default()
        logger.info(f"Using credentials from project: {project}")
        logger.info(f"Credential type: {type(credentials).__name__}")

        # Check if credentials support delegation
        if not hasattr(credentials, 'with_subject'):
            logger.error("❌ Credentials do not support domain-wide delegation!")
            logger.error("Make sure you're running this in Cloud Run or have a service account key set up locally")
            return False

        logger.info("✓ Credentials support domain-wide delegation")

        # Create delegated credentials
        scopes = [
            'https://www.googleapis.com/auth/chat.messages',
            'https://www.googleapis.com/auth/chat.spaces'
        ]

        logger.info(f"Creating delegated credentials for {impersonate_email}...")
        delegated_credentials = credentials.with_subject(impersonate_email).with_scopes(scopes)

        # Refresh if needed
        if not delegated_credentials.valid:
            logger.info("Refreshing delegated credentials...")
            delegated_credentials.refresh(Request())

        logger.info("✓ Delegated credentials created and refreshed")

        # Build Chat service
        chat = build('chat', 'v1', credentials=delegated_credentials)
        logger.info("✓ Chat service built successfully")

        # Try to find or create DM space with test user
        logger.info(f"Finding/creating DM space with {test_recipient}...")
        try:
            response = chat.spaces().findDirectMessage(name=f"users/{test_recipient}").execute()
            space_name = response.get('name')
            logger.info(f"✓ Found existing DM space: {space_name}")
        except Exception as find_error:
            logger.info(f"No existing DM space found, creating new one...")
            response = chat.spaces().setup(body={
                'space': {
                    'spaceType': 'DIRECT_MESSAGE'
                },
                'membershipInvitation': {
                    'user': {
                        'name': f'users/{test_recipient}'
                    }
                }
            }).execute()
            space_name = response.get('space', {}).get('name')
            logger.info(f"✓ Created new DM space: {space_name}")

        # Send test message
        test_message = {
            'text': f'🧪 Test message from service account impersonating {impersonate_email}\n\nIf you can read this, domain-wide delegation is working!'
        }

        logger.info("Sending test message...")
        result = chat.spaces().messages().create(
            parent=space_name,
            body=test_message
        ).execute()

        logger.info(f"✅ SUCCESS! Message sent: {result.get('name')}")
        logger.info(f"✅ Domain-wide delegation is working correctly!")
        return True

    except Exception as e:
        logger.error(f"❌ FAILED: {str(e)}", exc_info=True)
        return False


if __name__ == '__main__':
    print("\n" + "="*80)
    print("TESTING SERVICE ACCOUNT DOMAIN-WIDE DELEGATION FOR GOOGLE CHAT")
    print("="*80 + "\n")

    success = test_service_account_delegation()

    print("\n" + "="*80)
    if success:
        print("✅ ALL TESTS PASSED - Domain-wide delegation is working!")
        print("\nYou can now use the notification service to send Chat messages")
        print("by impersonating hola@edvolution.io")
    else:
        print("❌ TESTS FAILED - Please check the error messages above")
        print("\nMake sure:")
        print("1. Service account unique ID (115131457162383560161) is added to domain-wide delegation")
        print("2. Required scopes are authorized in Google Admin Console")
        print("3. Service account has proper permissions")
    print("="*80 + "\n")
