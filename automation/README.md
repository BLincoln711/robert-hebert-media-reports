# Robert Hebert Media - Automated Google Ads Reports

Fully automated weekly Google Ads performance reports for RHM clients.

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                    EVERY MONDAY 8:00 AM CST                      │
│                              ↓                                   │
│                  Cloud Scheduler Trigger                         │
│                              ↓                                   │
│                  Cloud Function (Python)                         │
│                              ↓                                   │
│    ┌─────────────────────────────────────────────────────┐      │
│    │  1. Pull Google Ads API data (last 7 days)          │      │
│    │  2. Calculate week-over-week changes                │      │
│    │  3. Generate branded HTML report                    │      │
│    │  4. Push to GitHub Pages                            │      │
│    │  5. Send email notification with link               │      │
│    └─────────────────────────────────────────────────────┘      │
│                              ↓                                   │
│         reports.roberthebertmedia.com/[client-dates]/            │
└─────────────────────────────────────────────────────────────────┘
```

## Report Features

### Lead Gen Metrics (Primary Focus)
- **Conversions** - Total lead form submissions
- **Cost Per Lead** - Average cost per conversion
- **Conversion Rate** - Clicks to conversions
- **Total Spend** - Weekly ad spend

### Supporting Metrics
- Impressions & Clicks
- Click-Through Rate (CTR)
- Average CPC
- Week-over-week trend indicators

### Visualizations
- Daily performance chart (conversions + spend)
- Campaign performance table
- Executive summary with highlights

---

## Prerequisites

1. **Google Cloud Project** with billing enabled
2. **Google Ads API Access**
   - Developer token
   - OAuth credentials
   - MCC (Manager) access to client accounts
3. **SendGrid Account** for email delivery
4. **GitHub Personal Access Token** with repo write access

---

## Setup Instructions

### Step 1: Google Ads API Credentials

1. Go to [Google Ads API Center](https://ads.google.com/aw/apicenter)
2. Create a developer token (apply for access if needed)
3. Create OAuth 2.0 credentials in Google Cloud Console
4. Create a `google-ads.yaml` file:

```yaml
developer_token: YOUR_DEVELOPER_TOKEN
client_id: YOUR_CLIENT_ID.apps.googleusercontent.com
client_secret: YOUR_CLIENT_SECRET
refresh_token: YOUR_REFRESH_TOKEN
login_customer_id: YOUR_MCC_CUSTOMER_ID
use_proto_plus: True
```

### Step 2: Get SendGrid API Key

1. Sign up at [SendGrid](https://sendgrid.com)
2. Create an API key with Mail Send permissions
3. Verify your sender email domain

### Step 3: GitHub Token

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate token with `repo` scope
3. Save for deployment

### Step 4: Configure Clients

Edit `clients.json`:

```json
{
  "clients": [
    {
      "name": "Client Display Name",
      "slug": "clientname",
      "customer_id": "1234567890",
      "email": "client@example.com",
      "cc": ["you@roberthebertmedia.com"],
      "active": true
    }
  ]
}
```

**Finding Customer ID:**
- In Google Ads, look at the URL
- Format: `https://ads.google.com/aw/overview?ocid=XXXXXXXXXX`
- Use the number without dashes

### Step 5: Deploy

```bash
cd automation
chmod +x deploy.sh
./deploy.sh
```

The script will:
1. Enable required GCP APIs
2. Create secrets in Secret Manager
3. Deploy the Cloud Function
4. Set up Cloud Scheduler for Monday 8am CST

---

## Manual Testing

Test the function immediately:

```bash
# Get function URL
FUNCTION_URL=$(gcloud functions describe rhm-google-ads-reports --region=us-central1 --format='value(serviceConfig.uri)')

# Trigger manually
curl -X POST $FUNCTION_URL
```

---

## Adding New Clients

1. Edit `clients.json` and add the new client
2. Redeploy the function:

```bash
gcloud functions deploy rhm-google-ads-reports \
    --gen2 \
    --runtime python311 \
    --region us-central1 \
    --source . \
    --entry-point generate_weekly_reports
```

---

## Troubleshooting

### Check Logs

```bash
gcloud functions logs read rhm-google-ads-reports --region=us-central1 --limit=50
```

### Common Issues

| Issue | Solution |
|-------|----------|
| `PERMISSION_DENIED` | Check service account has Secret Manager access |
| `INVALID_CUSTOMER_ID` | Remove dashes from customer ID |
| `UNAUTHENTICATED` | Refresh token expired - regenerate OAuth tokens |
| `Email not delivered` | Check SendGrid dashboard for bounces/blocks |

### Update Secrets

```bash
# Update Google Ads credentials
gcloud secrets versions add google-ads-credentials --data-file=google-ads.yaml

# Update GitHub token
echo -n "new_token" | gcloud secrets versions add github-token --data-file=-
```

---

## Cost Estimate

| Service | Cost |
|---------|------|
| Cloud Functions | ~$0.40/month (52 invocations/year) |
| Cloud Scheduler | Free (3 free jobs) |
| Secret Manager | ~$0.06/month |
| **Total** | **~$5/year** |

---

## File Structure

```
automation/
├── main.py              # Cloud Function code
├── requirements.txt     # Python dependencies
├── clients.json         # Client configuration
├── deploy.sh           # Deployment script
└── README.md           # This file
```

---

## Support

Questions? Contact Brandon at brandon@hendricks.ai
