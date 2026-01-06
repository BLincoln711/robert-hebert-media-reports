/**
 * Robert Hebert Media - Weekly Report Generator
 * Google Apps Script for automated report generation and deployment
 *
 * Setup:
 * 1. Copy this code to Extensions > Apps Script
 * 2. Configure the sheets as described in google-sheets-setup.md
 * 3. Set up a weekly trigger for generateWeeklyReports()
 */

// ============================================
// MAIN FUNCTION - Run this weekly
// ============================================

function generateWeeklyReports() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  // Get configuration
  const config = getConfig(ss);
  const clients = getClients(ss);
  const dateRange = getDateRange(ss);
  const thisWeekData = getWeekData(ss, 'This Week');
  const prevWeekData = getWeekData(ss, 'Previous Week');

  Logger.log('Starting report generation...');
  Logger.log('Date range: ' + dateRange.thisWeek);

  const reportUrls = [];
  const folderSuffix = getFolderSuffix(dateRange);

  // Generate report for each active client
  clients.forEach(client => {
    if (!client.active) return;

    const currentData = thisWeekData[client.name];
    const previousData = prevWeekData[client.name];

    if (!currentData) {
      Logger.log('No data for client: ' + client.name);
      return;
    }

    Logger.log('Generating report for: ' + client.name);

    // Generate HTML report
    const html = generateReportHtml(client, currentData, previousData || {spend: 0, impressions: 0, clicks: 0}, dateRange);

    // Deploy to GitHub
    const folderName = client.slug + '-' + folderSuffix;
    deployToGitHub(config, folderName, html);

    reportUrls.push({
      name: client.name,
      url: 'https://reports.roberthebertmedia.com/' + folderName + '/'
    });
  });

  // Update index.html
  updateIndexHtml(config, clients, dateRange, folderSuffix);

  // Send email notification
  sendEmailNotification(config, reportUrls, dateRange.thisWeek);

  Logger.log('Report generation complete!');
}

// ============================================
// DATA READING FUNCTIONS
// ============================================

function getConfig(ss) {
  const sheet = ss.getSheetByName('Config');
  const data = sheet.getDataRange().getValues();
  const config = {};

  data.forEach(row => {
    if (row[0] && row[1]) {
      config[row[0]] = row[1];
    }
  });

  return config;
}

function getClients(ss) {
  const sheet = ss.getSheetByName('Clients');
  const data = sheet.getDataRange().getValues();
  const clients = [];

  // Skip header row
  for (let i = 1; i < data.length; i++) {
    if (data[i][0]) {
      clients.push({
        name: data[i][0],
        slug: data[i][1],
        customerId: data[i][2],
        active: data[i][3] === true || data[i][3] === 'TRUE'
      });
    }
  }

  return clients;
}

function getDateRange(ss) {
  const sheet = ss.getSheetByName('Date Range');
  const data = sheet.getDataRange().getValues();
  const dates = {};

  data.forEach(row => {
    if (row[0] && row[1]) {
      dates[row[0]] = row[1];
    }
  });

  // Format date ranges
  const formatDate = (date) => {
    if (date instanceof Date) {
      return Utilities.formatDate(date, 'America/Chicago', 'MMMM d, yyyy');
    }
    return date;
  };

  return {
    thisWeek: formatDate(dates.this_week_start) + ' &ndash; ' + formatDate(dates.this_week_end),
    prevWeek: formatDate(dates.prev_week_start) + ' &ndash; ' + formatDate(dates.prev_week_end),
    thisWeekStart: dates.this_week_start,
    thisWeekEnd: dates.this_week_end
  };
}

function getWeekData(ss, sheetName) {
  const sheet = ss.getSheetByName(sheetName);
  const data = sheet.getDataRange().getValues();
  const weekData = {};

  // Skip header row
  for (let i = 1; i < data.length; i++) {
    if (data[i][0]) {
      weekData[data[i][0]] = {
        spend: parseFloat(data[i][1]) || 0,
        impressions: parseInt(data[i][2]) || 0,
        clicks: parseInt(data[i][3]) || 0
      };
    }
  }

  return weekData;
}

function getFolderSuffix(dateRange) {
  const start = dateRange.thisWeekStart;
  const end = dateRange.thisWeekEnd;

  const startDate = start instanceof Date ? start : new Date(start);
  const endDate = end instanceof Date ? end : new Date(end);

  const months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'];

  const startMonth = months[startDate.getMonth()];
  const endMonth = months[endDate.getMonth()];
  const startDay = startDate.getDate();
  const endDay = endDate.getDate();

  if (startMonth === endMonth) {
    return startMonth + startDay + '-' + endDay;
  } else {
    return startMonth + startDay + '-' + endMonth + endDay;
  }
}

// ============================================
// REPORT GENERATION
// ============================================

function generateReportHtml(client, current, previous, dateRange) {
  // Calculate derived metrics
  current.ctr = current.impressions > 0 ? (current.clicks / current.impressions * 100) : 0;
  current.cpc = current.clicks > 0 ? (current.spend / current.clicks) : 0;

  previous.ctr = previous.impressions > 0 ? (previous.clicks / previous.impressions * 100) : 0;
  previous.cpc = previous.clicks > 0 ? (previous.spend / previous.clicks) : 0;

  // Calculate changes
  const calcChange = (curr, prev) => prev === 0 ? (curr === 0 ? 0 : 100) : ((curr - prev) / prev * 100);

  const changes = {
    spend: calcChange(current.spend, previous.spend),
    impressions: calcChange(current.impressions, previous.impressions),
    clicks: calcChange(current.clicks, previous.clicks),
    ctr: calcChange(current.ctr, previous.ctr),
    cpc: calcChange(current.cpc, previous.cpc)
  };

  // Generate executive summary
  const summary = generateSummary(client.name, current, changes);

  // Generate insights
  const insights = generateInsights(current, previous, changes);

  // Get week number
  const endDate = dateRange.thisWeekEnd instanceof Date ? dateRange.thisWeekEnd : new Date(dateRange.thisWeekEnd);
  const weekNum = getWeekNumber(endDate);

  return getReportTemplate()
    .replace(/{client_name}/g, client.name)
    .replace(/{date_range}/g, dateRange.thisWeek)
    .replace(/{generated_date}/g, Utilities.formatDate(new Date(), 'America/Chicago', 'MMMM d, yyyy'))
    .replace(/{executive_summary}/g, summary)

    // Spend
    .replace(/{spend_display}/g, formatCurrency(current.spend))
    .replace(/{spend_change_class}/g, getChangeClass(changes.spend, true))
    .replace(/{spend_change_text}/g, formatChangeText(changes.spend, changes.spend < 0 ? ' cost savings' : ' vs last week'))
    .replace(/{spend_exact}/g, '$' + current.spend.toFixed(2))
    .replace(/{prev_spend}/g, '$' + previous.spend.toFixed(2))
    .replace(/{spend_change_pct}/g, formatChangePct(changes.spend))
    .replace(/{spend_table_class}/g, getTableClass(changes.spend, true))

    // CTR
    .replace(/{ctr_badge}/g, getCtrBadge(current.ctr))
    .replace(/{ctr_display}/g, current.ctr.toFixed(2) + '%')
    .replace(/{ctr_change_class}/g, getChangeClass(changes.ctr))
    .replace(/{ctr_change_text}/g, previous.ctr > 0 ? formatChangeText(changes.ctr) : 'Industry avg: 2-3%')
    .replace(/{ctr_exact}/g, current.ctr.toFixed(2) + '%')
    .replace(/{prev_ctr}/g, previous.ctr.toFixed(2) + '%')
    .replace(/{ctr_change_pct}/g, formatChangePct(changes.ctr))
    .replace(/{ctr_table_class}/g, getTableClass(changes.ctr))

    // CPC
    .replace(/{cpc_badge}/g, getCpcBadge(current.cpc))
    .replace(/{cpc_display}/g, '$' + current.cpc.toFixed(2))
    .replace(/{cpc_change_class}/g, getChangeClass(changes.cpc, true))
    .replace(/{cpc_change_text}/g, formatChangeText(changes.cpc, changes.cpc < 0 ? ' more efficient' : ' vs last week', true))
    .replace(/{cpc_exact}/g, '$' + current.cpc.toFixed(2))
    .replace(/{prev_cpc}/g, '$' + previous.cpc.toFixed(2))
    .replace(/{cpc_change_pct}/g, formatChangePct(changes.cpc))
    .replace(/{cpc_table_class}/g, getTableClass(changes.cpc, true))

    // Clicks
    .replace(/{clicks_badge}/g, getClicksBadge(changes.clicks))
    .replace(/{clicks_display}/g, formatNumber(current.clicks))
    .replace(/{clicks_change_class}/g, getChangeClass(changes.clicks))
    .replace(/{clicks_change_text}/g, formatChangeText(changes.clicks))
    .replace(/{clicks_exact}/g, formatNumber(current.clicks))
    .replace(/{prev_clicks}/g, formatNumber(previous.clicks))
    .replace(/{clicks_change_pct}/g, formatChangePct(changes.clicks))
    .replace(/{clicks_table_class}/g, getTableClass(changes.clicks))

    // Impressions
    .replace(/{impressions_display}/g, formatNumber(current.impressions))
    .replace(/{impressions_change_class}/g, getChangeClass(changes.impressions))
    .replace(/{impressions_change_text}/g, formatChangeText(changes.impressions))
    .replace(/{impressions_exact}/g, formatNumber(current.impressions))
    .replace(/{prev_impressions}/g, formatNumber(previous.impressions))
    .replace(/{impressions_change_pct}/g, formatChangePct(changes.impressions))
    .replace(/{impressions_table_class}/g, getTableClass(changes.impressions))

    // Other
    .replace(/{insights_html}/g, insights)
    .replace(/{report_id}/g, 'RHM-' + client.slug.toUpperCase().substring(0,3) + '-' + endDate.getFullYear() + '-W' + String(weekNum).padStart(2, '0'));
}

function generateSummary(clientName, current, changes) {
  let tone = '';
  if (changes.clicks > 50 || (changes.ctr > 20 && changes.cpc < -10)) {
    tone = '<strong>Outstanding week with exceptional performance.</strong> ';
  } else if (changes.clicks > 20 || changes.cpc < -15) {
    tone = '<strong>Strong performance this week.</strong> ';
  } else if (changes.clicks < -20 || changes.ctr < -20) {
    tone = 'This week showed some softness in key metrics. ';
  } else {
    tone = 'Solid performance this week. ';
  }

  let details = [];

  if (Math.abs(changes.clicks) > 10) {
    const direction = changes.clicks > 0 ? 'increased' : 'decreased';
    details.push('Clicks ' + direction + ' <strong>' + Math.abs(changes.clicks).toFixed(0) + '%</strong> to <strong>' + formatNumber(current.clicks) + '</strong>');
  }

  if (Math.abs(changes.ctr) > 10) {
    const direction = changes.ctr > 0 ? 'improved' : 'declined';
    details.push('CTR ' + direction + ' to <strong>' + current.ctr.toFixed(2) + '%</strong>');
  }

  if (Math.abs(changes.cpc) > 10) {
    const direction = changes.cpc < 0 ? 'dropped' : 'increased';
    details.push('CPC ' + direction + ' <strong>' + Math.abs(changes.cpc).toFixed(0) + '%</strong> to <strong>$' + current.cpc.toFixed(2) + '</strong>');
  }

  details.push('Total investment of <strong>$' + current.spend.toFixed(2) + '</strong>');

  return tone + details.join('. ') + '.';
}

function generateInsights(current, previous, changes) {
  let html = '';

  // CTR insight
  if (current.ctr >= 10) {
    html += createInsightCard('success', 'Outstanding CTR Performance',
      'A ' + current.ctr.toFixed(2) + '% CTR is exceptional&mdash;approximately 5-7x the industry average. ' +
      (changes.ctr > 5 ? 'The ' + changes.ctr.toFixed(0) + '% improvement week-over-week indicates strong ad relevance.' : 'This indicates highly effective ad copy and targeting.'));
  } else if (current.ctr >= 5) {
    html += createInsightCard('success', 'Strong Click-Through Rate',
      'A ' + current.ctr.toFixed(2) + '% CTR is approximately 2x the industry average, indicating strong ad relevance and effective messaging.');
  } else if (current.ctr < 2) {
    html += createInsightCard('warning', 'CTR Optimization Opportunity',
      'A ' + current.ctr.toFixed(2) + '% CTR is below industry average (2-3%). Recommend testing new ad copy and reviewing keyword relevance.');
  }

  // Efficiency insight
  if (changes.clicks > 50 && changes.cpc < 0) {
    html += createInsightCard('success', 'Exceptional Scale Achievement',
      'Clicks increased ' + changes.clicks.toFixed(0) + '% while CPC decreased ' + Math.abs(changes.cpc).toFixed(0) + '%. The campaign successfully scaled with improved efficiency.');
  } else if (changes.cpc < -15) {
    html += createInsightCard('success', 'Improved Cost Efficiency',
      'CPC dropped ' + Math.abs(changes.cpc).toFixed(0) + '% from $' + previous.cpc.toFixed(2) + ' to $' + current.cpc.toFixed(2) + '. This demonstrates excellent optimization results.');
  } else if (changes.clicks < -15) {
    html += createInsightCard('warning', 'Traffic Volume Decline',
      'Clicks decreased ' + Math.abs(changes.clicks).toFixed(0) + '% week-over-week. This may be due to seasonal factors, competitive pressure, or budget pacing. Recommend reviewing search impression share.');
  }

  // Recommendations
  html += createInsightCard('info', 'Recommendations', generateRecommendations(current, changes));

  return html;
}

function generateRecommendations(current, changes) {
  let recs = [];

  if (changes.clicks > 30) {
    recs.push('Continue current strategy&mdash;the scaling approach is working well');
    recs.push('Monitor CTR trends as volume increases to ensure quality');
  } else if (changes.clicks < -15) {
    recs.push('Review search impression share to identify if budget or rank is limiting visibility');
    recs.push('Analyze search terms report for new keyword opportunities');
  }

  if (changes.ctr < -10) {
    recs.push('Test new ad copy variations to improve click-through rate');
  }

  if (changes.cpc > 15) {
    recs.push('Review bid strategy and quality scores to improve efficiency');
  } else if (changes.cpc < -10) {
    recs.push('Consider reinvesting cost savings to expand reach');
  }

  if (recs.length < 2) {
    recs.push('Monitor competitive landscape for opportunities');
    recs.push('Test similar audiences to scale while maintaining efficiency');
  }

  return recs.slice(0, 4).map((r, i) => (i + 1) + ') ' + r).join('<br>');
}

function createInsightCard(type, title, text) {
  const iconChar = type === 'success' ? '&#10003;' : (type === 'warning' ? '!' : '&rarr;');
  return `
    <div class="insight-card">
      <div class="insight-header">
        <div class="insight-icon ${type}">${iconChar}</div>
        <div class="insight-title">${title}</div>
      </div>
      <p class="insight-text">${text}</p>
    </div>
  `;
}

// ============================================
// FORMATTING HELPERS
// ============================================

function formatCurrency(value) {
  if (value >= 1000) {
    return '$' + Math.round(value).toLocaleString();
  }
  return '$' + value.toFixed(2);
}

function formatNumber(value) {
  return Math.round(value).toLocaleString();
}

function formatChangeText(change, suffix, invert) {
  suffix = suffix || ' vs last week';
  if (Math.abs(change) < 0.5) return 'No change';
  const sign = change > 0 ? '+' : '';
  return sign + change.toFixed(1) + '%' + suffix;
}

function formatChangePct(change) {
  const sign = change > 0 ? '+' : '';
  return sign + change.toFixed(2) + '%';
}

function getChangeClass(change, invert) {
  if (Math.abs(change) < 0.5) return 'neutral';
  const isPositive = invert ? change < 0 : change > 0;
  return isPositive ? 'positive' : 'negative';
}

function getTableClass(change, invert) {
  if (Math.abs(change) < 0.5) return '';
  const isPositive = invert ? change < 0 : change > 0;
  return isPositive ? 'change-positive' : 'change-negative';
}

function getCtrBadge(ctr) {
  if (ctr >= 10) return '<span class="performance-badge excellent">Excellent</span>';
  if (ctr >= 5) return '<span class="performance-badge good">Strong</span>';
  return '';
}

function getCpcBadge(cpc) {
  if (cpc < 0.20) return '<span class="performance-badge excellent">Efficient</span>';
  if (cpc < 0.50) return '<span class="performance-badge good">Good</span>';
  return '';
}

function getClicksBadge(change) {
  if (change > 50) return '<span class="performance-badge excellent">+' + Math.round(change) + '%</span>';
  if (Math.abs(change) < 5) return '<span class="performance-badge good">Stable</span>';
  return '';
}

function getWeekNumber(date) {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  const dayNum = d.getUTCDay() || 7;
  d.setUTCDate(d.getUTCDate() + 4 - dayNum);
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  return Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
}

// ============================================
// GITHUB DEPLOYMENT
// ============================================

function deployToGitHub(config, folderName, htmlContent) {
  const token = config.github_token;
  const repo = config.github_repo;
  const path = folderName + '/index.html';

  const url = 'https://api.github.com/repos/' + repo + '/contents/' + path;

  // Check if file exists (to get SHA for update)
  let sha = null;
  try {
    const existingResponse = UrlFetchApp.fetch(url, {
      headers: {
        'Authorization': 'token ' + token,
        'Accept': 'application/vnd.github.v3+json'
      },
      muteHttpExceptions: true
    });

    if (existingResponse.getResponseCode() === 200) {
      sha = JSON.parse(existingResponse.getContentText()).sha;
    }
  } catch (e) {
    // File doesn't exist, that's fine
  }

  // Create or update file
  const payload = {
    message: 'Update ' + folderName + ' report',
    content: Utilities.base64Encode(htmlContent),
    branch: 'main'
  };

  if (sha) {
    payload.sha = sha;
  }

  const response = UrlFetchApp.fetch(url, {
    method: 'PUT',
    headers: {
      'Authorization': 'token ' + token,
      'Accept': 'application/vnd.github.v3+json',
      'Content-Type': 'application/json'
    },
    payload: JSON.stringify(payload)
  });

  Logger.log('Deployed ' + folderName + ': ' + response.getResponseCode());
}

function updateIndexHtml(config, clients, dateRange, folderSuffix) {
  const token = config.github_token;
  const repo = config.github_repo;

  // Generate new index content
  const indexHtml = generateIndexHtml(clients, dateRange.thisWeek, folderSuffix);

  // Deploy
  const url = 'https://api.github.com/repos/' + repo + '/contents/index.html';

  // Get existing SHA
  const existingResponse = UrlFetchApp.fetch(url, {
    headers: {
      'Authorization': 'token ' + token,
      'Accept': 'application/vnd.github.v3+json'
    }
  });

  const sha = JSON.parse(existingResponse.getContentText()).sha;

  const response = UrlFetchApp.fetch(url, {
    method: 'PUT',
    headers: {
      'Authorization': 'token ' + token,
      'Accept': 'application/vnd.github.v3+json',
      'Content-Type': 'application/json'
    },
    payload: JSON.stringify({
      message: 'Update index with new reports',
      content: Utilities.base64Encode(indexHtml),
      sha: sha,
      branch: 'main'
    })
  });

  Logger.log('Updated index.html: ' + response.getResponseCode());
}

function generateIndexHtml(clients, dateRange, folderSuffix) {
  let sections = '';

  clients.forEach(client => {
    if (!client.active) return;

    sections += `
        <!-- ${client.name} -->
        <section class="client-section">
            <div class="section-header">
                <span>${client.name}</span>
                <span class="client-badge">Google Ads</span>
            </div>
            <div class="report-card">
                <a href="/${client.slug}-${folderSuffix}/">
                    <div class="report-info">
                        <div class="report-title">
                            Weekly Performance Report
                            <span class="badge-new">New</span>
                        </div>
                        <div class="report-date">${dateRange}</div>
                    </div>
                    <span class="arrow-icon">&rarr;</span>
                </a>
            </div>
        </section>`;
  });

  return getIndexTemplate().replace('{client_sections}', sections);
}

// ============================================
// EMAIL NOTIFICATION
// ============================================

function sendEmailNotification(config, reportUrls, dateRange) {
  const to = config.email_to;
  const bcc = config.email_bcc;

  let body = 'The weekly performance reports for ' + dateRange + ' are ready:\n\n';
  body += 'Reports Portal: https://reports.roberthebertmedia.com/\n\n';
  body += 'Direct Links:\n';

  reportUrls.forEach(report => {
    body += '• ' + report.name + ': ' + report.url + '\n';
  });

  body += '\nLet me know if you need any changes.\n\nBrandon';

  GmailApp.sendEmail(to, 'Weekly Google Ads Reports Ready - ' + dateRange, body, {
    bcc: bcc,
    name: 'Brandon Hendricks'
  });

  Logger.log('Email sent to: ' + to);
}

// ============================================
// TEMPLATES
// ============================================

function getReportTemplate() {
  return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weekly Performance Report | {client_name} | {date_range}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
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
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #fff;
            color: var(--gray-800);
            line-height: 1.5;
            font-size: 14px;
        }
        .report-container { max-width: 1100px; margin: 0 auto; padding: 40px; }
        .report-header { border-bottom: 3px solid var(--primary); padding-bottom: 24px; margin-bottom: 32px; }
        .header-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; }
        .brand { font-size: 12px; font-weight: 600; color: var(--gray-500); text-transform: uppercase; letter-spacing: 1.5px; }
        .report-date { font-size: 12px; color: var(--gray-500); text-align: right; }
        .client-name { font-size: 32px; font-weight: 700; color: var(--gray-900); margin-bottom: 4px; }
        .report-title { font-size: 18px; font-weight: 400; color: var(--gray-600); }
        .report-period { display: inline-block; background: var(--primary); color: white; padding: 6px 16px; border-radius: 4px; font-size: 13px; font-weight: 500; margin-top: 12px; }
        .executive-summary { background: var(--gray-50); border-left: 4px solid var(--primary); padding: 24px 28px; margin-bottom: 40px; }
        .summary-title { font-size: 11px; font-weight: 600; color: var(--primary); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px; }
        .summary-text { font-size: 16px; color: var(--gray-700); line-height: 1.7; }
        .summary-text strong { color: var(--gray-900); font-weight: 600; }
        .kpi-section { margin-bottom: 48px; }
        .section-header { font-size: 11px; font-weight: 600; color: var(--gray-500); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 20px; padding-bottom: 8px; border-bottom: 1px solid var(--gray-200); }
        .kpi-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }
        .kpi-card { background: white; border: 1px solid var(--gray-200); border-radius: 8px; padding: 24px; position: relative; }
        .kpi-card.highlight { border-color: var(--primary); border-width: 2px; }
        .kpi-label { font-size: 12px; font-weight: 500; color: var(--gray-500); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
        .kpi-value { font-size: 36px; font-weight: 700; color: var(--gray-900); line-height: 1; margin-bottom: 8px; }
        .kpi-card.highlight .kpi-value { color: var(--primary); }
        .kpi-change { font-size: 13px; font-weight: 500; display: flex; align-items: center; gap: 4px; }
        .kpi-change.positive { color: var(--success); }
        .kpi-change.negative { color: var(--danger); }
        .kpi-change.neutral { color: var(--gray-400); }
        .kpi-subtitle { font-size: 12px; color: var(--gray-500); margin-top: 4px; }
        .performance-badge { position: absolute; top: 16px; right: 16px; padding: 4px 10px; border-radius: 4px; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
        .performance-badge.excellent { background: #D1FAE5; color: #065F46; }
        .performance-badge.good { background: #DBEAFE; color: #1E40AF; }
        .table-section { margin-bottom: 48px; }
        .data-table { width: 100%; border-collapse: collapse; background: white; border: 1px solid var(--gray-200); border-radius: 8px; overflow: hidden; }
        .data-table thead { background: var(--gray-50); }
        .data-table th { padding: 14px 16px; text-align: left; font-size: 11px; font-weight: 600; color: var(--gray-600); text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid var(--gray-200); }
        .data-table th:not(:first-child) { text-align: right; }
        .data-table td { padding: 16px; border-bottom: 1px solid var(--gray-100); font-size: 14px; }
        .data-table td:not(:first-child) { text-align: right; font-variant-numeric: tabular-nums; }
        .data-table tbody tr:hover { background: var(--gray-50); }
        .data-table tbody tr:last-child td { border-bottom: none; }
        .metric-name { font-weight: 500; color: var(--gray-800); }
        .metric-value { font-weight: 600; color: var(--gray-900); }
        .change-positive { color: var(--success); font-weight: 500; }
        .change-negative { color: var(--danger); font-weight: 500; }
        .insights-section { margin-bottom: 48px; }
        .insight-card { background: white; border: 1px solid var(--gray-200); border-radius: 8px; padding: 24px; margin-bottom: 16px; }
        .insight-card:last-child { margin-bottom: 0; }
        .insight-header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
        .insight-icon { width: 32px; height: 32px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 16px; }
        .insight-icon.success { background: #D1FAE5; }
        .insight-icon.info { background: #DBEAFE; }
        .insight-icon.warning { background: #FEF3C7; }
        .insight-title { font-size: 14px; font-weight: 600; color: var(--gray-800); }
        .insight-text { font-size: 14px; color: var(--gray-600); line-height: 1.6; }
        .report-footer { border-top: 1px solid var(--gray-200); padding-top: 24px; margin-top: 48px; display: flex; justify-content: space-between; align-items: center; }
        .footer-brand { font-size: 12px; color: var(--gray-500); }
        .footer-brand a { color: var(--primary); text-decoration: none; font-weight: 500; }
        .footer-meta { font-size: 11px; color: var(--gray-400); }
        @media (max-width: 768px) { .report-container { padding: 20px; } .kpi-grid { grid-template-columns: repeat(2, 1fr); gap: 16px; } .kpi-value { font-size: 28px; } .header-top { flex-direction: column; gap: 8px; } }
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
                    <div class="kpi-value">&mdash;</div>
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
</html>`;
}

function getIndexTemplate() {
  return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Client Reports | Robert Hebert Media</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #0066CC;
            --success: #059669;
            --gray-50: #F9FAFB;
            --gray-100: #F3F4F6;
            --gray-200: #E5E7EB;
            --gray-400: #9CA3AF;
            --gray-500: #6B7280;
            --gray-600: #4B5563;
            --gray-700: #374151;
            --gray-800: #1F2937;
            --gray-900: #111827;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #fff;
            color: var(--gray-800);
            line-height: 1.5;
            font-size: 14px;
        }
        .page-container { max-width: 900px; margin: 0 auto; padding: 40px; }
        .page-header { border-bottom: 3px solid var(--primary); padding-bottom: 24px; margin-bottom: 40px; }
        .header-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; }
        .brand { font-size: 12px; font-weight: 600; color: var(--gray-500); text-transform: uppercase; letter-spacing: 1.5px; }
        .header-meta { font-size: 12px; color: var(--gray-500); text-align: right; }
        .page-title { font-size: 32px; font-weight: 700; color: var(--gray-900); margin-bottom: 4px; }
        .page-subtitle { font-size: 18px; font-weight: 400; color: var(--gray-600); }
        .client-section { margin-bottom: 32px; }
        .section-header { font-size: 11px; font-weight: 600; color: var(--gray-500); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 1px solid var(--gray-200); display: flex; align-items: center; gap: 12px; }
        .client-badge { background: var(--primary); color: white; padding: 3px 10px; border-radius: 4px; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
        .report-card { background: white; border: 1px solid var(--gray-200); border-radius: 8px; padding: 20px 24px; margin-bottom: 12px; transition: all 0.2s ease; position: relative; }
        .report-card:hover { border-color: var(--primary); box-shadow: 0 4px 12px rgba(0, 102, 204, 0.1); transform: translateY(-2px); }
        .report-card:last-child { margin-bottom: 0; }
        .report-card a { text-decoration: none; color: inherit; display: flex; justify-content: space-between; align-items: center; }
        .report-info { flex: 1; }
        .report-title { font-size: 15px; font-weight: 600; color: var(--gray-900); margin-bottom: 4px; display: flex; align-items: center; gap: 10px; }
        .report-date { font-size: 13px; color: var(--gray-500); }
        .badge-new { display: inline-block; background: #D1FAE5; color: #065F46; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
        .arrow-icon { color: var(--gray-400); font-size: 18px; transition: transform 0.2s ease, color 0.2s ease; }
        .report-card:hover .arrow-icon { color: var(--primary); transform: translateX(4px); }
        .page-footer { border-top: 1px solid var(--gray-200); padding-top: 24px; margin-top: 48px; display: flex; justify-content: space-between; align-items: center; }
        .footer-brand { font-size: 12px; color: var(--gray-500); }
        .footer-brand a { color: var(--primary); text-decoration: none; font-weight: 500; }
        .footer-brand a:hover { text-decoration: underline; }
        .footer-meta { font-size: 11px; color: var(--gray-400); }
        @media (max-width: 768px) { .page-container { padding: 20px; } .header-top { flex-direction: column; gap: 8px; } .page-title { font-size: 24px; } .report-card a { flex-direction: column; align-items: flex-start; gap: 8px; } .arrow-icon { display: none; } }
    </style>
</head>
<body>
    <div class="page-container">
        <header class="page-header">
            <div class="header-top">
                <div class="brand">Robert Hebert Media</div>
                <div class="header-meta">Client Reports Portal</div>
            </div>
            <h1 class="page-title">Performance Reports</h1>
            <p class="page-subtitle">Weekly Google Ads Analytics</p>
        </header>

        {client_sections}

        <footer class="page-footer">
            <div class="footer-brand">Powered by <a href="https://roberthebertmedia.com">Robert Hebert Media</a></div>
            <div class="footer-meta">Confidential Client Portal</div>
        </footer>
    </div>
</body>
</html>`;
}

// ============================================
// MENU FUNCTIONS
// ============================================

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('RHM Reports')
    .addItem('Generate Reports Now', 'generateWeeklyReports')
    .addItem('Test Email', 'testEmail')
    .addToUi();
}

function testEmail() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const config = getConfig(ss);

  GmailApp.sendEmail(config.email_bcc, 'Test - RHM Report System', 'This is a test email from the RHM Report Generator.', {
    name: 'RHM Report System'
  });

  SpreadsheetApp.getUi().alert('Test email sent to ' + config.email_bcc);
}
