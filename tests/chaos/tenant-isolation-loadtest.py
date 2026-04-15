#!/usr/bin/env python3
"""
Multi-Tenant Isolation Validation with Synthetic Workloads

Generates realistic and stress-test workloads to validate tenant isolation
across all layers. Detects data leakage, race conditions, and isolation failures.

Usage:
    python tenant-isolation-loadtest.py --mode realistic --duration 300
    python tenant-isolation-loadtest.py --mode stress --concurrent 1000
"""

import argparse
import asyncio
import json
import logging
import random
import secrets
import sys
import time
from dataclasses import dataclass
from typing import Any

import aiohttp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Tenant:
    """Represents a synthetic tenant."""
    id: str
    token: str
    api_key: str
    data_created: list[dict] = None
    
    def __post_init__(self):
        if self.data_created is None:
            self.data_created = []


@dataclass
class IsolationViolation:
    """Records an isolation violation."""
    timestamp: str
    tenant_id: str
    accessed_tenant_id: str
    endpoint: str
    description: str


class TenantIsolationValidator:
    """Validates multi-tenant isolation through synthetic workloads."""
    
    BASE_URL = "http://localhost:8000"
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or self.BASE_URL
        self.violations: list[IsolationViolation] = []
        self.tenants: list[Tenant] = []
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "violations_detected": 0
        }
    
    def generate_synthetic_tenants(self, count: int = 10) -> list[Tenant]:
        """Generate synthetic tenant identities."""
        tenants = []
        for i in range(count):
            tenant_id = f"tenant-{i:03d}-{secrets.token_hex(4)}"
            token = f"synth-token-{tenant_id}-{secrets.token_urlsafe(32)}"
            api_key = f"synth-key-{secrets.token_hex(16)}"
            tenants.append(Tenant(tenant_id, token, api_key))
        
        self.tenants = tenants
        logger.info(f"Generated {count} synthetic tenants")
        return tenants
    
    async def simulate_user_journey(
        self,
        session: aiohttp.ClientSession,
        tenant: Tenant,
        journey_type: str = "standard"
    ) -> dict[str, Any]:
        """Simulate a realistic user journey."""
        results = {
            "tenant_id": tenant.id,
            "journey_type": journey_type,
            "steps_completed": 0,
            "violations": []
        }
        
        headers = {
            "Authorization": f"Bearer {tenant.token}",
            "X-Tenant-ID": tenant.id,
            "X-API-Key": tenant.api_key
        }
        
        try:
            # Step 1: Authentication check
            async with session.get(
                f"{self.base_url}/api/v1/auth/verify",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    results["steps_completed"] += 1
                    auth_data = await resp.json()
                    # Verify tenant context is correct
                    if auth_data.get("tenant_id") != tenant.id:
                        violation = IsolationViolation(
                            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            tenant_id=tenant.id,
                            accessed_tenant_id=auth_data.get("tenant_id", "unknown"),
                            endpoint="/api/v1/auth/verify",
                            description="JWT tenant claim mismatch"
                        )
                        self.violations.append(violation)
                        results["violations"].append(violation)
            
            # Step 2: Create data entity
            entity_data = {
                "name": f"Entity-{secrets.token_hex(4)}",
                "tenant_id": tenant.id,  # Should be ignored/overridden by server
                "data": {"synthetic": True, "test_id": secrets.token_hex(8)}
            }
            
            async with session.post(
                f"{self.base_url}/api/v1/entities",
                headers=headers,
                json=entity_data
            ) as resp:
                if resp.status in [200, 201]:
                    results["steps_completed"] += 1
                    created = await resp.json()
                    entity_id = created.get("id")
                    if entity_id:
                        tenant.data_created.append(created)
            
            # Step 3: List entities (should only see own data)
            async with session.get(
                f"{self.base_url}/api/v1/entities",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    results["steps_completed"] += 1
                    entities = await resp.json()
                    
                    # Verify all returned entities belong to this tenant
                    for entity in entities.get("items", []):
                        entity_tenant = entity.get("tenant_id")
                        if entity_tenant and entity_tenant != tenant.id:
                            violation = IsolationViolation(
                                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                tenant_id=tenant.id,
                                accessed_tenant_id=entity_tenant,
                                endpoint="/api/v1/entities",
                                description=f"Accessed entity from different tenant: {entity_tenant}"
                            )
                            self.violations.append(violation)
                            results["violations"].append(violation)
            
            # Step 4: Graph query (if applicable)
            async with session.post(
                f"{self.base_url}/api/v1/query/graph",
                headers=headers,
                json={"query": "MATCH (n) RETURN n LIMIT 10"}
            ) as resp:
                if resp.status == 200:
                    results["steps_completed"] += 1
                    graph_data = await resp.json()
                    
                    # Check for cross-tenant nodes
                    for node in graph_data.get("nodes", []):
                        node_tenant = node.get("tenant_id")
                        if node_tenant and node_tenant != tenant.id:
                            violation = IsolationViolation(
                                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                tenant_id=tenant.id,
                                accessed_tenant_id=node_tenant,
                                endpoint="/api/v1/query/graph",
                                description=f"Graph query returned cross-tenant node: {node_tenant}"
                            )
                            self.violations.append(violation)
                            results["violations"].append(violation)
            
            # Step 5: Attempt header spoofing (negative test)
            spoof_headers = {
                **headers,
                "X-Tenant-ID": "spoofed-tenant-999"  # Attempt to access different tenant
            }
            
            async with session.get(
                f"{self.base_url}/api/v1/entities",
                headers=spoof_headers
            ) as resp:
                # Should NOT succeed - verify spoofing was blocked
                if resp.status == 200:
                    entities = await resp.json()
                    # If we got data, check it belongs to original tenant, not spoofed
                    for entity in entities.get("items", []):
                        if entity.get("tenant_id") == "spoofed-tenant-999":
                            violation = IsolationViolation(
                                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                tenant_id=tenant.id,
                                accessed_tenant_id="spoofed-tenant-999",
                                endpoint="/api/v1/entities",
                                description="Header spoofing succeeded - CRITICAL VULNERABILITY"
                            )
                            self.violations.append(violation)
                            results["violations"].append(violation)
            
        except Exception as e:
            logger.error(f"Journey failed for {tenant.id}: {e}")
            results["error"] = str(e)
        
        return results
    
    async def run_realistic_workload(
        self,
        duration_seconds: int = 300,
        concurrent_users: int = 10
    ) -> dict[str, Any]:
        """Run realistic user workload simulation."""
        logger.info(f"Starting realistic workload: {duration_seconds}s with {concurrent_users} concurrent users")
        
        start_time = time.time()
        all_results = []
        
        async with aiohttp.ClientSession() as session:
            while time.time() - start_time < duration_seconds:
                # Create batch of concurrent journeys
                tasks = []
                selected_tenants = random.sample(
                    self.tenants,
                    min(concurrent_users, len(self.tenants))
                )
                
                for tenant in selected_tenants:
                    journey_type = random.choice(["standard", "advanced", "admin"])
                    task = self.simulate_user_journey(session, tenant, journey_type)
                    tasks.append(task)
                
                # Run concurrent journeys
                results = await asyncio.gather(*tasks, return_exceptions=True)
                all_results.extend([r for r in results if not isinstance(r, Exception)])
                
                self.stats["total_requests"] += len(tasks)
                self.stats["successful_requests"] += len([r for r in results if not isinstance(r, Exception)])
                
                # Brief pause between batches
                await asyncio.sleep(0.1)
        
        self.stats["violations_detected"] = len(self.violations)
        
        return {
            "mode": "realistic",
            "duration": duration_seconds,
            "concurrent_users": concurrent_users,
            "total_journeys": len(all_results),
            "violations": len(self.violations),
            "violation_details": [vars(v) for v in self.violations],
            "stats": self.stats
        }
    
    async def run_stress_test(
        self,
        duration_seconds: int = 60,
        concurrent_requests: int = 1000,
        target_endpoint: str = "/api/v1/entities"
    ) -> dict[str, Any]:
        """Run high-volume stress test to find race conditions."""
        logger.info(f"Starting stress test: {duration_seconds}s with {concurrent_requests} concurrent requests")
        
        start_time = time.time()
        violation_count = 0
        
        async def stress_request(tenant: Tenant, spoof_attempt: bool = False) -> dict:
            """Single stress request."""
            target_tenant = random.choice(self.tenants)
            
            headers = {
                "Authorization": f"Bearer {tenant.token}",
                "X-Tenant-ID": tenant.id if not spoof_attempt else target_tenant.id,
                "X-API-Key": tenant.api_key
            }
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.base_url}{target_endpoint}",
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            items = data.get("items", [])
                            
                            # Check for violations
                            violations = []
                            for item in items:
                                item_tenant = item.get("tenant_id")
                                if spoof_attempt and item_tenant == target_tenant.id:
                                    violations.append({
                                        "type": "spoof_success",
                                        "accessed_tenant": item_tenant
                                    })
                                elif not spoof_attempt and item_tenant != tenant.id:
                                    violations.append({
                                        "type": "data_leak",
                                        "accessed_tenant": item_tenant
                                    })
                            
                            return {
                                "success": True,
                                "violations": violations,
                                "response_time": time.time()
                            }
                        return {"success": False, "status": resp.status}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        async with aiohttp.ClientSession() as session:
            while time.time() - start_time < duration_seconds:
                # Generate burst of concurrent requests
                tasks = []
                for _ in range(concurrent_requests):
                    tenant = random.choice(self.tenants)
                    spoof = random.random() < 0.3  # 30% spoof attempts
                    tasks.append(stress_request(tenant, spoof))
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Count violations
                for result in results:
                    if isinstance(result, dict):
                        for v in result.get("violations", []):
                            violation_count += 1
                            violation = IsolationViolation(
                                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                tenant_id="stress-test",
                                accessed_tenant_id=v.get("accessed_tenant", "unknown"),
                                endpoint=target_endpoint,
                                description=f"Stress test violation: {v.get('type')}"
                            )
                            self.violations.append(violation)
                
                self.stats["total_requests"] += len(tasks)
        
        return {
            "mode": "stress",
            "duration": duration_seconds,
            "concurrent_requests": concurrent_requests,
            "total_violations": violation_count,
            "violation_details": [vars(v) for v in self.violations],
            "stats": self.stats
        }
    
    def generate_report(self, output_file: str = None) -> dict[str, Any]:
        """Generate test report."""
        report = {
            "test_type": "Tenant Isolation Validation",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "summary": {
                "total_violations": len(self.violations),
                "violation_severity": {
                    "critical": len([v for v in self.violations if "CRITICAL" in v.description]),
                    "high": len([v for v in self.violations if "spoof" in v.description.lower()]),
                    "medium": len([v for v in self.violations if "mismatch" in v.description.lower()]),
                    "low": len(self.violations)  # All others
                },
                "isolation_test_passed": len(self.violations) == 0
            },
            "statistics": self.stats,
            "violations": [vars(v) for v in self.violations]
        }
        
        if output_file:
            with open(output_file, "w") as f:
                json.dump(report, f, indent=2)
            logger.info(f"Report written to: {output_file}")
        
        return report


def main():
    parser = argparse.ArgumentParser(description="Tenant Isolation Load Test")
    parser.add_argument("--mode", choices=["realistic", "stress"], required=True)
    parser.add_argument("--duration", type=int, default=300, help="Test duration in seconds")
    parser.add_argument("--concurrent", type=int, default=10, help="Concurrent users (realistic) or requests (stress)")
    parser.add_argument("--tenants", type=int, default=10, help="Number of synthetic tenants")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--output", default="tenant-isolation-report.json", help="Output report file")
    parser.add_argument("--fail-on-violation", action="store_true", help="Exit with error if violations found")
    
    args = parser.parse_args()
    
    validator = TenantIsolationValidator(args.base_url)
    validator.generate_synthetic_tenants(args.tenants)
    
    if args.mode == "realistic":
        results = asyncio.run(validator.run_realistic_workload(
            duration_seconds=args.duration,
            concurrent_users=args.concurrent
        ))
    else:
        results = asyncio.run(validator.run_stress_test(
            duration_seconds=args.duration,
            concurrent_requests=args.concurrent
        ))
    
    # Generate report
    report = validator.generate_report(args.output)
    
    # Print summary
    print(f"\n{'='*60}")
    print("TENANT ISOLATION TEST RESULTS")
    print(f"{'='*60}")
    print(f"Mode: {args.mode}")
    print(f"Duration: {args.duration}s")
    print(f"Total violations: {report['summary']['total_violations']}")
    print(f"Test passed: {report['summary']['isolation_test_passed']}")
    print(f"{'='*60}\n")
    
    if report['summary']['total_violations'] > 0:
        print("VIOLATIONS DETECTED:")
        for v in report['violations']:
            print(f"  - {v['description']} ({v['endpoint']})")
        print()
    
    if args.fail_on_violation and report['summary']['total_violations'] > 0:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
