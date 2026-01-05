"""
Robert Hebert Media - Automated Google Ads Weekly Report Generator
Runs every Monday at 8:00 AM CST via Cloud Scheduler
"""

import os
import json
import base64
import subprocess
from datetime import datetime, timedelta
from google.cloud import secretmanager
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType
import tempfile


# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ID = os.environ.get('GCP_PROJECT', 'hendricks-ai-prod')
GITHUB_REPO = 'BLincoln711/robert-hebert-media-reports'
REPORTS_DOMAIN = 'https://reports.roberthebertmedia.com'

# Lead Gen Metrics to track
METRICS = [
    'metrics.impressions',
    'metrics.clicks',
    'metrics.cost_micros',
    'metrics.conversions',
    'metrics.conversions_value',
    'metrics.all_conversions',
    'metrics.cost_per_conversion',
    'metrics.conversions_from_interactions_rate',
    'metrics.ctr',
    'metrics.average_cpc',
]

DIMENSIONS = [
    'campaign.name',
    'campaign.status',
    'segments.date',
    'segments.device',
]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_secret(secret_name):
    """Retrieve secret from Google Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


def load_clients_config():
    """Load client configuration from clients.json."""
    config_path = os.path.join(os.path.dirname(__file__), 'clients.json')
    with open(config_path, 'r') as f:
        return json.load(f)


def get_date_range():
    """Get the date range for the report (last 7 days)."""
    today = datetime.now()
    # Find the most recent Sunday (end of report period)
    days_since_sunday = (today.weekday() + 1) % 7
    end_date = today - timedelta(days=days_since_sunday)
    start_date = end_date - timedelta(days=6)

    return {
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'display_start': start_date.strftime('%B %d'),
        'display_end': end_date.strftime('%d, %Y'),
        'folder_name': f"{start_date.strftime('%b').lower()}{start_date.day}-{end_date.day}"
    }


def format_currency(micros):
    """Convert micros to dollars with formatting."""
    if micros is None:
        return "$0.00"
    return f"${micros / 1_000_000:,.2f}"


def format_number(num):
    """Format number with commas."""
    if num is None:
        return "0"
    return f"{num:,.0f}"


def format_percent(decimal):
    """Format decimal as percentage."""
    if decimal is None:
        return "0.00%"
    return f"{decimal * 100:.2f}%"


def calculate_change(current, previous):
    """Calculate percentage change between two values."""
    if previous == 0:
        return 0 if current == 0 else 100
    return ((current - previous) / previous) * 100


# ============================================================================
# GOOGLE ADS API
# ============================================================================

def get_google_ads_client(client_config):
    """Initialize Google Ads API client."""
    # Get credentials from Secret Manager
    google_ads_yaml = get_secret('google-ads-credentials')

    # Write to temp file for GoogleAdsClient
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(google_ads_yaml)
        temp_path = f.name

    try:
        client = GoogleAdsClient.load_from_storage(temp_path)
        return client
    finally:
        os.unlink(temp_path)


def fetch_google_ads_data(client, customer_id, start_date, end_date):
    """Fetch Google Ads performance data for the date range."""
    ga_service = client.get_service("GoogleAdsService")

    query = f"""
        SELECT
            campaign.name,
            campaign.status,
            segments.date,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions,
            metrics.all_conversions,
            metrics.ctr,
            metrics.average_cpc
        FROM campaign
        WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
            AND campaign.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC
    """

    response = ga_service.search(customer_id=customer_id, query=query)

    # Aggregate data
    data = {
        'campaigns': {},
        'daily': {},
        'totals': {
            'impressions': 0,
            'clicks': 0,
            'cost_micros': 0,
            'conversions': 0,
            'all_conversions': 0,
        }
    }

    for row in response:
        campaign_name = row.campaign.name
        date = row.segments.date

        # Campaign aggregation
        if campaign_name not in data['campaigns']:
            data['campaigns'][campaign_name] = {
                'impressions': 0,
                'clicks': 0,
                'cost_micros': 0,
                'conversions': 0,
                'status': row.campaign.status.name,
            }

        data['campaigns'][campaign_name]['impressions'] += row.metrics.impressions
        data['campaigns'][campaign_name]['clicks'] += row.metrics.clicks
        data['campaigns'][campaign_name]['cost_micros'] += row.metrics.cost_micros
        data['campaigns'][campaign_name]['conversions'] += row.metrics.conversions

        # Daily aggregation
        if date not in data['daily']:
            data['daily'][date] = {
                'impressions': 0,
                'clicks': 0,
                'cost_micros': 0,
                'conversions': 0,
            }

        data['daily'][date]['impressions'] += row.metrics.impressions
        data['daily'][date]['clicks'] += row.metrics.clicks
        data['daily'][date]['cost_micros'] += row.metrics.cost_micros
        data['daily'][date]['conversions'] += row.metrics.conversions

        # Totals
        data['totals']['impressions'] += row.metrics.impressions
        data['totals']['clicks'] += row.metrics.clicks
        data['totals']['cost_micros'] += row.metrics.cost_micros
        data['totals']['conversions'] += row.metrics.conversions
        data['totals']['all_conversions'] += row.metrics.all_conversions

    # Calculate derived metrics
    totals = data['totals']
    if totals['clicks'] > 0:
        totals['ctr'] = totals['clicks'] / totals['impressions'] if totals['impressions'] > 0 else 0
        totals['cpc'] = totals['cost_micros'] / totals['clicks']
    else:
        totals['ctr'] = 0
        totals['cpc'] = 0

    if totals['conversions'] > 0:
        totals['cpl'] = totals['cost_micros'] / totals['conversions']
        totals['conversion_rate'] = totals['conversions'] / totals['clicks'] if totals['clicks'] > 0 else 0
    else:
        totals['cpl'] = 0
        totals['conversion_rate'] = 0

    return data


def fetch_previous_period_data(client, customer_id, start_date, end_date):
    """Fetch previous period data for comparison."""
    # Calculate previous period dates
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    period_length = (end - start).days + 1

    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=period_length - 1)

    return fetch_google_ads_data(
        client,
        customer_id,
        prev_start.strftime('%Y-%m-%d'),
        prev_end.strftime('%Y-%m-%d')
    )


# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_html_report(client_name, data, prev_data, date_range):
    """Generate branded HTML report."""

    totals = data['totals']
    prev_totals = prev_data['totals']

    # Calculate week-over-week changes
    changes = {
        'impressions': calculate_change(totals['impressions'], prev_totals['impressions']),
        'clicks': calculate_change(totals['clicks'], prev_totals['clicks']),
        'conversions': calculate_change(totals['conversions'], prev_totals['conversions']),
        'cost': calculate_change(totals['cost_micros'], prev_totals['cost_micros']),
        'cpl': calculate_change(totals['cpl'], prev_totals['cpl']),
        'ctr': calculate_change(totals['ctr'], prev_totals['ctr']),
    }

    # Generate daily chart data
    daily_labels = sorted(data['daily'].keys())
    daily_conversions = [data['daily'][d]['conversions'] for d in daily_labels]
    daily_spend = [data['daily'][d]['cost_micros'] / 1_000_000 for d in daily_labels]

    # Format daily labels for display
    daily_labels_display = [datetime.strptime(d, '%Y-%m-%d').strftime('%a %m/%d') for d in daily_labels]

    # Generate campaign table rows
    campaign_rows = ""
    for name, metrics in sorted(data['campaigns'].items(), key=lambda x: x[1]['cost_micros'], reverse=True):
        cpl = metrics['cost_micros'] / metrics['conversions'] if metrics['conversions'] > 0 else 0
        cvr = (metrics['conversions'] / metrics['clicks'] * 100) if metrics['clicks'] > 0 else 0
        campaign_rows += f"""
            <tr>
                <td style="font-weight: 600;">{name}</td>
                <td>{format_currency(metrics['cost_micros'])}</td>
                <td>{format_number(metrics['impressions'])}</td>
                <td>{format_number(metrics['clicks'])}</td>
                <td>{metrics['conversions']:.1f}</td>
                <td>{format_currency(cpl)}</td>
                <td>{cvr:.1f}%</td>
            </tr>
        """

    def change_indicator(change, invert=False):
        """Generate change indicator HTML. Invert for metrics where down is good (like CPL)."""
        if change == 0:
            return '<span style="color: #666;">—</span>'
        is_positive = change > 0 if not invert else change < 0
        color = '#22c55e' if is_positive else '#ef4444'
        arrow = '↑' if change > 0 else '↓'
        return f'<span style="color: {color}; font-weight: 600;">{arrow} {abs(change):.1f}%</span>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Google Ads Report - {client_name} - Week of {date_range['display_start']}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: #0f0f0f;
            color: #e5e5e5;
            line-height: 1.6;
        }}

        .header {{
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            padding: 40px 20px;
            text-align: center;
        }}

        .header h1 {{
            color: #00d4ff;
            font-size: 2rem;
            margin-bottom: 8px;
        }}

        .header .subtitle {{
            color: #a0a0a0;
            font-size: 1.1rem;
        }}

        .header .date-range {{
            color: #00d4ff;
            font-weight: 600;
            margin-top: 12px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}

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

        .metric-card .value {{
            color: #00d4ff;
            font-size: 2rem;
            font-weight: 700;
        }}

        .metric-card .change {{
            margin-top: 8px;
            font-size: 0.9rem;
        }}

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

        .chart-container {{
            position: relative;
            height: 300px;
            margin: 20px 0;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 16px;
        }}

        th, td {{
            padding: 14px 12px;
            text-align: left;
            border-bottom: 1px solid #2a2a4e;
        }}

        th {{
            color: #00d4ff;
            font-weight: 600;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        tr:hover {{
            background: rgba(0, 212, 255, 0.05);
        }}

        .highlight {{
            background: linear-gradient(135deg, rgba(0, 212, 255, 0.1), rgba(0, 212, 255, 0.05));
            border: 1px solid rgba(0, 212, 255, 0.3);
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
        }}

        .highlight-title {{
            color: #00d4ff;
            font-weight: 700;
            margin-bottom: 8px;
        }}

        .footer {{
            text-align: center;
            padding: 40px 20px;
            color: #666;
            font-size: 0.85rem;
        }}

        .footer a {{
            color: #00d4ff;
            text-decoration: none;
        }}

        .badge {{
            display: inline-block;
            background: linear-gradient(135deg, #00d4ff, #0088cc);
            color: #000;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
        }}

        @media (max-width: 768px) {{
            .metrics-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}

            .header h1 {{
                font-size: 1.5rem;
            }}

            table {{
                font-size: 0.85rem;
            }}

            th, td {{
                padding: 10px 8px;
            }}
        }}
    </style>
</head>
<body>
    <header class="header">
        <h1>📊 Google Ads Performance Report</h1>
        <p class="subtitle">{client_name}</p>
        <p class="date-range">Week of {date_range['display_start']} - {date_range['display_end']}</p>
    </header>

    <div class="container">
        <!-- Key Metrics -->
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="label">Total Spend</div>
                <div class="value">{format_currency(totals['cost_micros'])}</div>
                <div class="change">{change_indicator(changes['cost'])}</div>
            </div>
            <div class="metric-card">
                <div class="label">Conversions</div>
                <div class="value">{totals['conversions']:.1f}</div>
                <div class="change">{change_indicator(changes['conversions'])}</div>
            </div>
            <div class="metric-card">
                <div class="label">Cost Per Lead</div>
                <div class="value">{format_currency(totals['cpl'])}</div>
                <div class="change">{change_indicator(changes['cpl'], invert=True)}</div>
            </div>
            <div class="metric-card">
                <div class="label">Conversion Rate</div>
                <div class="value">{format_percent(totals['conversion_rate'])}</div>
                <div class="change">{change_indicator(changes['ctr'])}</div>
            </div>
            <div class="metric-card">
                <div class="label">Clicks</div>
                <div class="value">{format_number(totals['clicks'])}</div>
                <div class="change">{change_indicator(changes['clicks'])}</div>
            </div>
            <div class="metric-card">
                <div class="label">Impressions</div>
                <div class="value">{format_number(totals['impressions'])}</div>
                <div class="change">{change_indicator(changes['impressions'])}</div>
            </div>
        </div>

        <!-- Executive Summary -->
        <div class="highlight">
            <div class="highlight-title">📈 Weekly Highlights</div>
            <p>
                This week generated <strong>{totals['conversions']:.0f} conversions</strong>
                at an average cost of <strong>{format_currency(totals['cpl'])}</strong> per lead.
                Total ad spend was <strong>{format_currency(totals['cost_micros'])}</strong>
                with a click-through rate of <strong>{format_percent(totals['ctr'])}</strong>.
            </p>
        </div>

        <!-- Daily Performance Chart -->
        <div class="section">
            <h2 class="section-title">📅 Daily Performance</h2>
            <div class="chart-container">
                <canvas id="dailyChart"></canvas>
            </div>
        </div>

        <!-- Campaign Performance -->
        <div class="section">
            <h2 class="section-title">🎯 Campaign Performance</h2>
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
        <p>Report generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        <p style="margin-top: 8px;">Powered by <a href="https://roberthebertmedia.com">Robert Hebert Media</a></p>
    </footer>

    <script>
        // Daily Performance Chart
        const ctx = document.getElementById('dailyChart').getContext('2d');
        new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(daily_labels_display)},
                datasets: [
                    {{
                        label: 'Conversions',
                        data: {json.dumps(daily_conversions)},
                        backgroundColor: 'rgba(0, 212, 255, 0.8)',
                        borderColor: '#00d4ff',
                        borderWidth: 2,
                        borderRadius: 6,
                        yAxisID: 'y'
                    }},
                    {{
                        label: 'Spend ($)',
                        data: {json.dumps(daily_spend)},
                        type: 'line',
                        borderColor: '#ff6b6b',
                        backgroundColor: 'transparent',
                        borderWidth: 3,
                        tension: 0.3,
                        pointRadius: 6,
                        pointBackgroundColor: '#ff6b6b',
                        yAxisID: 'y1'
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                interaction: {{
                    mode: 'index',
                    intersect: false,
                }},
                plugins: {{
                    legend: {{
                        labels: {{
                            color: '#a0a0a0',
                            usePointStyle: true,
                            padding: 20
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        ticks: {{ color: '#888' }},
                        grid: {{ color: 'rgba(255,255,255,0.05)' }}
                    }},
                    y: {{
                        type: 'linear',
                        display: true,
                        position: 'left',
                        ticks: {{ color: '#00d4ff' }},
                        grid: {{ color: 'rgba(255,255,255,0.05)' }},
                        title: {{
                            display: true,
                            text: 'Conversions',
                            color: '#00d4ff'
                        }}
                    }},
                    y1: {{
                        type: 'linear',
                        display: true,
                        position: 'right',
                        ticks: {{
                            color: '#ff6b6b',
                            callback: function(value) {{ return '$' + value; }}
                        }},
                        grid: {{ drawOnChartArea: false }},
                        title: {{
                            display: true,
                            text: 'Spend ($)',
                            color: '#ff6b6b'
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>"""

    return html


# ============================================================================
# EMAIL NOTIFICATION
# ============================================================================

def send_email_notification(client_config, report_url, date_range):
    """Send email notification with report link."""
    sendgrid_api_key = get_secret('sendgrid-api-key')

    html_content = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); padding: 30px; text-align: center; border-radius: 12px 12px 0 0;">
            <h1 style="color: #00d4ff; margin: 0;">📊 Your Weekly Google Ads Report</h1>
            <p style="color: #a0a0a0; margin-top: 8px;">{client_config['name']}</p>
        </div>
        <div style="background: #1a1a2e; padding: 30px; border-radius: 0 0 12px 12px;">
            <p style="color: #e5e5e5; font-size: 16px;">
                Your Google Ads performance report for the week of
                <strong style="color: #00d4ff;">{date_range['display_start']} - {date_range['display_end']}</strong>
                is now ready.
            </p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{report_url}" style="background: linear-gradient(135deg, #00d4ff, #0088cc); color: #000; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: 700; font-size: 16px; display: inline-block;">
                    View Full Report →
                </a>
            </div>
            <p style="color: #888; font-size: 14px; text-align: center;">
                This report is available at:<br>
                <a href="{report_url}" style="color: #00d4ff;">{report_url}</a>
            </p>
        </div>
        <div style="text-align: center; padding: 20px; color: #666; font-size: 12px;">
            Powered by <a href="https://roberthebertmedia.com" style="color: #00d4ff; text-decoration: none;">Robert Hebert Media</a>
        </div>
    </div>
    """

    message = Mail(
        from_email='reports@roberthebertmedia.com',
        to_emails=client_config['email'],
        subject=f'📊 Weekly Google Ads Report - {date_range["display_start"]}',
        html_content=html_content
    )

    # CC additional recipients if specified
    if 'cc' in client_config:
        for cc_email in client_config['cc']:
            message.add_cc(cc_email)

    # BCC additional recipients if specified
    if 'bcc' in client_config:
        for bcc_email in client_config['bcc']:
            message.add_bcc(bcc_email)

    try:
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        print(f"Email sent to {client_config['email']}: {response.status_code}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


# ============================================================================
# GITHUB DEPLOYMENT
# ============================================================================

def deploy_to_github(client_slug, html_content, date_range):
    """Deploy report to GitHub Pages."""
    github_token = get_secret('github-token')

    folder_name = f"{client_slug}-{date_range['folder_name']}"

    # Create temporary directory and file
    import tempfile
    import shutil

    with tempfile.TemporaryDirectory() as tmpdir:
        # Clone repo
        repo_url = f"https://{github_token}@github.com/{GITHUB_REPO}.git"
        subprocess.run(['git', 'clone', '--depth', '1', repo_url, tmpdir], check=True)

        # Create report directory
        report_dir = os.path.join(tmpdir, folder_name)
        os.makedirs(report_dir, exist_ok=True)

        # Write report
        report_path = os.path.join(report_dir, 'index.html')
        with open(report_path, 'w') as f:
            f.write(html_content)

        # Git commit and push
        os.chdir(tmpdir)
        subprocess.run(['git', 'config', 'user.email', 'reports@roberthebertmedia.com'], check=True)
        subprocess.run(['git', 'config', 'user.name', 'RHM Report Bot'], check=True)
        subprocess.run(['git', 'add', '-A'], check=True)
        subprocess.run(['git', 'commit', '-m', f'Add {client_slug} report for {date_range["folder_name"]}'], check=True)
        subprocess.run(['git', 'push'], check=True)

    return f"{REPORTS_DOMAIN}/{folder_name}/"


# ============================================================================
# MAIN CLOUD FUNCTION
# ============================================================================

def generate_weekly_reports(request):
    """
    Main Cloud Function entry point.
    Triggered by Cloud Scheduler every Monday at 8:00 AM CST.
    """
    try:
        clients = load_clients_config()
        date_range = get_date_range()

        results = []

        for client in clients['clients']:
            try:
                print(f"Processing {client['name']}...")

                # Initialize Google Ads client
                ads_client = get_google_ads_client(client)

                # Fetch current and previous period data
                current_data = fetch_google_ads_data(
                    ads_client,
                    client['customer_id'],
                    date_range['start_date'],
                    date_range['end_date']
                )

                prev_data = fetch_previous_period_data(
                    ads_client,
                    client['customer_id'],
                    date_range['start_date'],
                    date_range['end_date']
                )

                # Generate HTML report
                html = generate_html_report(
                    client['name'],
                    current_data,
                    prev_data,
                    date_range
                )

                # Deploy to GitHub Pages
                report_url = deploy_to_github(client['slug'], html, date_range)

                # Send email notification
                send_email_notification(client, report_url, date_range)

                results.append({
                    'client': client['name'],
                    'status': 'success',
                    'url': report_url
                })

            except Exception as e:
                print(f"Error processing {client['name']}: {e}")
                results.append({
                    'client': client['name'],
                    'status': 'error',
                    'error': str(e)
                })

        return {
            'status': 'complete',
            'date_range': date_range,
            'results': results
        }

    except Exception as e:
        print(f"Fatal error: {e}")
        return {'status': 'error', 'error': str(e)}


# For local testing
if __name__ == '__main__':
    result = generate_weekly_reports(None)
    print(json.dumps(result, indent=2))
