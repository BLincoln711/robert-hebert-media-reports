# Robert Hebert Media - Automated Weekly Reports via Google Sheets

## Overview
This system automatically generates weekly Google Ads reports every Monday at 8am CST using:
- **Google Sheets** with native Google Ads data connector
- **Google Apps Script** for report generation and deployment
- **GitHub API** for publishing to reports.roberthebertmedia.com

## Setup Instructions

### Step 1: Create the Google Sheet

1. Go to [Google Sheets](https://sheets.google.com) and create a new spreadsheet
2. Name it: `RHM Weekly Reports - Google Ads Data`
3. Share with: robert@roberthebertmedia.com (Editor access)

### Step 2: Connect Google Ads Data

1. In the Google Sheet, go to **Extensions > Add-ons > Get add-ons**
2. Search for **"Google Ads"** and install the official connector
3. Or use the built-in Data Connector:
   - Go to **Data > Data connectors > Connect to BigQuery** (if using BigQuery export)
   - Or manually set up the structure below

### Step 3: Sheet Structure

Create these sheets (tabs):

#### Sheet 1: "Config"
| A | B |
|---|---|
| github_token | ghp_xxxxxxxxxxxx |
| github_repo | BLincoln711/robert-hebert-media-reports |
| email_to | robert@roberthebertmedia.com |
| email_bcc | brandon@hendricks.ai |

#### Sheet 2: "Clients"
| Client Name | Slug | Customer ID | Active |
|-------------|------|-------------|--------|
| JFTx2025 | jftx2025 | 917-597-4799 | TRUE |
| PFBHNC | pfbhnc | 343-027-6201 | TRUE |
| ReOptica | reoptica | 326-336-6442 | TRUE |

#### Sheet 3: "This Week" (data entry)
| Client | Spend | Impressions | Clicks |
|--------|-------|-------------|--------|
| JFTx2025 | 1511.21 | 703710 | 13325 |
| PFBHNC | 2935.07 | 43930 | 6600 |
| ReOptica | 522.59 | 4056 | 232 |

#### Sheet 4: "Previous Week" (data entry)
| Client | Spend | Impressions | Clicks |
|--------|-------|-------------|--------|
| JFTx2025 | 893.73 | 282995 | 5700 |
| PFBHNC | 3607.04 | 54693 | 6586 |
| ReOptica | 535.51 | 4920 | 306 |

#### Sheet 5: "Date Range"
| A | B |
|---|---|
| this_week_start | 2025-12-29 |
| this_week_end | 2026-01-04 |
| prev_week_start | 2025-12-22 |
| prev_week_end | 2025-12-28 |

### Step 4: Add the Apps Script

1. In Google Sheets, go to **Extensions > Apps Script**
2. Delete any existing code
3. Copy the entire contents of `apps-script.js` (see below)
4. Click **Save** (Ctrl+S)
5. Name the project: `RHM Weekly Report Generator`

### Step 5: Set Up GitHub Token

1. Go to https://github.com/settings/tokens
2. Click **Generate new token (classic)**
3. Name: `RHM Report Automation`
4. Select scopes: `repo` (full control)
5. Generate and copy the token
6. Paste it in the Config sheet cell B1

### Step 6: Set Up Weekly Trigger

1. In Apps Script, click the clock icon (Triggers) in the left sidebar
2. Click **+ Add Trigger**
3. Configure:
   - Function: `generateWeeklyReports`
   - Deployment: `Head`
   - Event source: `Time-driven`
   - Type: `Week timer`
   - Day: `Monday`
   - Time: `8am to 9am`
4. Click **Save**

### Step 7: Test the System

1. In Apps Script, select `generateWeeklyReports` from the dropdown
2. Click **Run**
3. Check:
   - Reports appear at https://reports.roberthebertmedia.com/
   - Email notification received

---

## Weekly Workflow

### Automatic (after setup):
Every Monday at 8am, the system will:
1. Read data from "This Week" and "Previous Week" sheets
2. Generate HTML reports for each client
3. Deploy to GitHub Pages
4. Send email notification with report links

### Your only task:
Before Monday morning, update the data in:
- "This Week" sheet with current week's data
- "Previous Week" sheet (copy last week's "This Week" data)
- "Date Range" sheet with correct dates

**Pro tip:** Set up a Google Ads scheduled export to automatically populate the sheets.

---

## Troubleshooting

### Reports not generating
1. Check Apps Script execution log: Extensions > Apps Script > Executions
2. Verify GitHub token is valid and has repo access
3. Ensure all required sheets exist with correct names

### Email not sending
1. Check that email addresses are correct in Config sheet
2. Verify Apps Script has Gmail permissions

### Data not updating
1. Confirm Google Ads connector is refreshing
2. Check date ranges in "Date Range" sheet

---

## Files

- `apps-script.js` - Main Apps Script code
- `google-sheets-setup.md` - This file
