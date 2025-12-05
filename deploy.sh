#!/bin/bash

# Employee Portal Deployment Script for Google Cloud Run
# Usage: ./deploy.sh [environment]
# Example: ./deploy.sh production

set -e

ENVIRONMENT=${1:-development}
PROJECT_ID=${GCP_PROJECT_ID}
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
gcloud builds submit --tag $IMAGE_URL

# Deploy to Cloud Run
echo "🚢 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_URL \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars GCP_PROJECT_ID=$PROJECT_ID \
  --set-env-vars GCP_LOCATION=$REGION \
  --set-env-vars FLASK_ENV=$ENVIRONMENT \
  --set-env-vars WORKSPACE_DOMAIN=${WORKSPACE_DOMAIN} \
  --set-env-vars ADMIN_USERS=${ADMIN_USERS}

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')

echo "✅ Deployment complete!"
echo "🌐 Service URL: $SERVICE_URL"
echo ""
echo "📝 Next steps:"
echo "1. Update your OAuth redirect URI to: $SERVICE_URL/auth/callback"
echo "2. Update GOOGLE_REDIRECT_URI environment variable"
echo "3. Configure secrets in Secret Manager"
echo ""
echo "To configure secrets, run:"
echo "  ./setup-secrets.sh"
