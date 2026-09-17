#!/bin/bash
# Sovereign LMS: Single-Command Production Deployer
# Usage: ./deploy.sh ["Optional commit message"]
set -euo pipefail

COMMIT_MSG="${1:-Update LMS: $(date '+%Y-%m-%d %H:%M:%S')}"
FORGE_IP="187.127.154.120"

echo "🚀 === Sovereign LMS Deployer ==="

# 1. Stage, Commit & Push to GitHub
if [ -n "$(git status --porcelain)" ]; then
    echo "📦 Staging and committing changes: '${COMMIT_MSG}'..."
    git add .
    git commit -m "${COMMIT_MSG}"
else
    echo "ℹ️ Working tree clean. Deploying latest commits..."
fi

echo "�� Pushing to GitHub (origin/main)..."
git push origin main

# 2. Trigger Sovereign Forge GitOps Apply
echo "🚢 Triggering production deployment on Forge (${FORGE_IP})..."
ssh -o StrictHostKeyChecking=accept-new "root@${FORGE_IP}" "forge-ctl apply-app lms"

echo ""
echo "🎉 Deployment Complete!"
echo "🌐 Live URL: https://learn.loansemporium.com"
echo "==============================================="
