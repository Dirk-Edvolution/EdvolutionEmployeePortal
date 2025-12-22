#!/bin/bash
# Helper script to export OAuth credentials from current Cloud Run deployment
# Usage: source ./export-oauth-vars.sh

PROJECT_ID="edvolution-admon"
SERVICE_NAME="employee-portal"
REGION="us-central1"

echo "📥 Fetching OAuth credentials from Cloud Run service..."

# Get the current environment variables from Cloud Run
ENV_VARS=$(gcloud run services describe $SERVICE_NAME --region $REGION --format=json 2>/dev/null)

if [ $? -ne 0 ]; then
    echo "❌ Failed to fetch service configuration"
    return 1
fi

# Extract OAuth credentials
export GOOGLE_CLIENT_ID=$(echo "$ENV_VARS" | python3 -c "import sys, json; env = json.load(sys.stdin)['spec']['template']['spec']['containers'][0]['env']; print([e['value'] for e in env if e['name'] == 'GOOGLE_CLIENT_ID'][0])" 2>/dev/null)
export GOOGLE_CLIENT_SECRET=$(echo "$ENV_VARS" | python3 -c "import sys, json; env = json.load(sys.stdin)['spec']['template']['spec']['containers'][0]['env']; print([e['value'] for e in env if e['name'] == 'GOOGLE_CLIENT_SECRET'][0])" 2>/dev/null)

if [ -n "$GOOGLE_CLIENT_ID" ] && [ -n "$GOOGLE_CLIENT_SECRET" ]; then
    echo "✅ OAuth credentials exported successfully!"
    echo "   GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID:0:20}..."
    echo "   GOOGLE_CLIENT_SECRET=***"
    echo ""
    echo "You can now run: ./deploy.sh production"
else
    echo "❌ Failed to extract OAuth credentials"
    return 1
fi
