# Robert Hebert Media - Client Reports Platform

## Overview
Weekly performance reports platform for Robert Hebert Media clients.

**Live URL:** https://reports.roberthebertmedia.com
**Repository:** BLincoln711/robert-hebert-media-reports
**Hosting:** GitHub Pages

---

## Color Scheme (SAME AS BLOK.CO)

| Element | Value |
|---------|-------|
| Header Gradient | `linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)` |
| Accent Color | `#00d4ff` (Cyan) |
| Section Title Bar | `linear-gradient(180deg, #00d4ff 0%, #0f3460 100%)` |
| Report Item Border | `border-left: 4px solid #00d4ff` |
| Heading Text | `#1a1a2e` |
| Body Text | `#333` |
| Background | `#f5f5f5` |

---

## Directory Structure

```
robert-hebert-media-reports/
├── index.html                    # Main landing page (list of reports)
├── CNAME                         # Custom domain config
├── README.md                     # Setup documentation
├── WEEKLY_REPORT_TEMPLATE.md     # Report generation guide
├── quick-deploy.sh               # Deployment script
└── [clientname-dates]/           # Individual client reports
    └── index.html
```

---

## Current Clients

### Blair Realty Group
- **URL Pattern:** `/blairrealtygroup-[dates]/`
- **Reports:** Weekly performance reports
- **Data Sources:** GA4, Search Console

---

## Report Generation Workflow

### Step 1: Create Report
Use this prompt:
```
Create a weekly performance report for [CLIENT_NAME] comparing [CURRENT_WEEK] vs [PREVIOUS_WEEK].

[Paste analytics data]

Generate an interactive HTML report and save to:
~/robert-hebert-media-reports/[clientname-monthDD-DD]/index.html
```

### Step 2: Deploy
```bash
cd ~/robert-hebert-media-reports
git add -A
git commit -m "Add [client] report for [dates]"
git push
```

### Step 3: Update Index
Edit `index.html` to add the new report link:
```html
<div class="report-item">
    <a href="/clientname-dates/">
        <div class="report-title">Weekly Performance Report <span class="badge-new">NEW</span></div>
        <div class="report-date">Week of [Month Day-Day, Year]</div>
    </a>
</div>
```

### Step 4: Share
Send client: `https://reports.roberthebertmedia.com/clientname-dates/`

---

## File Naming Convention

**Format:** `clientname-monthDD-DD`

Examples:
- `blairrealtygroup-dec1-7`
- `clientname-oct13-19`
- `acmecorp-nov01-07`

---

## Report Features

Include in every report:
- Executive summary with highlights
- Key performance metrics (users, sessions, engagement)
- Week-over-week comparisons
- Channel performance charts (Chart.js)
- Traffic source distribution
- Top pages performance
- Geographic distribution
- Key insights and recommendations
- Mobile-responsive design

---

## Quick Deploy Script

```bash
./quick-deploy.sh "clientname-dates" "Client Name" "Month Day-Day, Year"
```

This script:
1. Adds all changes to git
2. Commits with formatted message
3. Pushes to GitHub
4. Updates index page

---

## Index Page Template

When adding a new report to `index.html`:

```html
<div class="report-item">
    <a href="/clientname-dates/">
        <div class="report-title">Weekly Performance Report <span class="badge-new">NEW</span></div>
        <div class="report-date">Week of [Dates]</div>
    </a>
</div>
```

Remove `<span class="badge-new">NEW</span>` from previous reports when adding new ones.

---

## Tone & Messaging

- **Keep messaging POSITIVE** - avoid harsh negative language
- Frame issues as "areas for improvement" or "opportunities"
- Balance criticism with actionable solutions
- Highlight wins prominently
- Be constructive, not critical

---

## Data Sources

Common sources for reports:
- Google Analytics 4 (primary)
- Google Search Console (SEO)
- Social media analytics
- CRM data (leads, conversions)
- Ad platform data

---

## Troubleshooting

### SSL Certificate Issues
- Wait 1-24 hours after DNS changes
- Temporary fallback: `https://blincoln711.github.io/robert-hebert-media-reports/[path]/`

### Update Existing Report
```bash
# Edit the HTML file
nano clientname-dates/index.html

# Deploy changes
git add -A && git commit -m "Update report" && git push
```

### Verify DNS
```bash
nslookup reports.roberthebertmedia.com
```

---

## Difference from Blok.co Reports

| Aspect | Robert Hebert Media | Blok.co |
|--------|---------------------|---------|
| Domain | reports.roberthebertmedia.com | reports-blok.co |
| Repository | robert-hebert-media-reports | blair-realty-report |
| Branding | "Powered by Blok.co" badge | Blok logo in header |

Both use the same color scheme and report structure.

---

## Weekly Checklist

- [ ] Gather analytics data
- [ ] Generate report with Claude
- [ ] Review for accuracy
- [ ] Deploy to GitHub Pages
- [ ] Update index.html with new link
- [ ] Remove "NEW" badge from previous report
- [ ] Test URL before sharing
- [ ] Send URL to client
