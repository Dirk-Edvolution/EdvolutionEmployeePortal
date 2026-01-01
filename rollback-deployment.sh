#!/bin/bash

# Rollback to the previous revision (if new version has issues)

set -e

echo "⏮️  Rollback Deployment"
echo "======================"
echo ""

# ============================================
# CONFIGURATION - MUST MATCH deploy-with-traffic-split.sh
# ============================================
PROJECT_ID="your-gcp-project-id"           # TODO: Replace
REGION="us-central1"                       # TODO: Replace
BACKEND_SERVICE="employee-portal-backend"  # TODO: Replace
FRONTEND_SERVICE="employee-portal-frontend" # TODO: Replace

# Confirm
echo "⚠️  This will rollback to the previous version."
echo ""
read -p "Are you sure you want to rollback? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Rollback cancelled."
    exit 1
fi

# Set project
gcloud config set project $PROJECT_ID

# List current revisions to find the previous one
echo "📋 Finding previous revisions..."

# Get backend revisions
echo ""
echo "Backend revisions:"
gcloud run revisions list \
  --service $BACKEND_SERVICE \
  --region $REGION \
  --format "table(revision,traffic,created)" \
  --limit 5

echo ""
read -p "Enter the backend revision name to rollback to (or press Enter to skip): " BACKEND_REVISION

if [ ! -z "$BACKEND_REVISION" ]; then
    echo "⏮️  Rolling back backend to: $BACKEND_REVISION"
    gcloud run services update-traffic $BACKEND_SERVICE \
      --to-revisions $BACKEND_REVISION=100 \
      --region $REGION
    echo "✅ Backend rolled back!"
fi

# Get frontend revisions
echo ""
echo "Frontend revisions:"
gcloud run revisions list \
  --service $FRONTEND_SERVICE \
  --region $REGION \
  --format "table(revision,traffic,created)" \
  --limit 5

echo ""
read -p "Enter the frontend revision name to rollback to (or press Enter to skip): " FRONTEND_REVISION

if [ ! -z "$FRONTEND_REVISION" ]; then
    echo "⏮️  Rolling back frontend to: $FRONTEND_REVISION"
    gcloud run services update-traffic $FRONTEND_SERVICE \
      --to-revisions $FRONTEND_REVISION=100 \
      --region $REGION
    echo "✅ Frontend rolled back!"
fi

echo ""
echo "======================================"
echo "✅ Rollback Complete!"
echo "======================================"
echo ""
echo "🌐 Production is now running the previous version."
echo ""
PROD_FRONTEND=$(gcloud run services describe $FRONTEND_SERVICE --region $REGION --format 'value(status.url)')
echo "   $PROD_FRONTEND"
echo ""
