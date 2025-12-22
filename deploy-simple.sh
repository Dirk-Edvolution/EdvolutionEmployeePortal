#!/bin/bash

# Employee Portal Deployment Script for Google Cloud Run (Simplified)
# Usage: ./deploy-simple.sh

set -e

PROJECT_ID="edvolution-admon"
REGION="us-central1"
SERVICE_NAME="employee-portal"

echo "🚀 Deploying Employee Portal to Google Cloud Run"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"

# Set the project
gcloud config set project $PROJECT_ID

# Build the container
echo "🔨 Building container image..."
IMAGE_URL="us-central1-docker.pkg.dev/$PROJECT_ID/my-repo/$SERVICE_NAME"
gcloud builds submit --tag $IMAGE_URL

# Deploy to Cloud Run (keeps existing env vars)
echo "🚢 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_URL \
  --platform managed \
  --region $REGION

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')

echo "✅ Deployment complete!"
echo "🌐 Service URL: $SERVICE_URL"
echo ""
echo "📝 Note: All environment variables and secrets were preserved from existing deployment"
