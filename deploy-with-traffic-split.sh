#!/bin/bash

# Deploy to Cloud Run with Traffic Splitting (Zero-Downtime Testing)
# This deploys the new code as a revision with 0% traffic initially

set -e  # Exit on error

echo "🚀 Cloud Run Traffic Split Deployment"
echo "======================================"
echo ""

# ============================================
# CONFIGURATION - UPDATE THESE VALUES
# ============================================
PROJECT_ID="your-gcp-project-id"           # TODO: Replace with your GCP project ID
REGION="us-central1"                       # TODO: Replace with your region (e.g., us-central1, europe-west1)
BACKEND_SERVICE="employee-portal-backend"  # TODO: Replace with your backend service name
FRONTEND_SERVICE="employee-portal-frontend" # TODO: Replace with your frontend service name

# ============================================
# Confirm Configuration
# ============================================
echo "📋 Configuration:"
echo "   Project ID: $PROJECT_ID"
echo "   Region: $REGION"
echo "   Backend Service: $BACKEND_SERVICE"
echo "   Frontend Service: $FRONTEND_SERVICE"
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

# ============================================
# DEPLOY BACKEND (with 0% traffic)
# ============================================
echo ""
echo "🔧 Deploying Backend (new revision with 0% traffic)..."
cd backend

gcloud run deploy $BACKEND_SERVICE \
  --source . \
  --platform managed \
  --region $REGION \
  --no-traffic \
  --tag test

echo "✅ Backend revision deployed (receiving 0% traffic)"

# Get the test URL for backend
BACKEND_TEST_URL=$(gcloud run services describe $BACKEND_SERVICE \
  --region $REGION \
  --format 'value(status.traffic.where(tag="test").url)' 2>/dev/null || echo "")

if [ -z "$BACKEND_TEST_URL" ]; then
    # Fallback: get the tagged URL another way
    BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE --region $REGION --format 'value(status.url)')
    BACKEND_TEST_URL="${BACKEND_URL/https:\/\//https://test---}"
fi

echo "🔗 Backend Test URL: $BACKEND_TEST_URL"

# ============================================
# DEPLOY FRONTEND (with 0% traffic)
# ============================================
echo ""
echo "🎨 Deploying Frontend (new revision with 0% traffic)..."
cd ../frontend

# Note: Frontend will use the production backend URL by default
# If you need to test with the test backend, uncomment below:
# echo "VITE_API_URL=$BACKEND_TEST_URL" > .env.production

gcloud run deploy $FRONTEND_SERVICE \
  --source . \
  --platform managed \
  --region $REGION \
  --no-traffic \
  --tag test

echo "✅ Frontend revision deployed (receiving 0% traffic)"

# Get the test URL for frontend
FRONTEND_TEST_URL=$(gcloud run services describe $FRONTEND_SERVICE \
  --region $REGION \
  --format 'value(status.traffic.where(tag="test").url)' 2>/dev/null || echo "")

if [ -z "$FRONTEND_TEST_URL" ]; then
    # Fallback
    FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE --region $REGION --format 'value(status.url)')
    FRONTEND_TEST_URL="${FRONTEND_URL/https:\/\//https://test---}"
fi

# ============================================
# DEPLOYMENT SUMMARY
# ============================================
echo ""
echo "======================================"
echo "✅ Deployment Complete!"
echo "======================================"
echo ""
echo "🔍 TEST URLs (0% traffic - only you can access these):"
echo "   Frontend: $FRONTEND_TEST_URL"
echo "   Backend:  $BACKEND_TEST_URL"
echo ""
echo "🌐 PRODUCTION URLs (still running old version):"
PROD_BACKEND=$(gcloud run services describe $BACKEND_SERVICE --region $REGION --format 'value(status.url)')
PROD_FRONTEND=$(gcloud run services describe $FRONTEND_SERVICE --region $REGION --format 'value(status.url)')
echo "   Frontend: $PROD_FRONTEND"
echo "   Backend:  $PROD_BACKEND"
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. TEST the new version:"
echo "   Open: $FRONTEND_TEST_URL"
echo "   Log in as a manager user"
echo "   Click 'My Team' → Click 'View' on an employee"
echo "   Test all 4 tabs (Overview, Time-Off, Performance, Contract)"
echo ""
echo "2. When testing is successful, PROMOTE to production:"
echo "   ./promote-to-production.sh"
echo ""
echo "3. If there are issues, ROLLBACK:"
echo "   ./rollback-deployment.sh"
echo ""
echo "💡 TIP: The test URL will remain active until you promote or delete the revision."
echo ""
