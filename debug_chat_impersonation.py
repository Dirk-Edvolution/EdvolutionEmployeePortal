import os
import json
import requests
from google.oauth2 import service_account
from google.auth import default as google_auth_default
from google.auth.transport.requests import Request
import time

def test_chat_impersonation():
    """
    Tests the full Domain-Wide Delegation flow by using gcloud to generate
    the necessary tokens and then calling the Google Chat API.
    """
    print("🚀 Starting Google Chat impersonation test...")

    try:
        # --- 1. Configuration ---
        admin_to_impersonate = os.environ.get('ADMIN_USERS', 'dirk@edvolution.io')
        # Ensure admin_to_impersonate is just the email, not a comma-separated list
        if ',' in admin_to_impersonate:
            admin_to_impersonate = admin_to_impersonate.split(',')[0].strip()

        service_account_email = "employee-portal-runtime@edvolution-admon.iam.gserviceaccount.com"
        # Scopes needed for DWD: chat.messages for sending, chat.spaces for finding/creating DM spaces
        chat_scopes = [
            'https://www.googleapis.com/auth/chat.messages',
            'https://www.googleapis.com/auth/chat.spaces'
        ]

        # --- 2. Obtain Service Account Credentials for Domain-Wide Delegation ---
        # This requires the service account's private key, typically from a JSON file
        # or an environment variable containing the JSON content.
        # or by using Application Default Credentials (ADC) via `gcloud auth`.
        print(f"🔑 Attempting to load service account credentials for DWD...")

        service_account_key_json = os.environ.get('GCP_SERVICE_ACCOUNT_KEY_JSON')
        if not service_account_key_json:
            raise ValueError(
                "GCP_SERVICE_ACCOUNT_KEY_JSON environment variable not set. "
                "It should contain the JSON content of your service account key."
            )
        service_account_info = json.loads(service_account_key_json)
        
        # Create credentials that impersonate the target user (Domain-Wide Delegation)
        user_creds = service_account.Credentials.from_service_account_info(
            service_account_info,
            subject=admin_to_impersonate,
            scopes=chat_scopes
        )
        
        # Refresh the token to get an access token for the impersonated user
        user_creds.refresh(Request())
        if not user_creds.token:
            raise Exception("Failed to obtain user-impersonated access token.")

        print(f"✅ Successfully obtained user-impersonated access token for {admin_to_impersonate}.")

        # --- 3. Find or Create Direct Message (DM) Space using the setup endpoint ---
        # This is the modern, idempotent way to get a DM space. It will either
        # find the existing DM space or create a new one if it doesn't exist.
        print(f"🔍 Finding or creating DM space with {admin_to_impersonate}...")
        headers = {
            "Authorization": f"Bearer {user_creds.token}",
            "Content-Type": "application/json"
        }
        setup_space_url = "https://chat.googleapis.com/v1/spaces:setup"
        setup_payload = {"member": f"users/{admin_to_impersonate}"}
        
        setup_response = requests.post(setup_space_url, headers=headers, json=setup_payload)
        setup_response.raise_for_status()
        dm_space_name = setup_response.json().get('name')
        
        if not dm_space_name:
            raise Exception("Failed to find or create DM space using the setup endpoint.")
        print(f"   ✓ Successfully found/created DM space: {dm_space_name}")

        # --- 4. Send the Google Chat message to the DM space ---
        print(f"📬 Sending test message to DM space {dm_space_name}...")
        send_message_url = f"https://chat.googleapis.com/v1/{dm_space_name}/messages"
        message_body = {'text': '✅ Test Message: Service account impersonation for Google Chat is working correctly!'}
        response = requests.post(send_message_url, headers=headers, json=message_body)
        response.raise_for_status()

        print("\n🎉 SUCCESS! The test message was sent successfully.")
        print("Please check your Google Chat for a message from the 'Google Chat App'.")

    except Exception as e:
        error_details = ""
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_details = f"API Response: {json.dumps(e.response.json(), indent=2)}"
            except json.JSONDecodeError:
                error_details = f"API Response: {e.response.text}"
        print(f"\n❌ FAILURE: The test failed. Reason: {e}\n{error_details}")
        print("\n📋 Troubleshooting Steps:")
        print("1. Ensure the `GCP_SERVICE_ACCOUNT_KEY_JSON` environment variable is set with the correct service account key JSON content.")
        print("2. Has the service account's Client ID been granted Domain-Wide Delegation in the Google Workspace Admin Console?")
        print("3. Does the delegation include the 'https://www.googleapis.com/auth/chat.messages' and 'https://www.googleapis.com/auth/chat.spaces' scopes?")
        print("4. Is the `admin_to_impersonate` email (e.g., dirk@edvolution.io) a valid user in your Google Workspace?")

if __name__ == "__main__":
    test_chat_impersonation()