#!/bin/bash

# Setup Google Cloud Secret Manager for Employee Portal
# This script creates and configures secrets for the application

set -e

PROJECT_ID=${GCP_PROJECT_ID}
SERVICE_NAME="employee-portal"
REGION=${GCP_LOCATION:-us-central1}

echo "🔐 Setting up secrets in Google Cloud Secret Manager"
echo "Project: $PROJECT_ID"

# Check if secrets exist, create if not
create_secret_if_not_exists() {
    local secret_name=$1
    local secret_value=$2

    if gcloud secrets describe $secret_name --project=$PROJECT_ID &> /dev/null; then
        echo "✓ Secret $secret_name already exists, updating..."
        echo -n "$secret_value" | gcloud secrets versions add $secret_name --data-file=- --project=$PROJECT_ID
    else
        echo "Creating secret $secret_name..."
        echo -n "$secret_value" | gcloud secrets create $secret_name --data-file=- --project=$PROJECT_ID
    fi
}

# Prompt for secrets if not set in environment
if [ -z "$GOOGLE_CLIENT_ID" ]; then
    read -p "Enter Google OAuth Client ID: " GOOGLE_CLIENT_ID
fi

if [ -z "$GOOGLE_CLIENT_SECRET" ]; then
    read -sp "Enter Google OAuth Client Secret: " GOOGLE_CLIENT_SECRET
    echo
fi

if [ -z "$FLASK_SECRET_KEY" ]; then
    echo "Generating Flask secret key..."
    FLASK_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
fi

if [ -z "$WORKSPACE_ADMIN_EMAIL" ]; then
    read -p "Enter Workspace Admin Email: " WORKSPACE_ADMIN_EMAIL
fi

# Create secrets
create_secret_if_not_exists "google-client-id" "$GOOGLE_CLIENT_ID"
create_secret_if_not_exists "google-client-secret" "$GOOGLE_CLIENT_SECRET"
create_secret_if_not_exists "flask-secret-key" "$FLASK_SECRET_KEY"
create_secret_if_not_exists "workspace-admin-email" "$WORKSPACE_ADMIN_EMAIL"

# Grant Cloud Run service account access to secrets
echo "🔑 Granting Cloud Run access to secrets..."
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

for secret in google-client-id google-client-secret flask-secret-key workspace-admin-email; do
    gcloud secrets add-iam-policy-binding $secret \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/secretmanager.secretAccessor" \
        --project=$PROJECT_ID
done

# Update Cloud Run service to use secrets
echo "🔄 Updating Cloud Run service with secrets..."
gcloud run services update $SERVICE_NAME \
    --region $REGION \
    --update-secrets GOOGLE_CLIENT_ID=google-client-id:latest \
    --update-secrets GOOGLE_CLIENT_SECRET=google-client-secret:latest \
    --update-secrets FLASK_SECRET_KEY=flask-secret-key:latest \
    --update-secrets WORKSPACE_ADMIN_EMAIL=workspace-admin-email:latest \
    --project=$PROJECT_ID

echo "✅ Secrets configured successfully!"
echo ""
echo "📋 Summary:"
echo "  - google-client-id: ✓"
echo "  - google-client-secret: ✓"
echo "  - flask-secret-key: ✓"
echo "  - workspace-admin-email: ✓"
