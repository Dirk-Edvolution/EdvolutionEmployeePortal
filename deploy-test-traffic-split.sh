#!/bin/bash

# Deploy Employee Portal with Traffic Splitting (0% traffic for testing)
# Based on your existing deploy.sh but adds traffic management

set -e

PROJECT_ID="edvolution-admon"
REGION="us-central1"
SERVICE_NAME="employee-portal"

echo "🚀 Deploying Employee Portal with Traffic Splitting"
echo "======================================"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo ""
echo "⚠️  This will deploy a new revision with 0% traffic for testing."
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled."
    exit 1
fi

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

# Get current environment variables from production
echo "📋 Fetching current configuration from production..."
CURRENT_ENV=$(gcloud run services describe $SERVICE_NAME --region $REGION --format='value(spec.template.spec.containers[0].env)')

# Deploy to Cloud Run with NO TRAFFIC and TEST tag
echo "🚢 Deploying new revision (0% traffic, tagged 'test')..."
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
  --no-traffic \
  --tag test

echo ""
echo "======================================"
echo "✅ Deployment Complete!"
echo "======================================"
echo ""

# Get URLs
PROD_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
TEST_URL="https://test---${PROD_URL#https://}"

echo "🔍 TEST URL (0% traffic - only you can access):"
echo "   $TEST_URL"
echo ""
echo "🌐 PRODUCTION URL (still running old version):"
echo "   $PROD_URL"
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. TEST the new version:"
echo "   Open: $TEST_URL"
echo "   Log in as a manager user"
echo "   Navigate to 'My Team'"
echo "   Click 'View' on any employee"
echo "   Test all 4 tabs: Overview, Time-Off History, Performance, Contract Info"
echo ""
echo "2. Verify security (you should NOT see):"
echo "   - Salary/compensation information"
echo "   - Personal home addresses"
echo "   - Emergency contact details"
echo ""
echo "3. When testing is successful:"
echo "   ./promote-test-to-production.sh"
echo ""
echo "4. If there are issues:"
echo "   ./rollback-to-previous.sh"
echo ""
echo "💡 The test URL will remain active until you promote or delete the revision."
echo ""
