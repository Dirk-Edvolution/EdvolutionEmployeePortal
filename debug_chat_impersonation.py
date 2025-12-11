import os
import json
import google.auth
from google.auth import impersonated_credentials
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession

def test_chat_impersonation():
    """
    Tests the ability of the service account to impersonate an admin
    and send a Google Chat message.
    """
    print("🚀 Starting Google Chat impersonation test...")

    try:
        # --- 1. Load Configuration & Credentials ---
        # --- 1. Configuration ---
        admin_to_impersonate = os.environ.get('ADMIN_USERS', 'dirk@edvolution.io')
        target_user_email = admin_to_impersonate # For this test, we'll message ourselves.
        service_account_email = "employee-portal-runtime@edvolution-admon.iam.gserviceaccount.com"
        scopes = ['https://www.googleapis.com/auth/chat.messages']
        creds = None

        # This logic supports two environments:
        # 1. CI/CD (like GitHub Actions) where GCP_CREDENTIALS is a secret.
        # 2. Local/Cloud Shell where Application Default Credentials are used.
        credentials_json_str = os.environ.get('GCP_CREDENTIALS')
        if credentials_json_str:
            print("🔑 Authenticating with GCP_CREDENTIALS environment variable...")
            creds_info = json.loads(credentials_json_str)
            creds = service_account.Credentials.from_service_account_info(creds_info)
        else:
            print("🔑 Authenticating with Application Default Credentials.")
            print("   (Expecting an impersonated service account in this environment).")
            creds, _ = google.auth.default()
        # --- 2. Authenticate and Impersonate Service Account ---
        # In Cloud Shell, google.auth.default() gets your user credentials.
        # We use these to impersonate the service account.
        print(f"� Using user credentials to impersonate service account: {service_account_email}")
        source_credentials, _ = google.auth.default()

        # This creates credentials that act AS the service account.
        sa_credentials = impersonated_credentials.Credentials(
            source_credentials=source_credentials,
            target_principal=service_account_email,
            target_scopes=['https://www.googleapis.com/auth/cloud-platform'], # Scopes for the SA itself
        )

        print(f"�👤 Admin to Impersonate: {admin_to_impersonate}")

        # --- 2. Create Impersonated Credentials ---
        impersonated_creds = creds.with_subject(admin_to_impersonate).with_scopes(scopes)
        # --- 3. Use Service Account to Impersonate User (Domain-Wide Delegation) ---
        # This is the second impersonation step.
        # We use the SA creds to act ON BEHALF OF the end user.
        user_impersonation_creds = sa_credentials.with_subject(admin_to_impersonate).with_scopes(scopes)
        print("✅ Successfully created impersonated credentials.")

        # --- 3. Send Chat Message ---
        authed_session = AuthorizedSession(impersonated_creds)
        # --- 4. Send Chat Message ---
        authed_session = AuthorizedSession(user_impersonation_creds)
        url = f"https://chat.googleapis.com/v1/spaces/users/{target_user_email}/messages"
        message_body = {'text': '✅ Test Message: Service account impersonation for Google Chat is working correctly!'}
        
        print(f"📬 Sending test message to {target_user_email}...")
        response = authed_session.post(url, json=message_body)
        response.raise_for_status()

        print("\n🎉 SUCCESS! The test message was sent successfully.")
        print("Please check your Google Chat for a message from the 'Google Chat App'.")

    except Exception as e:
        print(f"\n❌ FAILURE: The test failed. Reason: {e}")
        print("\nTroubleshooting Steps:")
        print("1. If running locally, did you impersonate the service account first?")
        print("   gcloud auth application-default login --impersonate-service-account=\"employee-portal-runtime@edvolution-admon.iam.gserviceaccount.com\"")
        print("\n📋 Troubleshooting Steps:")
        print("1. Is your logged-in user granted the 'Service Account Token Creator' role on the service account?")
        print("2. Has the service account's Client ID been granted Domain-Wide Delegation in the Google Workspace Admin Console?")
        print("3. Does the delegation include the 'https://www.googleapis.com/auth/chat.messages' scope?")

if __name__ == "__main__":
    test_chat_impersonation()