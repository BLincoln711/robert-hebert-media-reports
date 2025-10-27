# Robert Hebert Media - Client Reports Platform

Automated weekly performance reports hosted at **https://reports-roberthebertmedia.com**

## 🚀 Quick Start - Generate a New Weekly Report

### Step 1: Create Report with Claude Code

Use this prompt:

```
Create a weekly performance report for [CLIENT_NAME] comparing [WEEK1 DATES] vs [WEEK2 DATES].

[Paste or attach your analytics data]

Generate an interactive HTML report and save to:
/Users/brandonlhendricks/claudecode/robert-hebert-media-reports/[clientname-monthDD-DD]/index.html
```

### Step 2: Deploy

```bash
cd /Users/brandonlhendricks/claudecode/robert-hebert-media-reports
./quick-deploy.sh "clientname-oct20-26" "Client Name" "October 20-26, 2025"
```

### Step 3: Update Index (Optional)

Edit `index.html` to add the new report to the main landing page.

### Step 4: Share

Send client: `https://reports-roberthebertmedia.com/clientname-oct20-26/`

## 📁 Current Reports

- Reports will be listed here as they are created

## 📚 Documentation

- **Full Template**: See `WEEKLY_REPORT_TEMPLATE.md` for detailed instructions
- **Customization**: Client-specific preferences and guidelines
- **Troubleshooting**: Common issues and solutions

## 🔧 Technical Setup

- **Hosting**: GitHub Pages
- **Domain**: reports-roberthebertmedia.com
- **SSL**: Auto-provisioned by GitHub (Let's Encrypt)
- **Repository**: Will be created at https://github.com/BLincoln711/robert-hebert-media-reports

## 📝 File Structure

```
robert-hebert-media-reports/
├── index.html                    # Main landing page
├── CNAME                         # Custom domain config
├── README.md                     # This file
├── WEEKLY_REPORT_TEMPLATE.md    # Report generation guide
├── quick-deploy.sh              # Deployment script
└── [clientname-dates]/
    └── index.html               # Individual client report
```

## 🎨 Report Features

- Executive summary with highlights
- Interactive Chart.js visualizations
- Mobile-responsive design
- Professional gradient styling
- Week-over-week comparisons
- Geographic distribution
- Traffic channel analysis
- Competitive intelligence

## 🔐 Privacy

Each client gets a unique URL path. Reports are public URLs but not indexed or linked publicly. Share only the specific URL with each client.

## ⚡ Maintenance

### Update Existing Report
```bash
# Edit the HTML file
nano clientname-oct13-19/index.html

# Deploy changes
git add -A
git commit -m "Update client report"
git push
```

### Check SSL Status
Visit: https://github.com/BLincoln711/robert-hebert-media-reports/settings/pages

### Verify DNS
```bash
nslookup reports-roberthebertmedia.com
```
