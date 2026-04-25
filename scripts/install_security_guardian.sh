#!/bin/bash
# AI Security Guardian - Setup Script

set -e

echo "🛡️ Installing AI Security Guardian..."

# Create required directories
sudo mkdir -p /var/lib/ai-security

# Install required packages
sudo apt-get update -qq
sudo apt-get install -y -qq aide auditd >/dev/null 2>&1 || true

# Make script executable
chmod +x "$(dirname "$0")/security_guardian.py"

# Install systemd service
SERVICE_FILE="$(dirname "$0")/../systemd/ai-security-guardian.service"
if [ -f "$SERVICE_FILE" ]; then
    echo "📦 Installing systemd service..."
    sudo cp "$SERVICE_FILE" /etc/systemd/systemd/
    sudo systemctl daemon-reload
    sudo systemctl enable ai-security-guardian.service
    echo "✅ Service enabled"
fi

# Setup AIDE baseline
if command -v aide &> /dev/null; then
    echo "📊 Setting up AIDE baseline..."
    sudo aide --init 2>/dev/null || true
fi

echo "
✅ Security Guardian installed!

Commands:
  Start:  sudo systemctl start ai-security-guardian
  Stop:   sudo systemctl stop ai-security-guardian
  Status: sudo systemctl status ai-security-guardian
  Logs:   journalctl -u ai-security-guardian -f

Alert webhook (optional):
  export ALERT_WEBHOOK='https://your-webhook-url'
"