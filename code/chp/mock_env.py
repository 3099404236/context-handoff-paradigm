"""Mock Remote Target Environment (e.g. Remote VPS / Cloud Service).
Simulates realistic remote operations without requiring real SSH credentials.
"""

from typing import Dict, Any, Tuple


class MockVPSEnvironment:
    """Simulates a remote Linux VPS experiencing Nginx 502 Bad Gateway due to PHP-FPM OOM."""

    def __init__(self, target_id: str = "vps-prod-01"):
        self.target_id = target_id
        # State of the remote server
        self.state = {
            "php_fpm_status": "failed_oom",
            "pm_max_children": 250,           # excessively high, causes OOM
            "nginx_status": "running_with_502",
            "syslog": [
                "kernel: [14201.21] Out of memory: Kill process 29841 (php-fpm) score 340",
                "systemd[1]: php-fpm.service: Main process exited, code=killed, status=9/KILL",
                "systemd[1]: php-fpm.service: Failed with result 'oom-kill'."
            ]
        }

    def execute(self, cmd: str) -> Tuple[int, str]:
        """Simulate command execution over SSH."""
        cmd = cmd.strip()

        if "tail" in cmd and "nginx" in cmd:
            if self.state["php_fpm_status"] == "running":
                return 0, "[notice] 1421#0: *923 upstream response time 0.02s [status: 200 OK]"
            return 1, "[error] 1421#0: *881 connect() failed (111: Connection refused) while connecting to upstream: fastcgi://127.0.0.1:9000"

        if "systemctl status php-fpm" in cmd:
            if self.state["php_fpm_status"] == "running":
                return 0, "● php-fpm.service - The PHP FastCGI Process Manager\n   Active: active (running) since Thu 2026-09-03 15:52:10 UTC"
            return 3, "● php-fpm.service - The PHP FastCGI Process Manager\n   Active: failed (Result: oom-kill) since Thu 2026-09-03 15:40:02 UTC\n   Process: 29841 ExecStart=/usr/sbin/php-fpm (code=killed, status=9/KILL)"

        if "cat" in cmd and "www.conf" in cmd or "grep" in cmd and "pm.max_children" in cmd:
            return 0, f"pm = dynamic\npm.max_children = {self.state['pm_max_children']}\npm.start_servers = 10\npm.min_spare_servers = 5\npm.max_spare_servers = 20"

        if "sed" in cmd and "pm.max_children" in cmd:
            self.state["pm_max_children"] = 50
            return 0, "Config updated: pm.max_children set to 50"

        if "systemctl restart php-fpm" in cmd or "systemctl reload nginx" in cmd:
            if self.state["pm_max_children"] <= 60:
                self.state["php_fpm_status"] = "running"
                self.state["nginx_status"] = "running_healthy"
                return 0, "Services restarted successfully. Memory footprint: 380MB / 2048MB (Stable)."
            else:
                return 1, "Job for php-fpm.service failed: Insufficient memory."

        if "curl" in cmd and "healthz" in cmd or "curl" in cmd and "localhost" in cmd:
            if self.state["nginx_status"] == "running_healthy":
                return 0, "HTTP/1.1 200 OK\nServer: nginx/1.24.0\nContent-Type: text/plain\n\nOK: Service restored."
            return 1, "HTTP/1.1 502 Bad Gateway\nServer: nginx/1.24.0\nContent-Type: text/html\n\n<html><center>502 Bad Gateway</center></html>"

        return 0, f"Executed: {cmd} (Exit Code: 0)"
