"""Observability readiness gate plugin."""

import json
from pathlib import Path

from sdk.models import CheckResult, GateResult, GateSeverity
from sdk.plugin import GateContext, GatePlugin


class ObservabilityGate(GatePlugin):
    """Gate for observability readiness validation."""
    
    @property
    def gate_id(self) -> str:
        return "obs"
    
    @property
    def severity(self) -> GateSeverity:
        return GateSeverity.CRITICAL
    
    @property
    def expected_artifacts(self) -> list[str]:
        return [
            "obs/report.json",
            "obs/summary.md",
            "obs/dashboard-export.json",
        ]
    
    def execute(self, ctx: GateContext) -> list[CheckResult]:
        """Run observability readiness checks."""
        results = []
        
        # Check 1: Health check endpoints exist
        health = self._check_health_endpoints(ctx.workspace_dir)
        results.append(CheckResult(
            name="health_endpoints",
            result=GateResult.PASS if health["coverage"] >= 0.8 else GateResult.FAIL,
            value=health.get("coverage", 0.0),
            threshold=0.8,
            comparator="gte",
            message=f"Health endpoint coverage: {health.get('coverage', 0):.0%}",
        ))
        
        # Check 2: OpenTelemetry instrumentation
        otel = self._check_opentelemetry(ctx.workspace_dir)
        results.append(CheckResult(
            name="opentelemetry",
            result=GateResult.PASS if otel["instrumented"] else GateResult.FAIL,
            value=otel.get("instrumentation_score", 0.0),
            threshold=0.7,
            comparator="gte",
            message=f"OTel instrumentation: {otel.get('instrumentation_score', 0):.0%}",
        ))
        
        # Check 3: Prometheus metrics defined
        metrics = self._check_prometheus_metrics(ctx.workspace_dir)
        results.append(CheckResult(
            name="prometheus_metrics",
            result=GateResult.PASS if metrics["has_metrics"] else GateResult.FAIL,
            value=metrics.get("metric_count", 0),
            threshold=5,
            comparator="gte",
            message=f"Prometheus metrics: {metrics.get('metric_count', 0)}",
        ))
        
        # Check 4: Grafana dashboards exist
        dashboards = self._check_grafana_dashboards(ctx.workspace_dir)
        results.append(CheckResult(
            name="grafana_dashboards",
            result=GateResult.PASS if dashboards["has_dashboards"] else GateResult.FAIL,
            value=dashboards.get("dashboard_count", 0),
            threshold=3,
            comparator="gte",
            message=f"Grafana dashboards: {dashboards.get('dashboard_count', 0)}",
        ))
        
        # Check 5: Alerting rules defined
        alerts = self._check_alerting_rules(ctx.workspace_dir)
        results.append(CheckResult(
            name="alerting_rules",
            result=GateResult.PASS if alerts["has_alerts"] else GateResult.FAIL,
            value=alerts.get("alert_count", 0),
            threshold=5,
            comparator="gte",
            message=f"Alerting rules: {alerts.get('alert_count', 0)}",
        ))
        
        return results
    
    def _check_health_endpoints(self, workspace: Path) -> dict:
        """Check health endpoint coverage."""
        # Look for health check implementations
        health_files = [
            workspace / "value-fabric/layer1-ingestion/src/health.py",
            workspace / "value-fabric/layer2-extraction/src/health.py",
            workspace / "value-fabric/layer3-knowledge/src/api/health.py",
            workspace / "value-fabric/layer4-agents/src/api/routes/health.py",
        ]
        
        found = sum(1 for f in health_files if f.exists())
        coverage = found / len(health_files)
        
        return {
            "coverage": coverage,
            "found_count": found,
            "total_count": len(health_files),
        }
    
    def _check_opentelemetry(self, workspace: Path) -> dict:
        """Check OpenTelemetry instrumentation."""
        # Look for OTel imports and usage
        otel_patterns = [
            workspace / "shared/tracing.py",
            workspace / "shared/telemetry.py",
        ]
        
        # Also check main API files for OTel
        api_files = [
            workspace / "value-fabric/layer3-knowledge/src/api/main.py",
            workspace / "value-fabric/layer4-agents/src/api/main.py",
        ]
        
        score = 0.0
        
        # Check for tracing module
        for pattern in otel_patterns:
            if pattern.exists():
                score += 0.3
        
        # Check API files for OTel imports
        for api_file in api_files:
            if api_file.exists():
                content = api_file.read_text()
                if "opentelemetry" in content.lower() or "otel" in content.lower():
                    score += 0.2
        
        return {
            "instrumented": score >= 0.7,
            "instrumentation_score": min(score, 1.0),
        }
    
    def _check_prometheus_metrics(self, workspace: Path) -> dict:
        """Check Prometheus metrics definitions."""
        # Look for metrics in monitoring configs
        prom_config = workspace / "monitoring/prometheus/prometheus.yml"
        
        metric_count = 0
        
        # Check for recording rules
        rules_file = workspace / "monitoring/prometheus/recording-rules.yml"
        if rules_file.exists():
            content = rules_file.read_text()
            metric_count += content.count("record:")
        
        # Check for Redis rules
        redis_rules = workspace / "monitoring/prometheus/redis-recording-rules.yml"
        if redis_rules.exists():
            content = redis_rules.read_text()
            metric_count += content.count("record:")
        
        return {
            "has_metrics": metric_count >= 5,
            "metric_count": metric_count,
        }
    
    def _check_grafana_dashboards(self, workspace: Path) -> dict:
        """Check Grafana dashboards."""
        dashboard_dir = workspace / "monitoring/grafana/dashboards"
        
        if not dashboard_dir.exists():
            return {"has_dashboards": False, "dashboard_count": 0}
        
        dashboards = list(dashboard_dir.glob("*.json"))
        
        return {
            "has_dashboards": len(dashboards) >= 3,
            "dashboard_count": len(dashboards),
        }
    
    def _check_alerting_rules(self, workspace: Path) -> dict:
        """Check alerting rules."""
        alert_files = [
            workspace / "monitoring/alerting/rules.yml",
            workspace / "monitoring/alerting/rules-production.yml",
        ]
        
        alert_count = 0
        
        for alert_file in alert_files:
            if alert_file.exists():
                content = alert_file.read_text()
                alert_count += content.count("- alert:")
        
        return {
            "has_alerts": alert_count >= 5,
            "alert_count": alert_count,
        }
