#!/bin/bash

# Setup script for edvolution-admon project
# Run this after gcloud is installed

set -e

echo "🚀 Setting up Employee Portal for edvolution-admon"
echo "=================================================="
echo ""

# Reload shell to get gcloud in PATH
export PATH="$HOME/google-cloud-sdk/bin:$PATH"

# Login to Google Cloud
echo "📝 Step 1: Authenticating with Google Cloud..."
echo "A browser window will open for authentication."
echo ""
gcloud auth login

echo ""
echo "📝 Step 2: Setting up application credentials..."
echo "Another browser window will open."
echo ""
gcloud auth application-default login

echo ""
echo "📝 Step 3: Setting project to edvolution-admon..."
gcloud config set project edvolution-admon

echo ""
echo "📝 Step 4: Enabling required Google Cloud APIs..."
echo "This will take a few minutes..."
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
echo "✅ APIs enabled!"
echo ""

echo "📝 Step 5: Creating Firestore database..."
if gcloud firestore databases list --format="value(name)" 2>/dev/null | grep -q "(default)"; then
    echo "✅ Firestore database already exists"
else
    echo "Creating Firestore database in us-central1..."
    gcloud firestore databases create --location=us-central1
    echo "✅ Firestore database created"
fi

echo ""
echo "=================================================="
echo "✅ Google Cloud Setup Complete!"
echo "=================================================="
echo ""
echo "Project: edvolution-admon"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Create OAuth credentials:"
echo "   https://console.cloud.google.com/apis/credentials?project=edvolution-admon"
echo ""
echo "2. Set up OAuth Consent Screen:"
echo "   https://console.cloud.google.com/apis/credentials/consent?project=edvolution-admon"
echo ""
echo "3. Configure Domain-wide Delegation:"
echo "   https://admin.google.com/ac/owl/domainwidedelegation"
echo ""
echo "4. Then configure the application:"
echo "   cd /home/dirk/employee-portal"
echo "   nano .env"
echo ""
