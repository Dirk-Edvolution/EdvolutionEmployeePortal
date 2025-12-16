#!/bin/bash

# Employee Portal Deployment Script for Google Cloud Run
# Usage: ./deploy.sh [environment]
# Example: ./deploy.sh production

set -e

ENVIRONMENT=${1:-development}
PROJECT_ID="edvolution-admon"
REGION=${GCP_LOCATION:-us-central1}
SERVICE_NAME="employee-portal"

echo "🚀 Deploying Employee Portal to Google Cloud Run"
echo "Environment: $ENVIRONMENT"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Set the project
echo "📦 Setting GCP project..."
gcloud config set project $PROJECT_ID

# Build the container
echo "🔨 Building container image..."
IMAGE_URL="us-central1-docker.pkg.dev/$PROJECT_ID/my-repo/$SERVICE_NAME"
gcloud builds submit --tag $IMAGE_URL \
  --service-account="projects/${PROJECT_ID}/serviceAccounts/github-actions-deployer@${PROJECT_ID}.iam.gserviceaccount.com" \
  --gcs-source-staging-dir="gs://${PROJECT_ID}-staging/source" \
  --gcs-log-dir="gs://${PROJECT_ID}-staging/logs"

# Get the service URL (if it exists, to build correct redirect URI)
echo "🔍 Checking for existing service..."
EXISTING_SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)' 2>/dev/null || echo "")

if [ -z "$EXISTING_SERVICE_URL" ]; then
  echo "⚠️  Service not found. Using placeholder URL for GOOGLE_REDIRECT_URI."
  REDIRECT_URI="https://${SERVICE_NAME}-5n2ivebvra-uc.a.run.app/auth/callback"
else
  REDIRECT_URI="${EXISTING_SERVICE_URL}/auth/callback"
  echo "✓ Using existing service URL for redirect: $REDIRECT_URI"
fi

# Deploy to Cloud Run
echo "🚢 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_URL \
  --platform managed \
  --service-account employee-portal-runtime@${PROJECT_ID}.iam.gserviceaccount.com \
  --region $REGION \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars "^@^GCP_PROJECT_ID=${PROJECT_ID}@GCP_LOCATION=${REGION}@GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}@GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}@GOOGLE_REDIRECT_URI=https://${SERVICE_NAME}-5n2ivebvra-uc.a.run.app/auth/callback@FLASK_SECRET_KEY=a728c9a60328bdcd7036910d5f1850c38724dfea9fa50034a07806a9b68112ef@FLASK_ENV=${ENVIRONMENT}@WORKSPACE_DOMAIN=${WORKSPACE_DOMAIN}@WORKSPACE_ADMIN_EMAIL=${WORKSPACE_ADMIN_EMAIL}@ADMIN_USERS=${ADMIN_USERS}"

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')

echo "✅ Deployment complete!"
echo "🌐 Service URL: $SERVICE_URL"
echo ""
echo "📝 Important Notes:"
echo "1. OAuth redirect URI is set to: ${REDIRECT_URI}"
echo "2. Make sure this matches the authorized redirect URI in Google Cloud Console"
echo "3. FLASK_SECRET_KEY and OAuth credentials are set from environment variables"
echo ""
echo "Environment variables used:"
echo "  - GOOGLE_CLIENT_ID (from env)"
echo "  - GOOGLE_CLIENT_SECRET (from env)"
echo "  - FLASK_SECRET_KEY (from env)"
echo "  - WORKSPACE_DOMAIN=${WORKSPACE_DOMAIN}"
echo "  - ADMIN_USERS=${ADMIN_USERS}"
