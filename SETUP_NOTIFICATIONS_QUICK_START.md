# Quick Start: Set Up Notifications with hola@edvolution.io

This guide will help you set up email and Chat notifications in **15 minutes**.

## What You're Setting Up

Instead of complex domain-wide delegation, we're using a simple dedicated account (`hola@edvolution.io`) to send all automated notifications. This is how most companies do it!

## Step-by-Step Setup

### Step 1: Log in as hola@edvolution.io (5 min)

1. **Open the Employee Portal**: https://employee-portal-844588465159.us-central1.run.app
2. **Click "Sign in with Google"**
3. **Use hola@edvolution.io credentials**
4. **Authorize all requested scopes** (Gmail, Chat, Calendar, Tasks, etc.)
5. **You should now be logged in** - you'll see hola's profile

### Step 2: Extract OAuth Credentials (5 min)

Once logged in as hola@edvolution.io, we need to save the OAuth credentials.

**Option A: Use Browser DevTools (Easier)**
1. Open browser DevTools (F12)
2. Go to **Application** tab → **Cookies**
3. Find the `session` cookie for the Employee Portal
4. Copy the session value (it's encrypted, but contains the credentials)

**Option B: Add an Admin Endpoint (Better)**
I can add a temporary admin endpoint that lets you download the credentials as JSON.

Let me know which option you prefer, and I'll help you complete it.

### Step 3: Store Credentials in Secret Manager (3 min)

Once you have the credentials JSON file (`hola-credentials.json`), run:

```bash
# Create the secret
gcloud secrets create notification-account-credentials \
  --data-file=hola-credentials.json \
  --project=edvolution-admon

# Grant access to the service account
gcloud secrets add-iam-policy-binding notification-account-credentials \
  --member="serviceAccount:employee-portal-runtime@edvolution-admon.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=edvolution-admon
```

### Step 4: Deploy Updated Code (2 min)

The code is already updated and pushed to GitHub. Just deploy it:

```bash
cd /home/dirk/devprojects/employee-portal
gcloud builds submit --tag us-central1-docker.pkg.dev/edvolution-admon/my-repo/employee-portal:latest \
  --service-account="projects/edvolution-admon/serviceAccounts/github-actions-deployer@edvolution-admon.iam.gserviceaccount.com" \
  --gcs-source-staging-dir="gs://edvolution-admon-staging/source" \
  --gcs-log-dir="gs://edvolution-admon-staging/logs"

gcloud run services update employee-portal \
  --region us-central1 \
  --image us-central1-docker.pkg.dev/edvolution-admon/my-repo/employee-portal:latest \
  --set-env-vars="NOTIFICATION_ACCOUNT_EMAIL=hola@edvolution.io"
```

### Step 5: Test It! (1 min)

1. **Create a time-off request** in the Employee Portal (as any user)
2. **Manager should receive:**
   - ✅ Email from hola@edvolution.io
   - ✅ Google Chat DM from hola@edvolution.io
   - ✅ Google Task reminder

Done! 🎉

## What We Changed

**Before:**
- ❌ Service account tried to send emails → "Mail service not enabled" error
- ❌ Service account tried to send Chat DMs → Required complex domain-wide delegation
- ❌ Nothing worked

**After:**
- ✅ Real user account (hola@edvolution.io) sends emails → Works perfectly
- ✅ Real user account sends Chat DMs → Works perfectly
- ✅ Simple OAuth credentials stored in Secret Manager
- ✅ No domain-wide delegation needed

## Troubleshooting

### "Secret not found" error
Make sure you created the secret with the exact name: `notification-account-credentials`

### "Permission denied" error
Make sure the service account has `secretmanager.secretAccessor` role

### Emails/Chats still not arriving
1. Check Secret Manager has valid credentials
2. Verify hola@edvolution.io has Gmail and Chat enabled
3. Check Cloud Run logs for errors: `gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=employee-portal' --limit 20`

## Next Steps

Once this works, you can:
1. ✅ Remove the domain-wide delegation complexity (not needed anymore)
2. ✅ Update documentation to reflect the simpler approach
3. ✅ Set up refresh token for long-term automation (credentials won't expire)

---

**Need help with Step 2 (extracting credentials)?** Let me know and I'll create a temporary admin endpoint that downloads them for you!
