#!/bin/bash
# Quick deploy script for weekly reports
# Usage: ./quick-deploy.sh "clientname-oct20-26" "Client Name" "October 20-26, 2025"

CLIENT_DIR=$1
CLIENT_NAME=$2
DATE_RANGE=$3

if [ -z "$CLIENT_DIR" ] || [ -z "$CLIENT_NAME" ] || [ -z "$DATE_RANGE" ]; then
    echo "Usage: ./quick-deploy.sh \"clientname-oct20-26\" \"Client Name\" \"October 20-26, 2025\""
    exit 1
fi

echo "📊 Deploying report for $CLIENT_NAME..."

# Commit and push
git add -A
git commit -m "Add $CLIENT_NAME report for $DATE_RANGE"
git push

echo "✅ Report deployed!"
echo "🔗 URL: https://reports.roberthebertmedia.com/$CLIENT_DIR/"
echo ""
echo "📝 Don't forget to update index.html with:"
echo "<div class=\"report-item\">"
echo "    <a href=\"/$CLIENT_DIR/\">"
echo "        <div class=\"report-title\">$CLIENT_NAME</div>"
echo "        <div class=\"report-date\">Week of $DATE_RANGE</div>"
echo "    </a>"
echo "</div>"
