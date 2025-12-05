#!/bin/bash

# Employee Portal Quick Start Script
# This script automates the initial setup process

set -e

echo "🚀 Employee Portal Quick Start"
echo "=============================="
echo ""

# Check if running in employee-portal directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Please run this script from the employee-portal directory"
    exit 1
fi

# Step 1: Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Step 2: Project setup
echo "🔧 Setting up Google Cloud Project..."
read -p "Enter your GCP Project ID: " PROJECT_ID
gcloud config set project $PROJECT_ID

echo ""
read -p "Enable required Google Cloud APIs? (y/n): " ENABLE_APIS
if [ "$ENABLE_APIS" = "y" ]; then
    echo "Enabling APIs..."
    gcloud services enable \
        run.googleapis.com \
        firestore.googleapis.com \
        secretmanager.googleapis.com \
        admin.googleapis.com \
        calendar-json.googleapis.com \
        gmail.googleapis.com \
        cloudbuild.googleapis.com
    echo "✅ APIs enabled"
fi

# Step 3: Create .env file
echo ""
echo "📝 Creating environment configuration..."

if [ -f ".env" ]; then
    read -p ".env file already exists. Overwrite? (y/n): " OVERWRITE
    if [ "$OVERWRITE" != "y" ]; then
        echo "Skipping .env creation"
    else
        create_env=true
    fi
else
    create_env=true
fi

if [ "$create_env" = true ]; then
    cp .env.example .env

    read -p "Enter your Workspace domain (e.g., company.com): " DOMAIN
    read -p "Enter admin email: " ADMIN_EMAIL
    read -p "Enter Google OAuth Client ID: " CLIENT_ID
    read -sp "Enter Google OAuth Client Secret: " CLIENT_SECRET
    echo ""

    # Generate Flask secret key
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

    # Update .env file
    sed -i "s/your-project-id/$PROJECT_ID/g" .env
    sed -i "s/yourcompany.com/$DOMAIN/g" .env
    sed -i "s/admin@yourcompany.com/$ADMIN_EMAIL/g" .env
    sed -i "s/your-client-id.apps.googleusercontent.com/$CLIENT_ID/g" .env
    sed -i "s/your-client-secret/$CLIENT_SECRET/g" .env
    sed -i "s/your-secret-key-change-in-production/$SECRET_KEY/g" .env

    echo "✅ .env file created"
fi

# Step 4: Python environment
echo ""
echo "🐍 Setting up Python environment..."

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "Virtual environment already exists"
fi

source venv/bin/activate
pip install -q -r requirements.txt
echo "✅ Dependencies installed"

# Step 5: Authentication
echo ""
read -p "Authenticate with Google Cloud? (y/n): " DO_AUTH
if [ "$DO_AUTH" = "y" ]; then
    gcloud auth login
    gcloud auth application-default login
    echo "✅ Authenticated"
fi

# Step 6: Firestore check
echo ""
echo "🔍 Checking Firestore database..."
if gcloud firestore databases list --format="value(name)" | grep -q "(default)"; then
    echo "✅ Firestore database exists"
else
    echo "⚠️  Firestore database not found"
    read -p "Create Firestore database in us-central1? (y/n): " CREATE_DB
    if [ "$CREATE_DB" = "y" ]; then
        gcloud firestore databases create --region=us-central1
        echo "✅ Firestore database created"
    fi
fi

# Step 7: Summary and next steps
echo ""
echo "=============================="
echo "✅ Quick Start Complete!"
echo "=============================="
echo ""
echo "📚 Next Steps:"
echo ""
echo "1. Configure OAuth Consent Screen:"
echo "   → https://console.cloud.google.com/apis/credentials/consent"
echo ""
echo "2. Set up Domain-wide Delegation:"
echo "   → https://admin.google.com/ac/owl/domainwidedelegation"
echo "   → See SETUP_GUIDE.md for detailed instructions"
echo ""
echo "3. Start the development server:"
echo "   source venv/bin/activate"
echo "   python -m backend.app.main"
echo ""
echo "4. Open your browser to:"
echo "   http://localhost:8080"
echo ""
echo "5. For production deployment:"
echo "   ./deploy.sh production"
echo ""
echo "📖 Full documentation: README.md and SETUP_GUIDE.md"
echo ""
