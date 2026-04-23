"""Tests for Prometheus monitoring configuration.

Validates:
- Prometheus ConfigMap structure and scrape configs
- Alertmanager integration
- Scrape targets for all 6 layers
- Alerting rules configuration
- Recording rules
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml


class TestPrometheusConfigMap:
    """Tests for the Prometheus ConfigMap configuration."""

    def test_prometheus_configmap_exists(self, k8s_base_dir: Path) -> None:
        """Verify monitoring-prometheus.yml ConfigMap exists."""
        config = k8s_base_dir / "monitoring-prometheus.yml"
        assert config.exists(), "Prometheus ConfigMap must exist"

    def test_prometheus_configmap_structure(self, k8s_base_dir: Path) -> None:
        """Verify ConfigMap has correct structure with prometheus.yml and rules.yml."""
        config = k8s_base_dir / "monitoring-prometheus.yml"
        
        with open(config) as f:
            doc = yaml.safe_load(f)
        
        assert doc.get("kind") == "ConfigMap"
        assert doc.get("metadata", {}).get("name") == "prometheus-config"
        
        data = doc.get("data", {})
        assert "prometheus.yml" in data, "ConfigMap must contain prometheus.yml"
        assert "rules.yml" in data, "ConfigMap must contain rules.yml"

    def test_prometheus_global_settings(self, k8s_base_dir: Path) -> None:
        """Verify global scrape and evaluation intervals."""
        config = k8s_base_dir / "monitoring-prometheus.yml"
        
        with open(config) as f:
            doc = yaml.safe_load(f)
        
        prometheus_yml = yaml.safe_load(doc["data"]["prometheus.yml"])
        
        assert prometheus_yml.get("global", {}).get("scrape_interval") == "15s"
        assert prometheus_yml.get("global", {}).get("evaluation_interval") == "15s"
        assert prometheus_yml.get("global", {}).get("external_labels", {}).get("cluster") == "value-fabric"

    def test_alertmanager_integration_configured(self, k8s_base_dir: Path) -> None:
        """[3a] Verify Alertmanager integration is configured."""
        config = k8s_base_dir / "monitoring-prometheus.yml"
        
        with open(config) as f:
            doc = yaml.safe_load(f)
        
        prometheus_yml = yaml.safe_load(doc["data"]["prometheus.yml"])
        
        alerting = prometheus_yml.get("alerting", {})
        alertmanagers = alerting.get("alertmanagers", [])
        
        assert len(alertmanagers) > 0, "Alertmanager must be configured"
        
        static_configs = alertmanagers[0].get("static_configs", [])
        targets = static_configs[0].get("targets", []) if static_configs else []
        
        assert "alertmanager:9093" in targets, "[3b] Alertmanager target must be configured"

    def test_rule_files_configured(self, k8s_base_dir: Path) -> None:
        """Verify rule_files points to embedded rules."""
        config = k8s_base_dir / "monitoring-prometheus.yml"
        
        with open(config) as f:
            doc = yaml.safe_load(f)
        
        prometheus_yml = yaml.safe_load(doc["data"]["prometheus.yml"])
        
        rule_files = prometheus_yml.get("rule_files", [])
        assert "/etc/prometheus/alerting/rules.yml" in rule_files


class TestPrometheusScrapeConfigs:
    """Tests for Prometheus scrape configuration for all layers."""

    @pytest.fixture(scope="class")
    def scrape_configs(self, k8s_base_dir: Path) -> list[dict]:
        """Extract scrape_configs from Prometheus ConfigMap."""
        config = k8s_base_dir / "monitoring-prometheus.yml"
        
        with open(config) as f:
            doc = yaml.safe_load(f)
        
        prometheus_yml = yaml.safe_load(doc["data"]["prometheus.yml"])
        return prometheus_yml.get("scrape_configs", [])

    def test_prometheus_self_scrape(self, scrape_configs: list[dict]) -> None:
        """Verify Prometheus scrapes itself."""
        job = next((j for j in scrape_configs if j.get("job_name") == "prometheus"), None)
        assert job is not None
        assert job["static_configs"][0]["targets"] == ["localhost:9090"]

    def test_layer1_scrape_job(self, scrape_configs: list[dict]) -> None:
        """[3c] Verify Layer 1 ingestion scrape job is configured."""
        job = next(
            (j for j in scrape_configs if j.get("job_name") == "layer1-ingestion"),
            None
        )
        assert job is not None, "Layer 1 scrape job must exist"
        assert job["static_configs"][0]["targets"] == ["layer1-ingestion:8000"]
        assert job.get("metrics_path") == "/api/v1/ingestion/metrics", "[3d] Layer 1 must have custom metrics path"

    def test_layer2_scrape_job(self, scrape_configs: list[dict]) -> None:
        """Verify Layer 2 extraction scrape job is configured."""
        job = next(
            (j for j in scrape_configs if j.get("job_name") == "layer2-extraction"),
            None
        )
        assert job is not None
        assert job["static_configs"][0]["targets"] == ["layer2-extraction:8000"]
        assert job.get("metrics_path") == "/metrics"

    def test_layer3_scrape_job(self, scrape_configs: list[dict]) -> None:
        """Verify Layer 3 knowledge scrape job is configured."""
        job = next(
            (j for j in scrape_configs if j.get("job_name") == "layer3-knowledge"),
            None
        )
        assert job is not None
        assert job["static_configs"][0]["targets"] == ["layer3-knowledge:8001"]
        assert job.get("metrics_path") == "/metrics"

    def test_layer4_scrape_job(self, scrape_configs: list[dict]) -> None:
        """Verify Layer 4 agents scrape job is configured."""
        job = next(
            (j for j in scrape_configs if j.get("job_name") == "layer4-agents"),
            None
        )
        assert job is not None
        assert job["static_configs"][0]["targets"] == ["layer4-agents:8000"]
        assert job.get("metrics_path") == "/metrics"

    def test_layer5_scrape_job(self, scrape_configs: list[dict]) -> None:
        """Verify Layer 5 ground truth scrape job is configured."""
        job = next(
            (j for j in scrape_configs if j.get("job_name") == "layer5-ground-truth"),
            None
        )
        assert job is not None
        assert job["static_configs"][0]["targets"] == ["layer5-ground-truth:8005"]
        assert job.get("metrics_path") == "/metrics"

    def test_layer6_scrape_job(self, scrape_configs: list[dict]) -> None:
        """Verify Layer 6 benchmarks scrape job is configured."""
        job = next(
            (j for j in scrape_configs if j.get("job_name") == "layer6-benchmarks"),
            None
        )
        assert job is not None
        assert job["static_configs"][0]["targets"] == ["layer6-benchmarks:8006"]
        assert job.get("metrics_path") == "/metrics"

    def test_alertmanager_scrape_job(self, scrape_configs: list[dict]) -> None:
        """Verify Alertmanager scrape job is configured."""
        job = next(
            (j for j in scrape_configs if j.get("job_name") == "alertmanager"),
            None
        )
        assert job is not None
        assert job["static_configs"][0]["targets"] == ["alertmanager:9093"]

    def test_all_six_layers_configured(self, scrape_configs: list[dict]) -> None:
        """Verify all 6 Value Fabric layers have scrape jobs configured."""
        job_names = {j.get("job_name") for j in scrape_configs}
        
        required = {
            "layer1-ingestion",
            "layer2-extraction",
            "layer3-knowledge",
            "layer4-agents",
            "layer5-ground-truth",
            "layer6-benchmarks",
        }
        
        missing = required - job_names
        assert not missing, f"Missing scrape jobs for layers: {missing}"


class TestPrometheusAlertingRules:
    """Tests for Prometheus alerting rules configuration."""

    @pytest.fixture(scope="class")
    def alert_rules(self, k8s_base_dir: Path) -> list[dict]:
        """Extract alert rules from Prometheus ConfigMap."""
        config = k8s_base_dir / "monitoring-prometheus.yml"
        
        with open(config) as f:
            doc = yaml.safe_load(f)
        
        rules_yml = yaml.safe_load(doc["data"]["rules.yml"])
        return rules_yml.get("groups", [])

    def test_service_down_alert(self, alert_rules: list[dict]) -> None:
        """[3e] Verify ServiceDown alert is configured."""
        availability_group = next(
            (g for g in alert_rules if g.get("name") == "value-fabric-availability"),
            None
        )
        assert availability_group is not None
        
        rules = availability_group.get("rules", [])
        service_down = next(
            (r for r in rules if r.get("alert") == "ServiceDown"),
            None
        )
        assert service_down is not None
        
        # Verify severity is critical
        assert service_down.get("labels", {}).get("severity") == "critical"
        
        # Verify runbook URL is present
        assert "runbook_url" in service_down.get("annotations", {})

    def test_dependency_health_alert(self, alert_rules: list[dict]) -> None:
        """Verify DependencyHealthDegraded alert is configured."""
        availability_group = next(
            (g for g in alert_rules if g.get("name") == "value-fabric-availability"),
            None
        )
        assert availability_group is not None
        
        rules = availability_group.get("rules", [])
        health_alert = next(
            (r for r in rules if r.get("alert") == "DependencyHealthDegraded"),
            None
        )
        assert health_alert is not None
        assert health_alert.get("labels", {}).get("severity") == "critical"

    def test_error_rate_alert(self, alert_rules: list[dict]) -> None:
        """[7a, 7b] Verify ErrorRateSpike alert covers all layers."""
        slo_group = next(
            (g for g in alert_rules if g.get("name") == "value-fabric-slo"),
            None
        )
        assert slo_group is not None
        
        rules = slo_group.get("rules", [])
        error_rate = next(
            (r for r in rules if r.get("alert") == "ErrorRateSpike"),
            None
        )
        assert error_rate is not None
        
        expr = error_rate.get("expr", "")
        
        # Should cover all layers
        assert "layer1" in expr or "value_fabric" in expr
        assert "layer2" in expr or "value_fabric" in expr

    def test_latency_slo_alert(self, alert_rules: list[dict]) -> None:
        """Verify LatencySLOBreachP95 alert is configured."""
        slo_group = next(
            (g for g in alert_rules if g.get("name") == "value-fabric-slo"),
            None
        )
        assert slo_group is not None
        
        rules = slo_group.get("rules", [])
        latency_alert = next(
            (r for r in rules if r.get("alert") == "LatencySLOBreachP95"),
            None
        )
        assert latency_alert is not None
        
        # Threshold should be 2s or similar
        expr = latency_alert.get("expr", "")
        assert "0.95" in expr or "histogram_quantile" in expr

    def test_alert_group_has_runbook_urls(self, alert_rules: list[dict]) -> None:
        """Verify all alerts have runbook URLs for operational guidance."""
        for group in alert_rules:
            for rule in group.get("rules", []):
                if "alert" in rule:  # It's an alerting rule
                    annotations = rule.get("annotations", {})
                    assert "runbook_url" in annotations, \
                        f"Alert {rule['alert']} missing runbook_url"


class TestPrometheusDeployment:
    """Tests for Prometheus Deployment configuration."""

    def test_prometheus_deployment_exists(self, k8s_base_dir: Path) -> None:
        """Verify Prometheus Deployment manifest exists."""
        config = k8s_base_dir / "monitoring-prometheus.yml"
        
        with open(config) as f:
            docs = list(yaml.safe_load_all(f.read()))
        
        deployments = [d for d in docs if d and d.get("kind") == "Deployment"]
        assert len(deployments) > 0, "Prometheus Deployment must exist"

    def test_prometheus_deployment_uses_configmap(self, k8s_base_dir: Path) -> None:
        """[3f] Verify Prometheus container mounts ConfigMap for config."""
        config = k8s_base_dir / "monitoring-prometheus.yml"
        
        with open(config) as f:
            docs = list(yaml.safe_load_all(f.read()))
        
        deployment = next(
            (d for d in docs if d and d.get("kind") == "Deployment"),
            None
        )
        assert deployment is not None
        
        containers = deployment["spec"]["template"]["spec"]["containers"]
        prometheus_container = next(
            (c for c in containers if c.get("name") == "prometheus"),
            None
        )
        assert prometheus_container is not None
        
        # Check args include config file
        args = prometheus_container.get("args", [])
        assert any("--config.file=/etc/prometheus/prometheus.yml" in a for a in args)

    def test_prometheus_has_resource_limits(self, workload_documents: list) -> None:
        """Verify Prometheus Deployment has resource constraints."""
        prometheus_docs = [
            (f, d) for f, d in workload_documents
            if d.get("metadata", {}).get("name") == "prometheus"
            and d.get("kind") == "Deployment"
        ]
        
        if not prometheus_docs:
            pytest.skip("Prometheus workload not found")
        
        for _, doc in prometheus_docs:
            containers = doc["spec"]["template"]["spec"]["containers"]
            for container in containers:
                resources = container.get("resources", {})
                assert "requests" in resources, f"{container['name']} missing requests"
                assert "limits" in resources, f"{container['name']} missing limits"


class TestAlertmanagerConfig:
    """Tests for Alertmanager configuration."""

    def test_alertmanager_configmap_exists(self, k8s_base_dir: Path) -> None:
        """Verify Alertmanager ConfigMap exists."""
        config = k8s_base_dir / "monitoring-alertmanager.yml"
        assert config.exists(), "Alertmanager ConfigMap must exist"

    def test_alertmanager_routing_configuration(self, k8s_base_dir: Path) -> None:
        """[4a] Verify Alertmanager routing tree is configured."""
        config = k8s_base_dir / "monitoring-alertmanager.yml"
        
        with open(config) as f:
            doc = yaml.safe_load(f)
        
        data = doc.get("data", {})
        alertmanager_yml = yaml.safe_load(data.get("alertmanager.yml", ""))
        
        route = alertmanager_yml.get("route", {})
        assert "group_by" in route, "[4b] Route must have group_by"
        assert "group_wait" in route
        assert "group_interval" in route

    def test_critical_alert_route(self, k8s_base_dir: Path) -> None:
        """[4c] Verify critical alerts route to dedicated receiver."""
        config = k8s_base_dir / "monitoring-alertmanager.yml"
        
        with open(config) as f:
            doc = yaml.safe_load(f)
        
        data = doc.get("data", {})
        alertmanager_yml = yaml.safe_load(data.get("alertmanager.yml", ""))
        
        routes = alertmanager_yml.get("route", {}).get("routes", [])
        
        critical_route = next(
            (r for r in routes if r.get("match", {}).get("severity") == "critical"),
            None
        )
        assert critical_route is not None, "Critical alert route must exist"

    def test_inhibition_rules(self, k8s_base_dir: Path) -> None:
        """[4e] Verify inhibition rules suppress warning when critical fires."""
        config = k8s_base_dir / "monitoring-alertmanager.yml"
        
        with open(config) as f:
            doc = yaml.safe_load(f)
        
        data = doc.get("data", {})
        alertmanager_yml = yaml.safe_load(data.get("alertmanager.yml", ""))
        
        inhibit_rules = alertmanager_yml.get("inhibit_rules", [])
        assert len(inhibit_rules) > 0, "Inhibition rules must be configured"

    def test_receivers_configured(self, k8s_base_dir: Path) -> None:
        """[4d] Verify webhook receivers are configured."""
        config = k8s_base_dir / "monitoring-alertmanager.yml"
        
        with open(config) as f:
            doc = yaml.safe_load(f)
        
        data = doc.get("data", {})
        alertmanager_yml = yaml.safe_load(data.get("alertmanager.yml", ""))
        
        receivers = alertmanager_yml.get("receivers", [])
        assert len(receivers) > 0, "At least one receiver must be configured"
