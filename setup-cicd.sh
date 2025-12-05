#!/bin/bash

# CI/CD Setup Script for Google Cloud
# This script creates a Service Account for GitHub Actions and generates the necessary key.

set -e

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "❌ .env file not found. Please create one first."
    exit 1
fi

PROJECT_ID=${GCP_PROJECT_ID}
SA_NAME="github-actions-deployer"
SA_EMAIL="$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"

echo "🚀 Setting up CI/CD Service Account for project: $PROJECT_ID"

# 1. Enable necessary APIs
echo "🔌 Enabling required APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    iam.googleapis.com \
    artifactregistry.googleapis.com \
    --project "$PROJECT_ID"

# 2. Create Service Account (if it doesn't exist)
if gcloud iam service-accounts describe "$SA_EMAIL" --project "$PROJECT_ID" &>/dev/null; then
    echo "⚠️ Service Account $SA_EMAIL already exists. Using existing one."
else
    echo "👤 Creating Service Account: $SA_NAME..."
    gcloud iam service-accounts create "$SA_NAME" \
        --description="GitHub Actions CI/CD Deployer" \
        --display-name="GitHub Actions Deployer" \
        --project "$PROJECT_ID"
fi

# 3. Grant Permissions
echo "🔑 Granting permissions..."
# Cloud Run Admin (to deploy services)
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/run.admin" > /dev/null

# Service Account User (to act as the service account)
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/iam.serviceAccountUser" > /dev/null

# Storage Admin (for Cloud Build staging buckets)
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/storage.admin" > /dev/null

# Cloud Build Editor (to submit builds)
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/cloudbuild.builds.editor" > /dev/null

# 4. Generate Key File
echo "📝 Generating JSON Key file..."
KEY_FILE="github-deploy-key.json"

if [ -f "$KEY_FILE" ]; then
    echo "⚠️ Key file $KEY_FILE already exists. Please remove it first if you want to generate a new one."
else
    gcloud iam service-accounts keys create "$KEY_FILE" \
        --iam-account="$SA_EMAIL" \
        --project "$PROJECT_ID"
    
    echo "✅ Key generated: $KEY_FILE"
fi

echo ""
echo "🎉 CI/CD Setup Complete!"
echo "---------------------------------------------------"
echo "NEXT STEPS:"
echo "1. Go to your GitHub Repository Settings -> Secrets and variables -> Actions"
echo "2. Create a 'New repository secret'"
echo "   - Name: GCP_CREDENTIALS"
echo "   - Value: (Paste the entire content of $KEY_FILE)"
echo "3. Runs 'cat $KEY_FILE' to see the content."
echo "4. IMPORTANT: DELETE $KEY_FILE after adding it to GitHub!"
echo "---------------------------------------------------"
