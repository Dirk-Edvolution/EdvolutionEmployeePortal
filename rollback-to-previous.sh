#!/bin/bash

# Rollback to the previous revision

set -e

PROJECT_ID="edvolution-admon"
REGION="us-central1"
SERVICE_NAME="employee-portal"

echo "⏮️  Rollback to Previous Version"
echo "================================"
echo ""
echo "⚠️  This will rollback to the previous revision."
echo ""
read -p "Are you sure? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Rollback cancelled."
    exit 1
fi

# Set project
gcloud config set project $PROJECT_ID

# List revisions
echo "📋 Available revisions:"
echo ""
gcloud run revisions list \
  --service $SERVICE_NAME \
  --region $REGION \
  --format "table(revision:label=REVISION,traffic:label=TRAFFIC%,created.date():label=CREATED)" \
  --limit 5

echo ""
echo "The revision with 100% traffic is the current production version."
echo "The one with 0% (or no traffic shown) is likely the previous version."
echo ""
read -p "Enter the revision name to rollback to: " REVISION_NAME

if [ -z "$REVISION_NAME" ]; then
    echo "❌ No revision specified. Rollback cancelled."
    exit 1
fi

# Rollback
echo "⏮️  Rolling back to: $REVISION_NAME"
gcloud run services update-traffic $SERVICE_NAME \
  --to-revisions $REVISION_NAME=100 \
  --region $REGION

SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')

echo ""
echo "======================================"
echo "✅ Rollback Complete!"
echo "======================================"
echo ""
echo "🌐 Production URL: $SERVICE_URL"
echo ""
echo "The service is now running revision: $REVISION_NAME"
echo ""
