#!/usr/bin/env python3
"""
OWASP ZAP Full Scan Integration

Comprehensive web application penetration testing using ZAP API.
Runs full active scan with all rules enabled for maximum coverage.

Usage:
    python zap-full-scan.py --target http://localhost:8000 --output zap-results.sarif
"""

import argparse
import json
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ZAPScanner:
    """OWASP ZAP scanner wrapper."""

    def __init__(self, zap_url: str = "http://localhost:8080", api_key: str = None):
        self.zap_url = zap_url
        self.api_key = api_key
        self.session = requests.Session()
        
    def wait_for_zap(self, timeout: int = 60) -> bool:
        """Wait for ZAP to be ready."""
        start = time.time()
        while time.time() - start < timeout:
            try:
                response = self.session.get(f"{self.zap_url}/JSON/core/view/version/")
                if response.status_code == 200:
                    logger.info("ZAP is ready")
                    return True
            except requests.exceptions.ConnectionError:
                pass
            time.sleep(1)
        return False
    
    def start_spider(self, target: str, max_children: int = 100) -> str:
        """Start spider scan."""
        params = {
            "url": target,
            "maxChildren": max_children,
        }
        if self.api_key:
            params["apikey"] = self.api_key
            
        response = self.session.get(
            f"{self.zap_url}/JSON/spider/action/scan/",
            params=params,
            timeout=30
        )
        response.raise_for_status()
        return response.json().get("scan")
    
    def wait_for_spider(self, scan_id: str, timeout: int = 300) -> bool:
        """Wait for spider to complete."""
        start = time.time()
        while time.time() - start < timeout:
            params = {"scanId": scan_id}
            if self.api_key:
                params["apikey"] = self.api_key
                
            response = self.session.get(
                f"{self.zap_url}/JSON/spider/view/status/",
                params=params,
                timeout=30
            )
            progress = int(response.json().get("status", "0"))
            logger.info(f"Spider progress: {progress}%")
            
            if progress >= 100:
                return True
            time.sleep(2)
        return False
    
    def start_active_scan(self, target: str, scan_policy: str = None) -> str:
        """Start active scan."""
        params = {
            "url": target,
            "recurse": "true",
            "inScopeOnly": "false",
            "scanPolicyName": scan_policy or "Default Policy",
        }
        if self.api_key:
            params["apikey"] = self.api_key
            
        response = self.session.get(
            f"{self.zap_url}/JSON/ascan/action/scan/",
            params=params,
            timeout=30
        )
        response.raise_for_status()
        return response.json().get("scan")
    
    def wait_for_active_scan(self, scan_id: str, timeout: int = 600) -> bool:
        """Wait for active scan to complete."""
        start = time.time()
        while time.time() - start < timeout:
            params = {"scanId": scan_id}
            if self.api_key:
                params["apikey"] = self.api_key
                
            response = self.session.get(
                f"{self.zap_url}/JSON/ascan/view/status/",
                params=params,
                timeout=30
            )
            progress = int(response.json().get("status", "0"))
            logger.info(f"Active scan progress: {progress}%")
            
            if progress >= 100:
                return True
            time.sleep(5)
        return False
    
    def get_alerts(self, base_url: str = None) -> list[dict[str, Any]]:
        """Get all alerts from scan."""
        params = {}
        if base_url:
            params["baseurl"] = base_url
        if self.api_key:
            params["apikey"] = self.api_key
            
        response = self.session.get(
            f"{self.zap_url}/JSON/core/view/alerts/",
            params=params,
            timeout=60
        )
        response.raise_for_status()
        return response.json().get("alerts", [])
    
    def export_report(self, report_type: str = "sarif", output_path: str = None) -> str:
        """Export scan report."""
        if report_type == "sarif":
            endpoint = "/OTHER/core/other/sarif/"
        elif report_type == "json":
            endpoint = "/OTHER/core/other/jsonreport/"
        elif report_type == "html":
            endpoint = "/OTHER/core/other/htmlreport/"
        else:
            raise ValueError(f"Unsupported report type: {report_type}")
        
        params = {}
        if self.api_key:
            params["apikey"] = self.api_key
            
        response = self.session.get(
            f"{self.zap_url}{endpoint}",
            params=params,
            timeout=60
        )
        response.raise_for_status()
        
        if output_path:
            Path(output_path).write_text(response.text)
            return output_path
        return response.text
    
    def generate_sarif(self, alerts: list, tool_name: str = "OWASP ZAP") -> dict:
        """Convert ZAP alerts to SARIF format."""
        sarif = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [{
                "tool": {
                    "driver": {
                        "name": tool_name,
                        "informationUri": "https://www.zaproxy.org/",
                        "rules": []
                    }
                },
                "results": []
            }]
        }
        
        rule_ids = set()
        for alert in alerts:
            rule_id = alert.get("pluginId", "unknown")
            if rule_id not in rule_ids:
                rule_ids.add(rule_id)
                sarif["runs"][0]["tool"]["driver"]["rules"].append({
                    "id": rule_id,
                    "name": alert.get("name", "Unknown"),
                    "shortDescription": {
                        "text": alert.get("description", "No description")
                    },
                    "helpUri": alert.get("reference", ""),
                    "properties": {
                        "risk": alert.get("risk", "Informational"),
                        "confidence": alert.get("confidence", "Low")
                    }
                })
            
            # Map ZAP risk to SARIF level
            risk = alert.get("risk", "Informational")
            level = {
                "High": "error",
                "Medium": "warning",
                "Low": "note",
                "Informational": "none"
            }.get(risk, "none")
            
            sarif["runs"][0]["results"].append({
                "ruleId": rule_id,
                "level": level,
                "message": {
                    "text": alert.get("description", "")
                },
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": alert.get("url", "")
                        }
                    }
                }]
            })
        
        return sarif


def run_docker_zap(target: str, output_dir: str, timeout: int = 600) -> int:
    """Run ZAP in Docker container."""
    logger.info(f"Starting ZAP Docker scan against {target}")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        "docker", "run",
        "--rm",
        "-v", f"{output_path.absolute()}:/zap/wrk/:rw",
        "-t", "ghcr.io/zaproxy/zaproxy:stable",
        "zap-full-scan.py",
        "-t", target,
        "-r", "zap-report.html",
        "-J", "zap-report.json",
        "-w", "zap-report.md",
        "-x", "zap-report.xml",
        "-f", "openapi"  # Assume API endpoints
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        logger.info(f"ZAP scan completed with exit code: {result.returncode}")
        return result.returncode
    except subprocess.TimeoutExpired:
        logger.error(f"ZAP scan timed out after {timeout}s")
        return 1
    except FileNotFoundError:
        logger.error("Docker not found. Please install Docker.")
        return 1


def main():
    parser = argparse.ArgumentParser(description="OWASP ZAP Full Scan")
    parser.add_argument("--target", required=True, help="Target URL to scan")
    parser.add_argument("--output", default="zap-results.sarif", help="Output SARIF file")
    parser.add_argument("--zap-url", default="http://localhost:8080", help="ZAP API URL")
    parser.add_argument("--api-key", help="ZAP API key")
    parser.add_argument("--use-docker", action="store_true", help="Use Docker ZAP")
    parser.add_argument("--timeout", type=int, default=600, help="Scan timeout in seconds")
    
    args = parser.parse_args()
    
    if args.use_docker:
        output_dir = Path(args.output).parent
        return run_docker_zap(args.target, str(output_dir), args.timeout)
    
    scanner = ZAPScanner(args.zap_url, args.api_key)
    
    # Wait for ZAP
    if not scanner.wait_for_zap():
        logger.error("ZAP did not start within timeout")
        return 1
    
    # Spider scan
    logger.info("Starting spider scan...")
    spider_id = scanner.start_spider(args.target)
    if not scanner.wait_for_spider(spider_id):
        logger.error("Spider scan timed out")
        return 1
    
    # Active scan
    logger.info("Starting active scan...")
    ascan_id = scanner.start_active_scan(args.target)
    if not scanner.wait_for_active_scan(ascan_id, args.timeout):
        logger.error("Active scan timed out")
        return 1
    
    # Get alerts and generate SARIF
    logger.info("Generating report...")
    alerts = scanner.get_alerts(args.target)
    sarif = scanner.generate_sarif(alerts)
    
    # Write SARIF output
    with open(args.output, "w") as f:
        json.dump(sarif, f, indent=2)
    
    logger.info(f"Scan complete. Found {len(alerts)} alerts.")
    logger.info(f"SARIF report written to: {args.output}")
    
    # Return non-zero if high risk alerts found
    high_risk = [a for a in alerts if a.get("risk") == "High"]
    if high_risk:
        logger.error(f"Found {len(high_risk)} HIGH risk vulnerabilities!")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
