#!/bin/bash

# Deploy Test Service to Google Cloud Run
# This deploys the current branch as a separate test service

echo "🚀 Deploying Test Service to Google Cloud Run..."
echo "================================================"
echo ""

# Configuration
PROJECT_ID="your-gcp-project-id"  # TODO: Replace with your GCP project ID
REGION="us-central1"              # TODO: Replace with your region
SERVICE_NAME="employee-portal-test"  # Test service name (different from production)

# Confirm configuration
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Service Name: $SERVICE_NAME"
echo ""
read -p "Is this correct? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled. Please edit this script with correct values."
    exit 1
fi

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI is not installed"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set project
echo "📋 Setting GCP project..."
gcloud config set project $PROJECT_ID

# Deploy Backend
echo ""
echo "🔧 Deploying Backend Test Service..."
cd backend
gcloud run deploy $SERVICE_NAME-backend \
  --source . \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --max-instances 10 \
  --memory 512Mi \
  --timeout 300 \
  --tag test

# Get backend URL
BACKEND_URL=$(gcloud run services describe $SERVICE_NAME-backend --region $REGION --format 'value(status.url)')
echo "✅ Backend deployed: $BACKEND_URL"

# Deploy Frontend
echo ""
echo "🎨 Deploying Frontend Test Service..."
cd ../frontend

# Update API endpoint to point to test backend
echo "VITE_API_URL=$BACKEND_URL" > .env.production

gcloud run deploy $SERVICE_NAME-frontend \
  --source . \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --max-instances 10 \
  --memory 512Mi

# Get frontend URL
FRONTEND_URL=$(gcloud run services describe $SERVICE_NAME-frontend --region $REGION --format 'value(status.url)')

echo ""
echo "================================================"
echo "✅ Test Service Deployed Successfully!"
echo "================================================"
echo ""
echo "🌐 Frontend URL: $FRONTEND_URL"
echo "🔧 Backend URL:  $BACKEND_URL"
echo ""
echo "📝 Next Steps:"
echo "1. Open the frontend URL in your browser"
echo "2. Log in as a manager user"
echo "3. Test the 'My Team' view"
echo "4. Click 'View' on an employee"
echo "5. Test all 4 tabs (Overview, Time-Off, Performance, Contract)"
echo ""
echo "🗑️  To delete test service when done:"
echo "   gcloud run services delete $SERVICE_NAME-backend --region $REGION"
echo "   gcloud run services delete $SERVICE_NAME-frontend --region $REGION"
echo ""
