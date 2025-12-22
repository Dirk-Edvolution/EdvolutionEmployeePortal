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

# Set production configuration if not already set
: ${GOOGLE_CLIENT_ID:=""}
: ${GOOGLE_CLIENT_SECRET:=""}
: ${REDIRECT_URI:="https://rrhh.edvolution.io/auth/callback"}
: ${WORKSPACE_DOMAIN:="edvolution.io"}
: ${WORKSPACE_ADMIN_EMAIL:="dirk@edvolution.io"}
: ${ADMIN_USERS:="dirk@edvolution.io"}

# Validate required OAuth credentials
if [ -z "$GOOGLE_CLIENT_ID" ] || [ -z "$GOOGLE_CLIENT_SECRET" ]; then
    echo "❌ ERROR: OAuth credentials not set!"
    echo "Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables"
    echo "Or extract them from Cloud Run:"
    echo "  export GOOGLE_CLIENT_ID=\$(gcloud run services describe employee-portal --region us-central1 --format='value(spec.template.spec.containers[0].env.find({\"name\":\"GOOGLE_CLIENT_ID\"}).value)')"
    echo "  export GOOGLE_CLIENT_SECRET=\$(gcloud run services describe employee-portal --region us-central1 --format='value(spec.template.spec.containers[0].env.find({\"name\":\"GOOGLE_CLIENT_SECRET\"}).value)')"
    exit 1
fi

echo "🔍 OAuth Configuration:"
echo "  - Client ID: ${GOOGLE_CLIENT_ID:0:20}... (hidden)"
echo "  - Redirect URI: ${REDIRECT_URI}"
echo "  - Workspace Domain: ${WORKSPACE_DOMAIN}"

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
  --set-env-vars "GCP_PROJECT_ID=${PROJECT_ID},GCP_LOCATION=${REGION},GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID},GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET},GOOGLE_REDIRECT_URI=${REDIRECT_URI},FLASK_SECRET_KEY=a728c9a60328bdcd7036910d5f1850c38724dfea9fa50034a07806a9b68112ef,FLASK_ENV=${ENVIRONMENT},WORKSPACE_DOMAIN=${WORKSPACE_DOMAIN},WORKSPACE_ADMIN_EMAIL=${WORKSPACE_ADMIN_EMAIL},ADMIN_USERS=${ADMIN_USERS}"

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')

echo "✅ Deployment complete!"
echo "🌐 Service URL: $SERVICE_URL"
echo ""
echo "📝 Configuration Summary:"
echo "  - OAuth Client ID: ${GOOGLE_CLIENT_ID}"
echo "  - OAuth Redirect URI: ${REDIRECT_URI}"
echo "  - Workspace Domain: ${WORKSPACE_DOMAIN}"
echo "  - Admin Users: ${ADMIN_USERS}"
echo ""
echo "⚠️  Make sure ${REDIRECT_URI} is in the authorized redirect URIs in Google Cloud Console"
