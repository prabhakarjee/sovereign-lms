#!/bin/bash
# Sovereign LMS: Single-Command Deployer
# Usage: ./deploy.sh ["Optional commit message"]
set -euo pipefail

COMMIT_MSG="${1:-Auto-deploy update: $(date '+%Y-%m-%d %H:%M:%S')}"
FORGE_IP="187.127.154.120"

echo "🚀 === Deploying Sovereign LMS to Production ==="

# 1. Check & Push to GitHub
if [ -n "$(git status --porcelain)" ]; then
    echo "📦 Staging and committing local changes: '${COMMIT_MSG}'..."
    git add .
    git commit -m "${COMMIT_MSG}"
else
    echo "ℹ️ Working tree clean. Deploying latest commits..."
fi

echo "📤 Pushing to GitHub (origin/main)..."
git push origin main

# 2. Update and Reload on Forge
echo "🚢 Pulling & reloading on Forge (${FORGE_IP})..."
ssh -o StrictHostKeyChecking=accept-new "root@${FORGE_IP}" bash -s << 'REMOTE_EOF'
set -e
cd /var/lib/forge/apps/lms/src
echo "📥 GitOps: Pulling latest changes from GitHub..."
git fetch origin main
git reset --hard origin/main

echo "🏗️ Rebuilding LMS container..."
docker compose build

echo "⚡ Restarting container..."
docker compose up -d

echo "🔄 Running migrations & staticfiles..."
docker exec lms python manage.py migrate --noinput
docker exec lms python manage.py collectstatic --noinput

echo "✅ Live verification..."
curl -ILs -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:8000
REMOTE_EOF

echo ""
echo "🎉 Deployment Complete!"
echo "🌐 Live URL: https://learn.loansemporium.com"
echo "==============================================="
