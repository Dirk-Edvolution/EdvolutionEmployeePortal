# Cloud Run Traffic Splitting Deployment Guide

## Overview

This guide explains how to safely deploy the new manager features to production using Cloud Run's traffic splitting capability.

## How It Works

**Traffic Splitting** lets you deploy a new version of your code alongside the current production version:

1. **Deploy** new code as a revision with 0% traffic
2. **Test** the new version using a special test URL (only you can access it)
3. **Promote** to 100% traffic when ready (or rollback if issues)

## Environment Variables & Secrets

### ✅ Good News: Everything is Automatically Inherited!

When you deploy a new revision to the **same service**, it inherits:

- ✅ **All environment variables** (DATABASE_URL, ADMIN_USERS, etc.)
- ✅ **All secrets from Secret Manager** (API keys, credentials, etc.)
- ✅ **Service account** and its permissions
- ✅ **All configuration** (memory, CPU, timeout, etc.)

**You don't need to configure anything** - it just works!

### How Secrets Work

If you're using Google Secret Manager (which you should be):

```bash
# Your current production service probably has secrets like:
--set-secrets="GOOGLE_CLIENT_SECRET=google-oauth-secret:latest"
--set-secrets="DATABASE_PASSWORD=db-password:latest"
```

When you deploy a new revision:
- ✅ The new revision automatically gets the same secret references
- ✅ It reads the same secret values from Secret Manager
- ✅ No manual configuration needed

### Same Database, Same Everything

Since it's the **same service**, the new revision uses:
- ✅ Same Firestore database
- ✅ Same Google OAuth credentials
- ✅ Same service account permissions
- ✅ Same VPC network (if any)

**Only the code changes!**

## Step-by-Step Instructions

### Prerequisites

1. You have a Cloud Run service already deployed in production
2. You have `gcloud` CLI installed and authenticated
3. You know your GCP project ID, region, and service names

### Step 1: Configure the Scripts

Edit **all three scripts** and replace these values:

```bash
PROJECT_ID="your-gcp-project-id"           # Example: "my-company-prod"
REGION="us-central1"                       # Example: "us-central1" or "europe-west1"
BACKEND_SERVICE="employee-portal-backend"  # Your backend service name
FRONTEND_SERVICE="employee-portal-frontend" # Your frontend service name
```

**How to find these values:**

```bash
# List your Cloud Run services
gcloud run services list

# Get project ID
gcloud config get-value project

# Get region from existing service
gcloud run services describe YOUR-SERVICE-NAME --format="value(region)"
```

### Step 2: Make Scripts Executable

```bash
chmod +x deploy-with-traffic-split.sh
chmod +x promote-to-production.sh
chmod +x rollback-deployment.sh
```

### Step 3: Deploy with 0% Traffic

```bash
./deploy-with-traffic-split.sh
```

**What this does:**
- Builds and deploys your code from the current branch
- Creates a new revision with a "test" tag
- Routes 0% of production traffic to it
- Gives you a special test URL to test the new version
- Production continues running the old version (100% traffic)

**Expected output:**
```
✅ Deployment Complete!
🔍 TEST URLs (0% traffic - only you can access these):
   Frontend: https://test---employee-portal-frontend-abc123.a.run.app
   Backend:  https://test---employee-portal-backend-abc123.a.run.app

🌐 PRODUCTION URLs (still running old version):
   Frontend: https://employee-portal-frontend-abc123.a.run.app
   Backend:  https://employee-portal-backend-abc123.a.run.app
```

### Step 4: Test the New Version

1. Open the **test frontend URL** in your browser
2. Log in with a manager account
3. Navigate to "My Team"
4. Click "👁️ View" on any team member
5. Test all 4 tabs:
   - **Overview**: Basic employee info
   - **Time-Off History**: Past time-off requests
   - **Performance**: Add an evaluation and follow-up
   - **Contract Info**: Contract type and dates

**Verify security:**
- ✅ You should NOT see salary information
- ✅ You should NOT see personal addresses
- ✅ You should NOT see emergency contacts

### Step 5: Promote to Production

If everything works correctly:

```bash
./promote-to-production.sh
```

**What this does:**
- Routes 100% of traffic to the new revision
- Production users now see the new features
- Old revision stays available for quick rollback

### Step 6: Monitor (Optional but Recommended)

After promotion, monitor for 10-15 minutes:

```bash
# Watch Cloud Run logs
gcloud run services logs read FRONTEND-SERVICE-NAME --region REGION --limit 50

# Or open in Cloud Console
https://console.cloud.google.com/run?project=YOUR-PROJECT-ID
```

**Look for:**
- ✅ No error spikes
- ✅ Successful API calls
- ✅ Users accessing the new features

### Emergency: Rollback

If you notice issues after promotion:

```bash
./rollback-deployment.sh
```

**What this does:**
- Shows you a list of recent revisions
- Lets you select which revision to rollback to
- Routes 100% traffic back to the selected revision
- New version stays available for debugging

## Architecture Diagram

```
┌─────────────────────────────────────────────┐
│         Cloud Run Service (Same)            │
├─────────────────────────────────────────────┤
│                                             │
│  Revision 1 (Old) ──────► 100% traffic      │ ← Production
│  Environment: All secrets, configs          │
│                                             │
│  Revision 2 (New) ──────► 0% traffic        │ ← Test URL
│  Environment: Same secrets, configs         │ (only you access)
│                                             │
└─────────────────────────────────────────────┘
          │
          │ Both use same:
          ├─► Firestore Database
          ├─► Secret Manager secrets
          ├─► Service Account
          └─► Google OAuth credentials
```

After promotion:
```
┌─────────────────────────────────────────────┐
│         Cloud Run Service (Same)            │
├─────────────────────────────────────────────┤
│                                             │
│  Revision 1 (Old) ──────► 0% traffic        │ ← Available for rollback
│                                             │
│  Revision 2 (New) ──────► 100% traffic      │ ← Production
│                                             │
└─────────────────────────────────────────────┘
```

## Costs

**Traffic splitting costs nothing extra!**

- ✅ You only pay for the traffic each revision receives
- ✅ Test URL (0% traffic) = almost $0 (just your test requests)
- ✅ After promotion, old revision costs $0 (no traffic)
- ✅ Cloud Run only charges for actual usage

## Frequently Asked Questions

### Q: Will this affect my production users?
**A:** No! The new revision gets 0% traffic initially. Production users continue using the old version until you explicitly promote.

### Q: Do I need to reconfigure secrets?
**A:** No! The new revision automatically inherits all secrets from the service configuration.

### Q: Can I test with real data?
**A:** Yes! The test URL uses the same database as production. Any data you create during testing is real (e.g., evaluations you add will be stored).

### Q: What if I find bugs during testing?
**A:** Just don't promote! The new revision will stay at 0% traffic. Fix the bugs, and deploy a new revision with the fixes.

### Q: How do I delete the test revision?
**A:** Cloud Run automatically keeps the last few revisions. Old revisions with 0% traffic are automatically cleaned up after ~90 days. Or manually delete:

```bash
gcloud run revisions delete REVISION-NAME --region REGION
```

### Q: Can I gradually increase traffic (like 10%, then 50%, then 100%)?
**A:** Yes! But for this deployment, 0%→100% is fine since it's just new features (not changing existing behavior).

```bash
# If you want gradual rollout:
gcloud run services update-traffic SERVICE-NAME \
  --to-revisions LATEST=10,PREVIOUS=90 \
  --region REGION
```

## Troubleshooting

### Issue: "Permission denied" error
**Solution:** Make sure you're authenticated and have the correct role:
```bash
gcloud auth login
gcloud config set project YOUR-PROJECT-ID

# You need one of these roles:
# - Cloud Run Admin
# - Cloud Run Developer
```

### Issue: Can't access test URL
**Solution:** Test URLs are public by default (since your service is `--allow-unauthenticated`). If you can't access:
1. Check if the URL is correct (should start with `https://test---`)
2. Try in incognito mode
3. Check Cloud Run logs for errors

### Issue: Frontend can't connect to backend
**Solution:** Make sure your frontend's API URL points to the correct backend. Check `frontend/.env.production` or your build configuration.

### Issue: Database errors during testing
**Solution:** This is unlikely since we're using the same database. If you see errors:
1. Check Cloud Run logs
2. Verify Firestore security rules
3. Verify service account has Firestore permissions

## Summary

**Traffic splitting is the safest way to deploy** because:

1. ✅ Zero downtime (production keeps running)
2. ✅ Zero configuration (inherits everything)
3. ✅ Easy testing (dedicated test URL)
4. ✅ Quick rollback (if needed)
5. ✅ No cost (only pay for traffic)

**Perfect for your first deployment!** 🚀
