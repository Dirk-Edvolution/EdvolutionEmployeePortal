#!/bin/bash

# Promote the test revision to production (send 100% traffic to new version)

set -e

echo "🚀 Promoting to Production"
echo "=========================="
echo ""

# ============================================
# CONFIGURATION - MUST MATCH deploy-with-traffic-split.sh
# ============================================
PROJECT_ID="your-gcp-project-id"           # TODO: Replace
REGION="us-central1"                       # TODO: Replace
BACKEND_SERVICE="employee-portal-backend"  # TODO: Replace
FRONTEND_SERVICE="employee-portal-frontend" # TODO: Replace

# Confirm
echo "⚠️  This will send 100% of production traffic to the new version."
echo ""
read -p "Have you tested the new version? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Promotion cancelled. Please test first using the test URL."
    exit 1
fi

# Set project
gcloud config set project $PROJECT_ID

# Promote backend
echo "🔧 Promoting backend to 100% traffic..."
gcloud run services update-traffic $BACKEND_SERVICE \
  --to-latest \
  --region $REGION

echo "✅ Backend promoted!"

# Promote frontend
echo "🎨 Promoting frontend to 100% traffic..."
gcloud run services update-traffic $FRONTEND_SERVICE \
  --to-latest \
  --region $REGION

echo "✅ Frontend promoted!"

echo ""
echo "======================================"
echo "✅ Promotion Complete!"
echo "======================================"
echo ""
echo "🌐 Production is now running the new version."
echo ""
echo "📊 Monitor your application:"
PROD_FRONTEND=$(gcloud run services describe $FRONTEND_SERVICE --region $REGION --format 'value(status.url)')
echo "   $PROD_FRONTEND"
echo ""
echo "📈 Check Cloud Run logs:"
echo "   https://console.cloud.google.com/run?project=$PROJECT_ID"
echo ""
echo "⚠️  If issues occur, you can rollback:"
echo "   ./rollback-deployment.sh"
echo ""
