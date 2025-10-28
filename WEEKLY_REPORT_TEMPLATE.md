# Weekly Client Report Generation Template

## Quick Start Command
Use this prompt with Claude Code each week:

```
Create a weekly performance report for [CLIENT_NAME] comparing [CURRENT_WEEK_DATES] vs [PREVIOUS_WEEK_DATES].

Use the data from the attached file/CSV and create an interactive HTML report with:
- Executive summary with highlights and watch areas
- Key performance metrics cards (users, sessions, engagement rate, engagement time, events)
- Channel performance comparison charts
- Traffic source distribution
- Top pages performance
- User journey analysis
- Geographic distribution
- Competitive intelligence (if applicable)
- Key insights and recommendations

Style: Professional gradient header (purple/blue), white cards, interactive Chart.js visualizations, mobile-responsive.

Save to: /Users/brandonlhendricks/claudecode/robert-hebert-media-reports/[clientname-daterange]/index.html
```

## Deployment Process

1. **Create the report** using the prompt above
2. **Deploy to web**:
   ```bash
   cd /Users/brandonlhendricks/claudecode/robert-hebert-media-reports
   git add -A
   git commit -m "Add [clientname] report for [dates]"
   git push
   ```

3. **Update main index** - Edit `index.html` and add:
   ```html
   <div class="report-item">
       <a href="/clientname-daterange/">
           <div class="report-title">Client Name</div>
           <div class="report-date">Week of [dates]</div>
       </a>
   </div>
   ```

4. **Share URL** with client:
   - `https://reports.roberthebertmedia.com/clientname-daterange/`

## Report Customization Notes

### What to Include/Exclude:
- ✅ Include: Performance metrics, growth trends, strengths
- ❌ Exclude (per client preference): Specific negative critiques without context
- 🔄 Customize: Competitive intelligence section based on client industry

### Areas for Improvement Section:
- Focus on actionable insights
- Frame negatives constructively
- Balance criticism with solutions

## File Naming Convention

**Format:** `clientname-monthDD-DD`

Examples:
- `clientname-oct13-19`
- `acmecorp-nov01-07`
- `techstartup-dec15-21`

## Weekly Checklist

- [ ] Gather analytics data (GA4, Search Console, etc.)
- [ ] Run prompt with current/previous week dates
- [ ] Review report for accuracy
- [ ] Remove any sensitive/inappropriate recommendations
- [ ] Deploy to GitHub Pages
- [ ] Update main index page
- [ ] Test URL before sharing
- [ ] Send URL to client

## Client-Specific Notes

### [Add client names here]
- Focus: [Key focus areas]
- Exclude: [What not to include]
- Include: [What to emphasize]
- Key Pages: [Important pages to track]

## Data Sources

Common data sources for reports:
- Google Analytics 4 (primary)
- Google Search Console (SEO data)
- Social media analytics
- CRM data (leads, conversions)
- Ad platform data (Google Ads, Facebook Ads)

## Troubleshooting

**SSL Certificate not ready?**
- Wait 1-24 hours after DNS changes
- Use github.io URL temporarily: `https://blincoln711.github.io/robert-hebert-media-reports/[path]/`

**Need to update existing report?**
- Edit the HTML file in the specific folder
- Commit and push changes
- Changes go live within 1-2 minutes

**Client can't access URL?**
- Verify DNS propagation: `nslookup reports.roberthebertmedia.com`
- Check GitHub Pages settings
- Try incognito/private browsing
- Clear browser cache
