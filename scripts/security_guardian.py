#!/usr/bin/env python3
"""
AI Learning Security Guardian
- File integrity monitoring (AIDE)
- Log anomaly detection
- Rootkit check
- Network anomaly
- Auto-remediation
"""

import os
import re
import json
import hashlib
import subprocess
import time
from datetime import datetime
from pathlib import Path

CONFIG = {
    "check_interval": 60,  # seconds
    "alert_threshold": 3,
    "file_watch_paths": [
        "/home/dju/mojAiProjekat/New folder/backend/app",
        "/home/dju/mojAiProjekat/New folder/docker",
    ],
    "suspicious_patterns": [
        r"nc -l",  # Reverse shell
        r"bash -i.*&",  # Backdoor
        r"wget.*\|.*bash",  # Worm
        r"curl.*\|.*sh",  # Dropper
        r"\/dev\/tcp",  # Shell download
        r"0x",  # Hex encoded
    ],
    "max_failed_auth": 5,
    "alert_webhook": os.getenv("ALERT_WEBHOOK", ""),
}


class SecurityGuardian:
    def __init__(self):
        self.baseline = {}
        self.alerts = []
        self.load_baseline()

    def load_baseline(self):
        """Load or create file hash baseline"""
        baseline_file = Path("/var/lib/ai-security/baseline.json")
        if baseline_file.exists():
            self.baseline = json.loads(baseline_file.read_text())
        else:
            self.create_baseline()

    def create_baseline(self):
        """Create new baseline"""
        for path in CONFIG["file_watch_paths"]:
            for f in Path(path).rglob("*"):
                if f.is_file():
                    try:
                        self.baseline[str(f)] = self.hash_file(f)
                    except:
                        pass
        Path("/var/lib/ai-security/baseline.json").write_text(json.dumps(self.baseline))

    def hash_file(self, path):
        """SHA256 hash of file"""
        h = hashlib.sha256()
        h.update(path.read_bytes())
        return h.hexdigest()[:16]

    def check_file_integrity(self):
        """Check for modified files"""
        violations = []
        for path in CONFIG["file_watch_paths"]:
            for f in Path(path).rglob("*"):
                if f.is_file():
                    try:
                        key = str(f)
                        current = self.hash_file(f)
                        if key in self.baseline and current != self.baseline[key]:
                            violations.append(key)
                    except:
                        pass
        return violations

    def check_logs(self, log_file="/var/log/auth.log"):
        """Scan logs for suspicious patterns"""
        if not Path(log_file).exists():
            log_file = "/var/log/syslog"
            if not Path(log_file).exists():
                return []

        suspicious = []
        content = Path(log_file).read_text().split("\n")[-100:]  # Last 100 lines

        for line in content:
            for pattern in CONFIG["suspicious_patterns"]:
                if re.search(pattern, line, re.I):
                    suspicious.append(line.strip())

        # Check failed auth
        failed_auth = sum(
            1
            for l in content
            if "Failed password" in l or "authentication failure" in l
        )
        if failed_auth > CONFIG["max_failed_auth"]:
            suspicious.append(f"High failed auth: {failed_auth}")

        return suspicious

    def check_rootkits(self):
        """Check for rootkit indicators"""
        checks = [
            (
                "hidden processes",
                "ls /proc/*/comm 2>/dev/null | cut -d/ -f3 | sort -u | wc -l",
            ),
            ("suspicious ports", "netstat -tulpn 2>/dev/null | grep LISTEN"),
            ("loaded modules", "lsmod"),
        ]

        results = {}
        for name, cmd in checks:
            try:
                results[name] = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True
                ).stdout[:200]
            except:
                results[name] = "N/A"
        return results

    def check_containers(self):
        """Check Docker security"""
        checks = []

        # Running containers without healthcheck
        result = subprocess.run(
            "docker ps --format '{{.Names}}\t{{.Status}}'",
            shell=True,
            capture_output=True,
            text=True,
        )
        for line in result.stdout.split("\n"):
            if "(unhealthy)" in line or "Exited" in line:
                checks.append(line)

        return checks

    def send_alert(self, message, severity="warning"):
        """Send alert to webhook"""
        alert = {
            "time": datetime.now().isoformat(),
            "severity": severity,
            "message": message,
        }
        self.alerts.append(alert)

        if CONFIG["alert_webhook"]:
            try:
                import requests

                requests.post(CONFIG["alert_webhook"], json=alert, timeout=5)
            except:
                pass

    def run(self):
        """Main loop"""
        print(f"🛡️ Security Guardian started")

        while True:
            issues = []

            # File integrity
            modified = self.check_file_integrity()
            if modified:
                issues.append(f"Modified files: {modified[:3]}")

            # Log analysis
            suspicious = self.check_logs()
            if suspicious:
                issues.append(f"Suspicious activity: {suspicious[:2]}")

            # Container health
            bad_containers = self.check_containers()
            if bad_containers:
                issues.append(f"Container issues: {bad_containers}")

            # Rootkit check
            rk = self.check_rootkits()
            if rk.get("suspicious ports"):
                issues.append(f"Unusual ports detected")

            # Report
            if issues:
                for issue in issues:
                    print(f"⚠️ {issue}")
                    self.send_alert(issue)
            else:
                print(f"✓ {datetime.now().strftime('%H:%M:%S')} - All clean")

            time.sleep(CONFIG["check_interval"])


if __name__ == "__main__":
    Path("/var/lib/ai-security").mkdir(parents=True, exist_ok=True)
    guardian = SecurityGuardian()
    guardian.run()
