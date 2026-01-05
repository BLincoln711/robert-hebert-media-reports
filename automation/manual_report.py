#!/usr/bin/env python3
"""
Robert Hebert Media - Manual Google Ads Report Generator
Use this while waiting for API Basic Access approval.

Usage:
    python3 manual_report.py

Then paste the data when prompted.
"""

import json
from datetime import datetime, timedelta

def get_report_template():
    """Return the HTML report template."""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Google Ads Report - {client_name} - Week of {date_range}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f0f0f;
            color: #e5e5e5;
            line-height: 1.6;
        }}
        .header {{
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            padding: 40px 20px;
            text-align: center;
        }}
        .header h1 {{ color: #00d4ff; font-size: 2rem; margin-bottom: 8px; }}
        .header .subtitle {{ color: #a0a0a0; font-size: 1.1rem; }}
        .header .date-range {{ color: #00d4ff; font-weight: 600; margin-top: 12px; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .metric-card {{
            background: linear-gradient(145deg, #1a1a2e, #16213e);
            border: 1px solid #2a2a4e;
            border-radius: 16px;
            padding: 24px;
            text-align: center;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .metric-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 24px rgba(0, 212, 255, 0.15);
        }}
        .metric-card .label {{
            color: #888;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }}
        .metric-card .value {{ color: #00d4ff; font-size: 2rem; font-weight: 700; }}
        .metric-card .change {{ margin-top: 8px; font-size: 0.9rem; }}
        .section {{
            background: #1a1a2e;
            border-radius: 16px;
            padding: 24px;
            margin: 24px 0;
            border: 1px solid #2a2a4e;
        }}
        .section-title {{
            color: #00d4ff;
            font-size: 1.3rem;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid #00d4ff33;
        }}
        .chart-container {{ position: relative; height: 300px; margin: 20px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
        th, td {{ padding: 14px 12px; text-align: left; border-bottom: 1px solid #2a2a4e; }}
        th {{
            color: #00d4ff;
            font-weight: 600;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        tr:hover {{ background: rgba(0, 212, 255, 0.05); }}
        .highlight {{
            background: linear-gradient(135deg, rgba(0, 212, 255, 0.1), rgba(0, 212, 255, 0.05));
            border: 1px solid rgba(0, 212, 255, 0.3);
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
        }}
        .highlight-title {{ color: #00d4ff; font-weight: 700; margin-bottom: 8px; }}
        .footer {{
            text-align: center;
            padding: 40px 20px;
            color: #666;
            font-size: 0.85rem;
        }}
        .footer a {{ color: #00d4ff; text-decoration: none; }}
        @media (max-width: 768px) {{
            .metrics-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .header h1 {{ font-size: 1.5rem; }}
            table {{ font-size: 0.85rem; }}
            th, td {{ padding: 10px 8px; }}
        }}
    </style>
</head>
<body>
    <header class="header">
        <h1>Google Ads Performance Report</h1>
        <p class="subtitle">{client_name}</p>
        <p class="date-range">Week of {date_range}</p>
    </header>

    <div class="container">
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="label">Total Spend</div>
                <div class="value">{total_spend}</div>
                <div class="change">{spend_change}</div>
            </div>
            <div class="metric-card">
                <div class="label">Conversions</div>
                <div class="value">{conversions}</div>
                <div class="change">{conv_change}</div>
            </div>
            <div class="metric-card">
                <div class="label">Cost Per Lead</div>
                <div class="value">{cpl}</div>
                <div class="change">{cpl_change}</div>
            </div>
            <div class="metric-card">
                <div class="label">Conversion Rate</div>
                <div class="value">{cvr}</div>
                <div class="change">{cvr_change}</div>
            </div>
            <div class="metric-card">
                <div class="label">Clicks</div>
                <div class="value">{clicks}</div>
                <div class="change">{clicks_change}</div>
            </div>
            <div class="metric-card">
                <div class="label">Impressions</div>
                <div class="value">{impressions}</div>
                <div class="change">{impr_change}</div>
            </div>
        </div>

        <div class="highlight">
            <div class="highlight-title">Weekly Highlights</div>
            <p>
                This week generated <strong>{conversions} conversions</strong>
                at an average cost of <strong>{cpl}</strong> per lead.
                Total ad spend was <strong>{total_spend}</strong>
                with a click-through rate of <strong>{ctr}</strong>.
            </p>
        </div>

        <div class="section">
            <h2 class="section-title">Campaign Performance</h2>
            <table>
                <thead>
                    <tr>
                        <th>Campaign</th>
                        <th>Spend</th>
                        <th>Impressions</th>
                        <th>Clicks</th>
                        <th>Conversions</th>
                        <th>Cost/Lead</th>
                        <th>CVR</th>
                    </tr>
                </thead>
                <tbody>
                    {campaign_rows}
                </tbody>
            </table>
        </div>
    </div>

    <footer class="footer">
        <p>Report generated on {generated_date}</p>
        <p style="margin-top: 8px;">Powered by <a href="https://roberthebertmedia.com">Robert Hebert Media</a></p>
    </footer>
</body>
</html>'''


def format_currency(value):
    """Format as currency."""
    return f"${value:,.2f}"


def format_number(value):
    """Format with commas."""
    return f"{value:,.0f}"


def format_percent(value):
    """Format as percentage."""
    return f"{value:.2f}%"


def change_indicator(change, invert=False):
    """Generate change indicator HTML."""
    if change == 0:
        return '<span style="color: #666;">—</span>'
    is_positive = change > 0 if not invert else change < 0
    color = '#22c55e' if is_positive else '#ef4444'
    arrow = '↑' if change > 0 else '↓'
    return f'<span style="color: {color}; font-weight: 600;">{arrow} {abs(change):.1f}%</span>'


def main():
    print("\n" + "="*60)
    print("ROBERT HEBERT MEDIA - MANUAL REPORT GENERATOR")
    print("="*60)

    # Get client name
    print("\nAvailable clients:")
    print("  1. JFTx2025")
    print("  2. PFBHNC")
    print("  3. ReOptica")

    client_choice = input("\nSelect client (1-3): ").strip()
    clients = {
        "1": ("JFTx2025", "jftx2025"),
        "2": ("PFBHNC", "pfbhnc"),
        "3": ("ReOptica", "reoptica")
    }

    if client_choice not in clients:
        print("Invalid choice. Using JFTx2025.")
        client_choice = "1"

    client_name, client_slug = clients[client_choice]

    # Get date range
    print(f"\nClient: {client_name}")
    date_range = input("Enter date range (e.g., 'January 6 - 12, 2026'): ").strip()
    if not date_range:
        date_range = "January 6 - 12, 2026"

    # Get metrics
    print("\n" + "-"*40)
    print("Enter the metrics (press Enter for 0):")
    print("-"*40)

    def get_float(prompt, default=0):
        val = input(prompt).strip().replace(",", "").replace("$", "").replace("%", "")
        try:
            return float(val) if val else default
        except:
            return default

    # Current week
    print("\nCURRENT WEEK:")
    spend = get_float("  Total Spend ($): ")
    impressions = get_float("  Impressions: ")
    clicks = get_float("  Clicks: ")
    conversions = get_float("  Conversions: ")

    # Previous week (for comparison)
    print("\nPREVIOUS WEEK (for comparison):")
    prev_spend = get_float("  Total Spend ($): ")
    prev_impressions = get_float("  Impressions: ")
    prev_clicks = get_float("  Clicks: ")
    prev_conversions = get_float("  Conversions: ")

    # Calculate metrics
    ctr = (clicks / impressions * 100) if impressions > 0 else 0
    cpl = spend / conversions if conversions > 0 else 0
    cvr = (conversions / clicks * 100) if clicks > 0 else 0

    # Calculate changes
    def calc_change(curr, prev):
        if prev == 0:
            return 0 if curr == 0 else 100
        return ((curr - prev) / prev) * 100

    spend_chg = calc_change(spend, prev_spend)
    conv_chg = calc_change(conversions, prev_conversions)
    clicks_chg = calc_change(clicks, prev_clicks)
    impr_chg = calc_change(impressions, prev_impressions)

    prev_cpl = prev_spend / prev_conversions if prev_conversions > 0 else 0
    cpl_chg = calc_change(cpl, prev_cpl)

    prev_cvr = (prev_conversions / prev_clicks * 100) if prev_clicks > 0 else 0
    cvr_chg = calc_change(cvr, prev_cvr)

    # Get campaign data
    print("\n" + "-"*40)
    print("Enter campaign data (type 'done' when finished):")
    print("-"*40)

    campaigns = []
    while True:
        name = input("\nCampaign name (or 'done'): ").strip()
        if name.lower() == 'done' or not name:
            break

        c_spend = get_float("  Spend ($): ")
        c_impr = get_float("  Impressions: ")
        c_clicks = get_float("  Clicks: ")
        c_conv = get_float("  Conversions: ")

        campaigns.append({
            'name': name,
            'spend': c_spend,
            'impressions': c_impr,
            'clicks': c_clicks,
            'conversions': c_conv
        })

    # Generate campaign rows HTML
    campaign_rows = ""
    for c in campaigns:
        c_cpl = c['spend'] / c['conversions'] if c['conversions'] > 0 else 0
        c_cvr = (c['conversions'] / c['clicks'] * 100) if c['clicks'] > 0 else 0
        campaign_rows += f"""
            <tr>
                <td style="font-weight: 600;">{c['name']}</td>
                <td>{format_currency(c['spend'])}</td>
                <td>{format_number(c['impressions'])}</td>
                <td>{format_number(c['clicks'])}</td>
                <td>{c['conversions']:.1f}</td>
                <td>{format_currency(c_cpl)}</td>
                <td>{c_cvr:.1f}%</td>
            </tr>
        """

    if not campaign_rows:
        campaign_rows = "<tr><td colspan='7' style='text-align: center; color: #888;'>No campaign data entered</td></tr>"

    # Generate HTML
    html = get_report_template().format(
        client_name=client_name,
        date_range=date_range,
        total_spend=format_currency(spend),
        conversions=format_number(conversions),
        cpl=format_currency(cpl),
        cvr=format_percent(cvr),
        clicks=format_number(clicks),
        impressions=format_number(impressions),
        ctr=format_percent(ctr),
        spend_change=change_indicator(spend_chg),
        conv_change=change_indicator(conv_chg),
        cpl_change=change_indicator(cpl_chg, invert=True),
        cvr_change=change_indicator(cvr_chg),
        clicks_change=change_indicator(clicks_chg),
        impr_change=change_indicator(impr_chg),
        campaign_rows=campaign_rows,
        generated_date=datetime.now().strftime('%B %d, %Y at %I:%M %p')
    )

    # Determine folder name
    folder_name = f"{client_slug}-{datetime.now().strftime('%b').lower()}{datetime.now().day}-{datetime.now().day + 6}"

    # Save report
    import os
    report_dir = os.path.expanduser(f"~/robert-hebert-media-reports/{folder_name}")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, "index.html")

    with open(report_path, 'w') as f:
        f.write(html)

    print("\n" + "="*60)
    print("REPORT GENERATED!")
    print("="*60)
    print(f"\nSaved to: {report_path}")
    print(f"\nTo deploy:")
    print(f"  cd ~/robert-hebert-media-reports")
    print(f"  git add -A && git commit -m 'Add {client_name} report' && git push")
    print(f"\nReport URL will be:")
    print(f"  https://reports.roberthebertmedia.com/{folder_name}/")
    print("="*60 + "\n")

    # Open in browser
    os.system(f'open "{report_path}"')


if __name__ == "__main__":
    main()
