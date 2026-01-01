#!/bin/bash

# Promote the test revision to production (100% traffic)

set -e

PROJECT_ID="edvolution-admon"
REGION="us-central1"
SERVICE_NAME="employee-portal"

echo "🚀 Promoting Test Version to Production"
echo "========================================"
echo ""
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

# Promote to 100% traffic
echo "🚀 Promoting to 100% traffic..."
gcloud run services update-traffic $SERVICE_NAME \
  --to-latest \
  --region $REGION

SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')

echo ""
echo "======================================"
echo "✅ Promotion Complete!"
echo "======================================"
echo ""
echo "🌐 Production URL: $SERVICE_URL"
echo ""
echo "📊 Monitor your application:"
echo "   https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME?project=$PROJECT_ID"
echo ""
echo "📈 Check logs:"
echo "   gcloud run services logs read $SERVICE_NAME --region $REGION --limit 50"
echo ""
echo "⚠️  If issues occur, you can rollback:"
echo "   ./rollback-to-previous.sh"
echo ""
