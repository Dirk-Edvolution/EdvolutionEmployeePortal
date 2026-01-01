#!/bin/bash

# Cleanup Test Services from Google Cloud Run

echo "🗑️  Cleaning up Test Services..."
echo "==============================="
echo ""

# Configuration
PROJECT_ID="your-gcp-project-id"  # TODO: Replace with your GCP project ID
REGION="us-central1"              # TODO: Replace with your region
SERVICE_NAME="employee-portal-test"

# Confirm
echo "⚠️  This will delete:"
echo "   - $SERVICE_NAME-backend"
echo "   - $SERVICE_NAME-frontend"
echo ""
read -p "Are you sure? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cleanup cancelled."
    exit 1
fi

# Set project
gcloud config set project $PROJECT_ID

# Delete services
echo "Deleting backend service..."
gcloud run services delete $SERVICE_NAME-backend --region $REGION --quiet

echo "Deleting frontend service..."
gcloud run services delete $SERVICE_NAME-frontend --region $REGION --quiet

echo ""
echo "✅ Test services deleted successfully!"
echo ""
