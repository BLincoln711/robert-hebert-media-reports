#!/usr/bin/env python3
"""
Robert Hebert Media - Semi-Automated Weekly Report Generator

Usage:
    python3 weekly_report.py                    # Interactive mode
    python3 weekly_report.py --csv data.csv    # From Google Ads CSV export
    python3 weekly_report.py --deploy          # Auto-deploy after generation
    python3 weekly_report.py --email           # Send email notification

Example workflow:
    1. Export data from Google Ads (Accounts > Export)
    2. Run: python3 weekly_report.py --csv export.csv --deploy --email
"""

import os
import sys
import csv
import json
import subprocess
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
REPO_DIR = Path.home() / "robert-hebert-media-reports"
CLIENTS = {
    "jftx2025": {"name": "JFTx2025", "customer_id": "917-597-4799"},
    "pfbhnc": {"name": "PFBHNC", "customer_id": "343-027-6201"},
    "reoptica": {"name": "ReOptica", "customer_id": "326-336-6442"},
}

REPORT_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weekly Performance Report | {client_name} | {date_range}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #0066CC;
            --success: #059669;
            --warning: #D97706;
            --danger: #DC2626;
            --gray-50: #F9FAFB;
            --gray-100: #F3F4F6;
            --gray-200: #E5E7EB;
            --gray-400: #9CA3AF;
            --gray-500: #6B7280;
            --gray-600: #4B5563;
            --gray-700: #374151;
            --gray-800: #1F2937;
            --gray-900: #111827;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #fff;
            color: var(--gray-800);
            line-height: 1.5;
            font-size: 14px;
        }}
        .report-container {{ max-width: 1100px; margin: 0 auto; padding: 40px; }}
        .report-header {{ border-bottom: 3px solid var(--primary); padding-bottom: 24px; margin-bottom: 32px; }}
        .header-top {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; }}
        .brand {{ font-size: 12px; font-weight: 600; color: var(--gray-500); text-transform: uppercase; letter-spacing: 1.5px; }}
        .report-date {{ font-size: 12px; color: var(--gray-500); text-align: right; }}
        .client-name {{ font-size: 32px; font-weight: 700; color: var(--gray-900); margin-bottom: 4px; }}
        .report-title {{ font-size: 18px; font-weight: 400; color: var(--gray-600); }}
        .report-period {{ display: inline-block; background: var(--primary); color: white; padding: 6px 16px; border-radius: 4px; font-size: 13px; font-weight: 500; margin-top: 12px; }}
        .executive-summary {{ background: var(--gray-50); border-left: 4px solid var(--primary); padding: 24px 28px; margin-bottom: 40px; }}
        .summary-title {{ font-size: 11px; font-weight: 600; color: var(--primary); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px; }}
        .summary-text {{ font-size: 16px; color: var(--gray-700); line-height: 1.7; }}
        .summary-text strong {{ color: var(--gray-900); font-weight: 600; }}
        .kpi-section {{ margin-bottom: 48px; }}
        .section-header {{ font-size: 11px; font-weight: 600; color: var(--gray-500); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 20px; padding-bottom: 8px; border-bottom: 1px solid var(--gray-200); }}
        .kpi-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }}
        .kpi-card {{ background: white; border: 1px solid var(--gray-200); border-radius: 8px; padding: 24px; position: relative; }}
        .kpi-card.highlight {{ border-color: var(--primary); border-width: 2px; }}
        .kpi-label {{ font-size: 12px; font-weight: 500; color: var(--gray-500); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }}
        .kpi-value {{ font-size: 36px; font-weight: 700; color: var(--gray-900); line-height: 1; margin-bottom: 8px; }}
        .kpi-card.highlight .kpi-value {{ color: var(--primary); }}
        .kpi-change {{ font-size: 13px; font-weight: 500; display: flex; align-items: center; gap: 4px; }}
        .kpi-change.positive {{ color: var(--success); }}
        .kpi-change.negative {{ color: var(--danger); }}
        .kpi-change.neutral {{ color: var(--gray-400); }}
        .kpi-subtitle {{ font-size: 12px; color: var(--gray-500); margin-top: 4px; }}
        .performance-badge {{ position: absolute; top: 16px; right: 16px; padding: 4px 10px; border-radius: 4px; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }}
        .performance-badge.excellent {{ background: #D1FAE5; color: #065F46; }}
        .performance-badge.good {{ background: #DBEAFE; color: #1E40AF; }}
        .table-section {{ margin-bottom: 48px; }}
        .data-table {{ width: 100%; border-collapse: collapse; background: white; border: 1px solid var(--gray-200); border-radius: 8px; overflow: hidden; }}
        .data-table thead {{ background: var(--gray-50); }}
        .data-table th {{ padding: 14px 16px; text-align: left; font-size: 11px; font-weight: 600; color: var(--gray-600); text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid var(--gray-200); }}
        .data-table th:not(:first-child) {{ text-align: right; }}
        .data-table td {{ padding: 16px; border-bottom: 1px solid var(--gray-100); font-size: 14px; }}
        .data-table td:not(:first-child) {{ text-align: right; font-variant-numeric: tabular-nums; }}
        .data-table tbody tr:hover {{ background: var(--gray-50); }}
        .data-table tbody tr:last-child td {{ border-bottom: none; }}
        .metric-name {{ font-weight: 500; color: var(--gray-800); }}
        .metric-value {{ font-weight: 600; color: var(--gray-900); }}
        .change-positive {{ color: var(--success); font-weight: 500; }}
        .change-negative {{ color: var(--danger); font-weight: 500; }}
        .insights-section {{ margin-bottom: 48px; }}
        .insight-card {{ background: white; border: 1px solid var(--gray-200); border-radius: 8px; padding: 24px; margin-bottom: 16px; }}
        .insight-card:last-child {{ margin-bottom: 0; }}
        .insight-header {{ display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }}
        .insight-icon {{ width: 32px; height: 32px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 16px; }}
        .insight-icon.success {{ background: #D1FAE5; }}
        .insight-icon.info {{ background: #DBEAFE; }}
        .insight-icon.warning {{ background: #FEF3C7; }}
        .insight-title {{ font-size: 14px; font-weight: 600; color: var(--gray-800); }}
        .insight-text {{ font-size: 14px; color: var(--gray-600); line-height: 1.6; }}
        .report-footer {{ border-top: 1px solid var(--gray-200); padding-top: 24px; margin-top: 48px; display: flex; justify-content: space-between; align-items: center; }}
        .footer-brand {{ font-size: 12px; color: var(--gray-500); }}
        .footer-brand a {{ color: var(--primary); text-decoration: none; font-weight: 500; }}
        .footer-meta {{ font-size: 11px; color: var(--gray-400); }}
        @media (max-width: 768px) {{ .report-container {{ padding: 20px; }} .kpi-grid {{ grid-template-columns: repeat(2, 1fr); gap: 16px; }} .kpi-value {{ font-size: 28px; }} .header-top {{ flex-direction: column; gap: 8px; }} }}
    </style>
</head>
<body>
    <div class="report-container">
        <header class="report-header">
            <div class="header-top">
                <div class="brand">Robert Hebert Media</div>
                <div class="report-date">Report Generated: {generated_date}<br>Confidential</div>
            </div>
            <h1 class="client-name">{client_name}</h1>
            <p class="report-title">Weekly Google Ads Performance Report</p>
            <span class="report-period">{date_range}</span>
        </header>

        <div class="executive-summary">
            <div class="summary-title">Executive Summary</div>
            <p class="summary-text">{executive_summary}</p>
        </div>

        <section class="kpi-section">
            <div class="section-header">Key Performance Indicators</div>
            <div class="kpi-grid">
                <div class="kpi-card highlight">
                    <div class="kpi-label">Total Spend</div>
                    <div class="kpi-value">{spend_display}</div>
                    <div class="kpi-change {spend_change_class}">{spend_change_text}</div>
                </div>
                <div class="kpi-card highlight">
                    {ctr_badge}
                    <div class="kpi-label">Click-Through Rate</div>
                    <div class="kpi-value">{ctr_display}</div>
                    <div class="kpi-change {ctr_change_class}">{ctr_change_text}</div>
                </div>
                <div class="kpi-card">
                    {cpc_badge}
                    <div class="kpi-label">Avg. Cost Per Click</div>
                    <div class="kpi-value">{cpc_display}</div>
                    <div class="kpi-change {cpc_change_class}">{cpc_change_text}</div>
                </div>
                <div class="kpi-card">
                    {clicks_badge}
                    <div class="kpi-label">Total Clicks</div>
                    <div class="kpi-value">{clicks_display}</div>
                    <div class="kpi-change {clicks_change_class}">{clicks_change_text}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Impressions</div>
                    <div class="kpi-value">{impressions_display}</div>
                    <div class="kpi-change {impressions_change_class}">{impressions_change_text}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Impression Share</div>
                    <div class="kpi-value">—</div>
                    <div class="kpi-subtitle">Data pending</div>
                </div>
            </div>
        </section>

        <section class="table-section">
            <div class="section-header">Detailed Metrics</div>
            <table class="data-table">
                <thead>
                    <tr><th>Metric</th><th>This Week</th><th>Previous Week</th><th>Change</th></tr>
                </thead>
                <tbody>
                    <tr><td class="metric-name">Total Ad Spend</td><td class="metric-value">{spend_exact}</td><td>{prev_spend}</td><td class="{spend_table_class}">{spend_change_pct}</td></tr>
                    <tr><td class="metric-name">Impressions</td><td class="metric-value">{impressions_exact}</td><td>{prev_impressions}</td><td class="{impressions_table_class}">{impressions_change_pct}</td></tr>
                    <tr><td class="metric-name">Clicks</td><td class="metric-value">{clicks_exact}</td><td>{prev_clicks}</td><td class="{clicks_table_class}">{clicks_change_pct}</td></tr>
                    <tr><td class="metric-name">Click-Through Rate (CTR)</td><td class="metric-value">{ctr_exact}</td><td>{prev_ctr}</td><td class="{ctr_table_class}">{ctr_change_pct}</td></tr>
                    <tr><td class="metric-name">Average CPC</td><td class="metric-value">{cpc_exact}</td><td>{prev_cpc}</td><td class="{cpc_table_class}">{cpc_change_pct}</td></tr>
                </tbody>
            </table>
        </section>

        <section class="insights-section">
            <div class="section-header">Key Insights & Recommendations</div>
            {insights_html}
        </section>

        <footer class="report-footer">
            <div class="footer-brand">Prepared by <a href="https://roberthebertmedia.com">Robert Hebert Media</a></div>
            <div class="footer-meta">Report ID: {report_id} | Page 1 of 1</div>
        </footer>
    </div>
</body>
</html>
'''


def parse_number(value):
    """Parse a number from string, handling currency and commas."""
    if not value or value == '—':
        return 0
    return float(str(value).replace('$', '').replace(',', '').replace('%', '').strip())


def format_currency(value):
    """Format as currency."""
    if value >= 1000:
        return f"${value:,.0f}"
    return f"${value:,.2f}"


def format_number(value):
    """Format with commas."""
    return f"{value:,.0f}"


def format_percent(value):
    """Format as percentage."""
    return f"{value:.2f}%"


def calc_change(current, previous):
    """Calculate percentage change."""
    if previous == 0:
        return 0 if current == 0 else 100
    return ((current - previous) / previous) * 100


def get_change_class(change, invert=False):
    """Get CSS class for change indicator."""
    if abs(change) < 0.5:
        return "neutral"
    is_positive = change > 0 if not invert else change < 0
    return "positive" if is_positive else "negative"


def get_table_class(change, invert=False):
    """Get CSS class for table change."""
    if abs(change) < 0.5:
        return ""
    is_positive = change > 0 if not invert else change < 0
    return "change-positive" if is_positive else "change-negative"


def format_change_text(change, prefix="", suffix=" vs last week", invert=False):
    """Format change text for KPI cards."""
    if abs(change) < 0.5:
        return "No change"
    sign = "+" if change > 0 else ""
    return f"{prefix}{sign}{change:.1f}%{suffix}"


def generate_insights(data, prev_data):
    """Generate dynamic insights based on data."""
    insights = []

    # CTR insight
    ctr = data['ctr']
    ctr_change = calc_change(ctr, prev_data['ctr']) if prev_data['ctr'] > 0 else 0

    if ctr >= 10:
        insights.append({
            "icon": "success",
            "title": "Outstanding CTR Performance",
            "text": f"A {ctr:.2f}% CTR is exceptional—approximately 5-7x the industry average. "
                   f"{'The ' + format_change_text(ctr_change).replace(' vs last week', '') + ' improvement week-over-week indicates strong ad relevance.' if ctr_change > 5 else 'This indicates highly effective ad copy and targeting.'}"
        })
    elif ctr >= 5:
        insights.append({
            "icon": "success",
            "title": "Strong Click-Through Rate",
            "text": f"A {ctr:.2f}% CTR is approximately 2x the industry average, indicating strong ad relevance and effective messaging."
        })
    elif ctr >= 2:
        insights.append({
            "icon": "info",
            "title": "Solid CTR Performance",
            "text": f"A {ctr:.2f}% CTR is at or above industry average. Consider testing ad variations to improve engagement."
        })
    else:
        insights.append({
            "icon": "warning",
            "title": "CTR Optimization Opportunity",
            "text": f"A {ctr:.2f}% CTR is below industry average (2-3%). Recommend testing new ad copy and reviewing keyword relevance."
        })

    # Volume/efficiency insights
    clicks_change = calc_change(data['clicks'], prev_data['clicks'])
    spend_change = calc_change(data['spend'], prev_data['spend'])
    cpc_change = calc_change(data['cpc'], prev_data['cpc'])

    if clicks_change > 50 and cpc_change < 0:
        insights.append({
            "icon": "success",
            "title": "Exceptional Scale Achievement",
            "text": f"Clicks increased {clicks_change:.0f}% while CPC decreased {abs(cpc_change):.0f}%. "
                   "The campaign successfully scaled with improved efficiency."
        })
    elif cpc_change < -15:
        insights.append({
            "icon": "success",
            "title": "Improved Cost Efficiency",
            "text": f"CPC dropped {abs(cpc_change):.0f}% from ${prev_data['cpc']:.2f} to ${data['cpc']:.2f}. "
                   "This demonstrates excellent optimization results."
        })
    elif clicks_change < -15:
        insights.append({
            "icon": "warning",
            "title": "Traffic Volume Decline",
            "text": f"Clicks decreased {abs(clicks_change):.0f}% week-over-week. This may be due to seasonal factors, "
                   "competitive pressure, or budget pacing. Recommend reviewing search impression share."
        })
    elif spend_change < -10 and abs(clicks_change) < 5:
        insights.append({
            "icon": "success",
            "title": "Cost Savings with Maintained Volume",
            "text": f"Spend decreased {abs(spend_change):.0f}% while maintaining click volume. "
                   "The campaign is delivering the same traffic at lower cost."
        })

    # Recommendations
    insights.append({
        "icon": "info",
        "title": "Recommendations",
        "text": generate_recommendations(data, prev_data, clicks_change, ctr_change, cpc_change)
    })

    return insights


def generate_recommendations(data, prev_data, clicks_change, ctr_change, cpc_change):
    """Generate contextual recommendations."""
    recs = []

    if clicks_change > 30:
        recs.append("Continue current strategy—the scaling approach is working well")
        recs.append("Monitor CTR trends as volume increases to ensure quality")
    elif clicks_change < -15:
        recs.append("Review search impression share to identify if budget or rank is limiting visibility")
        recs.append("Analyze search terms report for new keyword opportunities")

    if ctr_change < -10:
        recs.append("Test new ad copy variations to improve click-through rate")

    if cpc_change > 15:
        recs.append("Review bid strategy and quality scores to improve efficiency")
    elif cpc_change < -10:
        recs.append("Consider reinvesting cost savings to expand reach")

    if data['ctr'] < 3:
        recs.append("Test responsive search ads with more headline/description variations")

    # Default recommendations if none generated
    if len(recs) < 2:
        recs.extend([
            "Monitor competitive landscape for opportunities",
            "Test similar audiences to scale while maintaining efficiency"
        ])

    return "<br>".join([f"{i+1}) {r}" for i, r in enumerate(recs[:4])])


def render_insights(insights):
    """Render insights as HTML."""
    html = ""
    for insight in insights:
        icon_char = "&#10003;" if insight["icon"] == "success" else ("!" if insight["icon"] == "warning" else "&rarr;")
        html += f'''
            <div class="insight-card">
                <div class="insight-header">
                    <div class="insight-icon {insight['icon']}">{icon_char}</div>
                    <div class="insight-title">{insight['title']}</div>
                </div>
                <p class="insight-text">{insight['text']}</p>
            </div>
        '''
    return html


def generate_executive_summary(client_name, data, prev_data):
    """Generate executive summary based on performance."""
    clicks_change = calc_change(data['clicks'], prev_data['clicks'])
    spend_change = calc_change(data['spend'], prev_data['spend'])
    cpc_change = calc_change(data['cpc'], prev_data['cpc'])
    ctr_change = calc_change(data['ctr'], prev_data['ctr'])

    # Determine overall tone
    if clicks_change > 50 or (ctr_change > 20 and cpc_change < -10):
        tone = "<strong>Outstanding week with exceptional performance.</strong>"
    elif clicks_change > 20 or cpc_change < -15:
        tone = "<strong>Strong performance this week.</strong>"
    elif clicks_change < -20 or ctr_change < -20:
        tone = "This week showed some softness in key metrics."
    else:
        tone = "Solid performance this week."

    # Build summary
    summary_parts = [tone]

    if abs(clicks_change) > 10:
        direction = "increased" if clicks_change > 0 else "decreased"
        summary_parts.append(f"Clicks {direction} <strong>{abs(clicks_change):.0f}%</strong> to <strong>{data['clicks']:,.0f}</strong>")

    if abs(ctr_change) > 10:
        direction = "improved" if ctr_change > 0 else "declined"
        summary_parts.append(f"CTR {direction} to <strong>{data['ctr']:.2f}%</strong>")

    if abs(cpc_change) > 10:
        direction = "dropped" if cpc_change < 0 else "increased"
        summary_parts.append(f"CPC {direction} <strong>{abs(cpc_change):.0f}%</strong> to <strong>${data['cpc']:.2f}</strong>")

    summary_parts.append(f"Total investment of <strong>${data['spend']:,.2f}</strong>")

    return " ".join(summary_parts) + "."


def generate_report(client_slug, client_name, data, prev_data, date_range, prev_date_range, week_num):
    """Generate HTML report for a client."""

    # Calculate derived metrics
    data['ctr'] = (data['clicks'] / data['impressions'] * 100) if data['impressions'] > 0 else 0
    data['cpc'] = data['spend'] / data['clicks'] if data['clicks'] > 0 else 0

    prev_data['ctr'] = (prev_data['clicks'] / prev_data['impressions'] * 100) if prev_data['impressions'] > 0 else 0
    prev_data['cpc'] = prev_data['spend'] / prev_data['clicks'] if prev_data['clicks'] > 0 else 0

    # Calculate changes
    spend_change = calc_change(data['spend'], prev_data['spend'])
    impressions_change = calc_change(data['impressions'], prev_data['impressions'])
    clicks_change = calc_change(data['clicks'], prev_data['clicks'])
    ctr_change = calc_change(data['ctr'], prev_data['ctr'])
    cpc_change = calc_change(data['cpc'], prev_data['cpc'])

    # Generate badges
    ctr_badge = '<span class="performance-badge excellent">Excellent</span>' if data['ctr'] >= 10 else ('<span class="performance-badge good">Strong</span>' if data['ctr'] >= 5 else '')
    cpc_badge = '<span class="performance-badge excellent">Efficient</span>' if data['cpc'] < 0.20 else ('<span class="performance-badge good">Good</span>' if data['cpc'] < 0.50 else '')
    clicks_badge = f'<span class="performance-badge excellent">+{clicks_change:.0f}%</span>' if clicks_change > 50 else (f'<span class="performance-badge good">Stable</span>' if abs(clicks_change) < 5 else '')

    # Generate insights
    insights = generate_insights(data, prev_data)

    # Build report
    report = REPORT_TEMPLATE.format(
        client_name=client_name,
        date_range=date_range,
        generated_date=datetime.now().strftime('%B %d, %Y'),
        executive_summary=generate_executive_summary(client_name, data, prev_data),

        # Spend
        spend_display=format_currency(data['spend']),
        spend_change_class=get_change_class(spend_change, invert=True),
        spend_change_text=format_change_text(spend_change, suffix=" cost savings" if spend_change < 0 else " vs last week"),
        spend_exact=f"${data['spend']:,.2f}",
        prev_spend=f"${prev_data['spend']:,.2f}",
        spend_change_pct=f"{'+' if spend_change > 0 else ''}{spend_change:.2f}%",
        spend_table_class=get_table_class(spend_change, invert=True),

        # CTR
        ctr_badge=ctr_badge,
        ctr_display=f"{data['ctr']:.2f}%",
        ctr_change_class=get_change_class(ctr_change),
        ctr_change_text=format_change_text(ctr_change) if prev_data['ctr'] > 0 else "Industry avg: 2-3%",
        ctr_exact=f"{data['ctr']:.2f}%",
        prev_ctr=f"{prev_data['ctr']:.2f}%",
        ctr_change_pct=f"{'+' if ctr_change > 0 else ''}{ctr_change:.2f}%",
        ctr_table_class=get_table_class(ctr_change),

        # CPC
        cpc_badge=cpc_badge,
        cpc_display=f"${data['cpc']:.2f}",
        cpc_change_class=get_change_class(cpc_change, invert=True),
        cpc_change_text=format_change_text(cpc_change, suffix=" more efficient" if cpc_change < 0 else " vs last week", invert=True),
        cpc_exact=f"${data['cpc']:.2f}",
        prev_cpc=f"${prev_data['cpc']:.2f}",
        cpc_change_pct=f"{'+' if cpc_change > 0 else ''}{cpc_change:.2f}%",
        cpc_table_class=get_table_class(cpc_change, invert=True),

        # Clicks
        clicks_badge=clicks_badge,
        clicks_display=format_number(data['clicks']),
        clicks_change_class=get_change_class(clicks_change),
        clicks_change_text=format_change_text(clicks_change),
        clicks_exact=format_number(data['clicks']),
        prev_clicks=format_number(prev_data['clicks']),
        clicks_change_pct=f"{'+' if clicks_change > 0 else ''}{clicks_change:.2f}%",
        clicks_table_class=get_table_class(clicks_change),

        # Impressions
        impressions_display=format_number(data['impressions']),
        impressions_change_class=get_change_class(impressions_change),
        impressions_change_text=format_change_text(impressions_change),
        impressions_exact=format_number(data['impressions']),
        prev_impressions=format_number(prev_data['impressions']),
        impressions_change_pct=f"{'+' if impressions_change > 0 else ''}{impressions_change:.2f}%",
        impressions_table_class=get_table_class(impressions_change),

        # Other
        insights_html=render_insights(insights),
        report_id=f"RHM-{client_slug.upper()[:3]}-{datetime.now().year}-W{week_num:02d}"
    )

    return report


def get_folder_name(start_date, end_date):
    """Generate folder name from dates."""
    start_str = start_date.strftime('%b%d').lower()
    end_str = end_date.strftime('%b%d').lower() if start_date.month == end_date.month else end_date.strftime('%b%d').lower()

    # Handle cross-month/year
    if start_date.month != end_date.month:
        return f"{start_date.strftime('%b').lower()}{start_date.day}-{end_date.strftime('%b').lower()}{end_date.day}"
    return f"{start_date.strftime('%b').lower()}{start_date.day}-{end_date.day}"


def update_index_html(clients_data, date_range, folder_suffix):
    """Update the main index.html with new report links."""

    index_path = REPO_DIR / "index.html"

    # Generate client sections
    sections = []
    for slug, info in CLIENTS.items():
        if slug in clients_data:
            sections.append(f'''
        <!-- {info['name']} -->
        <section class="client-section">
            <div class="section-header">
                <span>{info['name']}</span>
                <span class="client-badge">Google Ads</span>
            </div>
            <div class="report-card">
                <a href="/{slug}-{folder_suffix}/">
                    <div class="report-info">
                        <div class="report-title">
                            Weekly Performance Report
                            <span class="badge-new">New</span>
                        </div>
                        <div class="report-date">{date_range}</div>
                    </div>
                    <span class="arrow-icon">&rarr;</span>
                </a>
            </div>
        </section>''')

    # Read and update index
    with open(index_path, 'r') as f:
        content = f.read()

    # Find and replace client sections
    import re
    pattern = r'<!-- JFTx2025 -->.*?</section>\s*<!-- PFBHNC -->.*?</section>\s*<!-- ReOptica -->.*?</section>'
    replacement = '\n'.join(sections)

    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    with open(index_path, 'w') as f:
        f.write(new_content)

    print(f"Updated index.html")


def interactive_input():
    """Get data interactively from user."""
    print("\n" + "="*60)
    print("ROBERT HEBERT MEDIA - WEEKLY REPORT GENERATOR")
    print("="*60)

    # Get date range
    print("\nEnter the reporting period:")
    print("  Format: Start date - End date (e.g., December 29, 2025 - January 4, 2026)")
    date_range = input("  This week: ").strip()
    prev_date_range = input("  Previous week: ").strip()

    if not date_range:
        # Default to last week
        today = datetime.now()
        end_date = today - timedelta(days=today.weekday() + 1)  # Last Sunday
        start_date = end_date - timedelta(days=6)  # Previous Monday
        date_range = f"{start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}"

        prev_end = start_date - timedelta(days=1)
        prev_start = prev_end - timedelta(days=6)
        prev_date_range = f"{prev_start.strftime('%B %d, %Y')} - {prev_end.strftime('%B %d, %Y')}"

    clients_data = {}

    for slug, info in CLIENTS.items():
        print(f"\n{'-'*40}")
        print(f"Enter data for {info['name']} ({info['customer_id']}):")
        print(f"{'-'*40}")

        include = input(f"  Include {info['name']}? (Y/n): ").strip().lower()
        if include == 'n':
            continue

        print("\n  THIS WEEK:")
        spend = parse_number(input("    Spend ($): "))
        impressions = parse_number(input("    Impressions: "))
        clicks = parse_number(input("    Clicks: "))

        print("\n  PREVIOUS WEEK:")
        prev_spend = parse_number(input("    Spend ($): "))
        prev_impressions = parse_number(input("    Impressions: "))
        prev_clicks = parse_number(input("    Clicks: "))

        clients_data[slug] = {
            'current': {'spend': spend, 'impressions': impressions, 'clicks': clicks},
            'previous': {'spend': prev_spend, 'impressions': prev_impressions, 'clicks': prev_clicks}
        }

    return clients_data, date_range, prev_date_range


def parse_csv(csv_path):
    """Parse Google Ads CSV export."""
    clients_data = {}

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Try to match by account name or customer ID
            account_name = row.get('Account', row.get('account', ''))
            customer_id = row.get('Customer ID', row.get('customer_id', ''))

            for slug, info in CLIENTS.items():
                if info['name'].lower() in account_name.lower() or info['customer_id'].replace('-', '') in customer_id.replace('-', ''):
                    spend = parse_number(row.get('Cost', row.get('cost', row.get('Spend', 0))))
                    impressions = parse_number(row.get('Impressions', row.get('impressions', row.get('Impr.', 0))))
                    clicks = parse_number(row.get('Clicks', row.get('clicks', 0)))

                    clients_data[slug] = {
                        'current': {'spend': spend, 'impressions': impressions, 'clicks': clicks},
                        'previous': {'spend': 0, 'impressions': 0, 'clicks': 0}  # Will need manual input
                    }

    return clients_data


def deploy_to_github():
    """Commit and push to GitHub."""
    os.chdir(REPO_DIR)

    # Add all changes
    subprocess.run(['git', 'add', '-A'], check=True)

    # Commit
    commit_msg = f"""Add weekly reports - {datetime.now().strftime('%B %d, %Y')}

🤖 Generated with weekly_report.py

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"""

    subprocess.run(['git', 'commit', '-m', commit_msg], check=True)

    # Push
    subprocess.run(['git', 'push', 'origin', 'main'], check=True)

    print("\n✓ Deployed to GitHub Pages")
    print("  Reports will be live at: https://reports.roberthebertmedia.com/")


def main():
    parser = argparse.ArgumentParser(description='Generate weekly Google Ads reports')
    parser.add_argument('--csv', help='Path to Google Ads CSV export')
    parser.add_argument('--deploy', action='store_true', help='Auto-deploy to GitHub')
    parser.add_argument('--email', action='store_true', help='Send email notification')
    args = parser.parse_args()

    # Get data
    if args.csv:
        print(f"Parsing CSV: {args.csv}")
        clients_data = parse_csv(args.csv)
        # Still need dates and previous week data
        clients_data, date_range, prev_date_range = interactive_input()
    else:
        clients_data, date_range, prev_date_range = interactive_input()

    if not clients_data:
        print("No client data entered. Exiting.")
        return

    # Parse dates for folder naming
    try:
        # Try to parse the date range
        parts = date_range.split(' - ')
        start_str = parts[0].strip()
        end_str = parts[1].strip()

        # Handle various formats
        for fmt in ['%B %d, %Y', '%B %d %Y', '%b %d, %Y', '%b %d %Y']:
            try:
                start_date = datetime.strptime(start_str, fmt)
                break
            except:
                continue

        for fmt in ['%B %d, %Y', '%B %d %Y', '%b %d, %Y', '%b %d %Y']:
            try:
                end_date = datetime.strptime(end_str, fmt)
                break
            except:
                continue

        folder_suffix = get_folder_name(start_date, end_date)
        week_num = end_date.isocalendar()[1]
    except Exception as e:
        print(f"Warning: Could not parse dates, using default naming. Error: {e}")
        folder_suffix = datetime.now().strftime('%b%d').lower()
        week_num = datetime.now().isocalendar()[1]

    # Generate reports
    print("\n" + "="*60)
    print("GENERATING REPORTS")
    print("="*60)

    for slug, data in clients_data.items():
        client_name = CLIENTS[slug]['name']
        print(f"\n  Generating report for {client_name}...")

        # Create folder
        folder_path = REPO_DIR / f"{slug}-{folder_suffix}"
        folder_path.mkdir(exist_ok=True)

        # Generate report HTML
        html = generate_report(
            slug, client_name,
            data['current'], data['previous'],
            date_range, prev_date_range,
            week_num
        )

        # Write report
        report_path = folder_path / "index.html"
        with open(report_path, 'w') as f:
            f.write(html)

        print(f"    ✓ Saved: {report_path}")

    # Update index
    print("\n  Updating index.html...")
    update_index_html(clients_data, date_range, folder_suffix)

    # Deploy if requested
    if args.deploy:
        print("\n" + "="*60)
        print("DEPLOYING TO GITHUB")
        print("="*60)
        deploy_to_github()

    # Print summary
    print("\n" + "="*60)
    print("COMPLETE!")
    print("="*60)

    for slug in clients_data:
        print(f"\n  {CLIENTS[slug]['name']}:")
        print(f"    https://reports.roberthebertmedia.com/{slug}-{folder_suffix}/")

    if not args.deploy:
        print("\n  To deploy, run:")
        print(f"    cd {REPO_DIR}")
        print("    git add -A && git commit -m 'Add weekly reports' && git push")

    print("\n" + "="*60)


if __name__ == "__main__":
    main()
