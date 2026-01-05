#!/bin/bash

# ============================================================================
# Robert Hebert Media - Google Ads Report Automation Deployment
# ============================================================================

set -e

PROJECT_ID="hendricks-ai-prod"
REGION="us-central1"
FUNCTION_NAME="rhm-google-ads-reports"
SCHEDULER_NAME="rhm-weekly-reports"

echo "=========================================="
echo "Deploying Google Ads Report Automation"
echo "=========================================="

# Check if logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1 > /dev/null 2>&1; then
    echo "Please login to gcloud first: gcloud auth login"
    exit 1
fi

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo ""
echo "Enabling required APIs..."
gcloud services enable \
    cloudfunctions.googleapis.com \
    cloudscheduler.googleapis.com \
    secretmanager.googleapis.com \
    cloudbuild.googleapis.com

# ============================================================================
# STEP 1: Create Secrets (if they don't exist)
# ============================================================================

echo ""
echo "Checking secrets..."

# Google Ads credentials secret
if ! gcloud secrets describe google-ads-credentials --project=$PROJECT_ID > /dev/null 2>&1; then
    echo "Creating google-ads-credentials secret..."
    echo "Please paste your google-ads.yaml content (Ctrl+D when done):"
    gcloud secrets create google-ads-credentials --project=$PROJECT_ID --data-file=-
else
    echo "google-ads-credentials secret already exists"
fi

# GitHub token secret
if ! gcloud secrets describe github-token --project=$PROJECT_ID > /dev/null 2>&1; then
    echo "Creating github-token secret..."
    read -p "Enter your GitHub personal access token: " github_token
    echo -n "$github_token" | gcloud secrets create github-token --project=$PROJECT_ID --data-file=-
else
    echo "github-token secret already exists"
fi

# SendGrid API key secret
if ! gcloud secrets describe sendgrid-api-key --project=$PROJECT_ID > /dev/null 2>&1; then
    echo "Creating sendgrid-api-key secret..."
    read -p "Enter your SendGrid API key: " sendgrid_key
    echo -n "$sendgrid_key" | gcloud secrets create sendgrid-api-key --project=$PROJECT_ID --data-file=-
else
    echo "sendgrid-api-key secret already exists"
fi

# ============================================================================
# STEP 2: Deploy Cloud Function
# ============================================================================

echo ""
echo "Deploying Cloud Function..."

gcloud functions deploy $FUNCTION_NAME \
    --gen2 \
    --runtime python311 \
    --region $REGION \
    --source . \
    --entry-point generate_weekly_reports \
    --trigger-http \
    --allow-unauthenticated \
    --memory 512MB \
    --timeout 540s \
    --set-env-vars GCP_PROJECT=$PROJECT_ID

# Get the function URL
FUNCTION_URL=$(gcloud functions describe $FUNCTION_NAME --region=$REGION --format='value(serviceConfig.uri)')

echo ""
echo "Function deployed at: $FUNCTION_URL"

# ============================================================================
# STEP 3: Grant Secret Access
# ============================================================================

echo ""
echo "Granting secret access to Cloud Function..."

# Get the service account
SERVICE_ACCOUNT=$(gcloud functions describe $FUNCTION_NAME --region=$REGION --format='value(serviceConfig.serviceAccountEmail)')

for secret in google-ads-credentials github-token sendgrid-api-key; do
    gcloud secrets add-iam-policy-binding $secret \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/secretmanager.secretAccessor" \
        --project=$PROJECT_ID
done

# ============================================================================
# STEP 4: Create Cloud Scheduler Job
# ============================================================================

echo ""
echo "Creating Cloud Scheduler job..."

# Delete existing job if it exists
gcloud scheduler jobs delete $SCHEDULER_NAME --location=$REGION --quiet 2>/dev/null || true

# Create new scheduler job - Monday 8:00 AM CST
gcloud scheduler jobs create http $SCHEDULER_NAME \
    --location=$REGION \
    --schedule="0 8 * * 1" \
    --time-zone="America/Chicago" \
    --uri="$FUNCTION_URL" \
    --http-method=POST \
    --oidc-service-account-email=$SERVICE_ACCOUNT

echo ""
echo "=========================================="
echo "DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "Cloud Function: $FUNCTION_URL"
echo "Schedule: Every Monday at 8:00 AM CST"
echo ""
echo "Next steps:"
echo "1. Update clients.json with actual client data"
echo "2. Test manually: curl -X POST $FUNCTION_URL"
echo "3. Check Cloud Scheduler for next run time"
echo ""
