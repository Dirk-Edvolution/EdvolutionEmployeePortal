#!/bin/bash
# Monitor Google Chat webhook activity in Cloud Run logs

echo "🔍 Monitoring Google Chat Webhook Activity..."
echo "Press Ctrl+C to stop"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Tail the logs
gcloud logging tail "resource.type=cloud_run_revision \
  AND resource.labels.service_name=employee-portal \
  AND (textPayload=~\"Chat\" OR textPayload=~\"chat\" OR jsonPayload.message=~\"chat\")" \
  --format="table(timestamp,severity,textPayload,jsonPayload.message)" \
  --project=edvolution-admon

