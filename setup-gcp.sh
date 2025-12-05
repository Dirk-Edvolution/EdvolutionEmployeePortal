#!/bin/bash

# Google Cloud Project Setup Script
# This script enables all required APIs and sets up Firestore

set -e

echo "🔧 Google Cloud Project Setup"
echo "=============================="
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first."
    echo "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get current project
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)

if [ -z "$CURRENT_PROJECT" ]; then
    echo "No project is currently set."
    read -p "Enter your GCP Project ID: " PROJECT_ID
    gcloud config set project $PROJECT_ID
else
    echo "Current project: $CURRENT_PROJECT"
    read -p "Use this project? (y/n): " USE_CURRENT
    if [ "$USE_CURRENT" != "y" ]; then
        read -p "Enter your GCP Project ID: " PROJECT_ID
        gcloud config set project $PROJECT_ID
    else
        PROJECT_ID=$CURRENT_PROJECT
    fi
fi

echo ""
echo "📦 Project: $PROJECT_ID"
echo ""

# Enable required APIs
echo "🔌 Enabling required Google Cloud APIs..."
echo "This may take a few minutes..."
echo ""

gcloud services enable cloudresourcemanager.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable admin.googleapis.com
gcloud services enable calendar-json.googleapis.com
gcloud services enable gmail.googleapis.com
gcloud services enable cloudbuild.googleapis.com

echo ""
echo "✅ All APIs enabled!"
echo ""

# Check Firestore
echo "🔍 Checking Firestore database..."

if gcloud firestore databases list --format="value(name)" 2>/dev/null | grep -q "(default)"; then
    echo "✅ Firestore database already exists"
else
    echo "📊 Firestore database not found"
    read -p "Create Firestore database in us-central1? (y/n): " CREATE_DB
    if [ "$CREATE_DB" = "y" ]; then
        echo "Creating Firestore database..."
        gcloud firestore databases create --region=us-central1
        echo "✅ Firestore database created"
    else
        echo "⚠️  Skipping Firestore creation. You'll need to create it manually."
    fi
fi

echo ""
echo "=============================="
echo "✅ GCP Setup Complete!"
echo "=============================="
echo ""
echo "Project: $PROJECT_ID"
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. Set up OAuth credentials:"
echo "   Open: https://console.cloud.google.com/apis/credentials?project=$PROJECT_ID"
echo ""
echo "2. Then run the application setup:"
echo "   ./quickstart.sh"
echo ""
