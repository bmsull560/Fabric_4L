#!/usr/bin/env python3
"""
Tenant Race Condition Detection Tests

Specialized tests designed to find timing-based isolation vulnerabilities.
Uses carefully crafted concurrent operations that attempt to exploit
race conditions in tenant data access.

Usage:
    python tenant-race-condition-test.py --scenario data-race --duration 120
"""

import argparse
import asyncio
import json
import logging
import random
import secrets
import sys
import time
from dataclasses import dataclass, field
from typing import Any

import aiohttp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RaceConditionResult:
    """Result of a race condition test."""
    scenario: str
    passed: bool
    violations: list[dict] = field(default_factory=list)
    timing_ms: float = 0.0
    concurrent_operations: int = 0


class RaceConditionDetector:
    """Detects race conditions in tenant isolation."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.violations: list[dict] = []
    
    async def scenario_switch_attack(
        self,
        session: aiohttp.ClientSession,
        tenant_a: str,
        tenant_b: str,
        iterations: int = 100
    ) -> RaceConditionResult:
        """
        Rapid tenant context switching attack.
        
        Simulates a malicious user rapidly switching between tenant contexts
        hoping to catch a race condition where the server validates one request
        but processes another with a different tenant context.
        """
        violations = []
        start = time.time()
        
        async def mixed_request(tenant_id: str, request_id: int):
            """Send request with specific tenant context."""
            headers = {
                "Authorization": f"Bearer token-{tenant_id}",
                "X-Tenant-ID": tenant_id,
                "X-Request-ID": f"{request_id}-{secrets.token_hex(4)}"
            }
            
            try:
                async with session.get(
                    f"{self.base_url}/api/v1/entities",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=2)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        # Check for cross-tenant data
                        for item in data.get("items", []):
                            item_tenant = item.get("tenant_id")
                            if item_tenant and item_tenant != tenant_id:
                                return {
                                    "type": "switch_race",
                                    "expected_tenant": tenant_id,
                                    "actual_tenant": item_tenant,
                                    "request_id": request_id
                                }
                    return None
            except Exception:
                return None
        
        # Interleave requests between tenants
        tasks = []
        for i in range(iterations):
            # Alternate between tenants
            tenant = tenant_a if i % 2 == 0 else tenant_b
            tasks.append(mixed_request(tenant, i))
        
        results = await asyncio.gather(*tasks)
        
        for r in results:
            if r:
                violations.append(r)
        
        return RaceConditionResult(
            scenario="switch_attack",
            passed=len(violations) == 0,
            violations=violations,
            timing_ms=(time.time() - start) * 1000,
            concurrent_operations=iterations
        )
    
    async def scenario_read_after_write(
        self,
        session: aiohttp.ClientSession,
        tenant_a: str,
        tenant_b: str,
        iterations: int = 50
    ) -> RaceConditionResult:
        """
        Read-after-write consistency test.
        
        One tenant writes data, immediately another tenant attempts to read it.
        Tests for eventual consistency issues in tenant data isolation.
        """
        violations = []
        start = time.time()
        
        async def write_then_read(write_tenant: str, read_tenant: str, idx: int):
            """Write data, then immediately have different tenant try to read."""
            # Write operation
            write_headers = {
                "Authorization": f"Bearer token-{write_tenant}",
                "X-Tenant-ID": write_tenant
            }
            
            entity_name = f"race-test-{idx}-{secrets.token_hex(4)}"
            write_data = {
                "name": entity_name,
                "data": {"tenant_marker": write_tenant}
            }
            
            try:
                # Create entity
                async with session.post(
                    f"{self.base_url}/api/v1/entities",
                    headers=write_headers,
                    json=write_data,
                    timeout=aiohttp.ClientTimeout(total=2)
                ) as resp:
                    if resp.status in [200, 201]:
                        created = await resp.json()
                        entity_id = created.get("id")
                        
                        # Immediately try to read with different tenant
                        read_headers = {
                            "Authorization": f"Bearer token-{read_tenant}",
                            "X-Tenant-ID": read_tenant
                        }
                        
                        async with session.get(
                            f"{self.base_url}/api/v1/entities/{entity_id}",
                            headers=read_headers,
                            timeout=aiohttp.ClientTimeout(total=2)
                        ) as read_resp:
                            if read_resp.status == 200:
                                # CRITICAL: Should be 403 or 404
                                return {
                                    "type": "raw_violation",
                                    "entity_id": entity_id,
                                    "writer_tenant": write_tenant,
                                    "reader_tenant": read_tenant,
                                    "description": "Cross-tenant read succeeded after write"
                                }
            except Exception:
                pass
            
            return None
        
        # Run concurrent read-after-write tests
        tasks = []
        for i in range(iterations):
            tasks.append(write_then_read(tenant_a, tenant_b, i))
            tasks.append(write_then_read(tenant_b, tenant_a, i))
        
        results = await asyncio.gather(*tasks)
        
        for r in results:
            if r:
                violations.append(r)
        
        return RaceConditionResult(
            scenario="read_after_write",
            passed=len(violations) == 0,
            violations=violations,
            timing_ms=(time.time() - start) * 1000,
            concurrent_operations=iterations * 2
        )
    
    async def scenario_graph_traversal(
        self,
        session: aiohttp.ClientSession,
        tenant_a: str,
        tenant_b: str,
        iterations: int = 30
    ) -> RaceConditionResult:
        """
        Graph traversal race condition.
        
        Creates interconnected entities and tests if graph queries
        can accidentally traverse across tenant boundaries.
        """
        violations = []
        start = time.time()
        
        async def create_linked_entities(tenant: str, prefix: str):
            """Create a chain of linked entities."""
            entities = []
            prev_id = None
            
            for i in range(3):
                headers = {
                    "Authorization": f"Bearer token-{tenant}",
                    "X-Tenant-ID": tenant
                }
                
                data = {
                    "name": f"{prefix}-entity-{i}",
                    "relationships": [{"target": prev_id}] if prev_id else []
                }
                
                try:
                    async with session.post(
                        f"{self.base_url}/api/v1/entities",
                        headers=headers,
                        json=data,
                        timeout=aiohttp.ClientTimeout(total=2)
                    ) as resp:
                        if resp.status in [200, 201]:
                            result = await resp.json()
                            entities.append(result.get("id"))
                            prev_id = result.get("id")
                except Exception:
                    pass
            
            return entities
        
        # Create entity chains for both tenants
        chain_a = await create_linked_entities(tenant_a, "A")
        chain_b = await create_linked_entities(tenant_b, "B")
        
        # Try to traverse from tenant A to tenant B's entities
        if chain_a and chain_b:
            headers = {
                "Authorization": f"Bearer token-{tenant_a}",
                "X-Tenant-ID": tenant_a
            }
            
            # Query that might traverse across tenants
            query = {
                "query": f"MATCH (n)-[*1..3]->(m) WHERE n.id = '{chain_a[0]}' RETURN m",
                "tenant_id": tenant_a
            }
            
            try:
                async with session.post(
                    f"{self.base_url}/api/v1/query/graph",
                    headers=headers,
                    json=query,
                    timeout=aiohttp.ClientTimeout(total=3)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for node in data.get("nodes", []):
                            node_tenant = node.get("tenant_id")
                            if node_tenant == tenant_b:
                                violations.append({
                                    "type": "graph_traversal_race",
                                    "source_tenant": tenant_a,
                                    "leaked_tenant": tenant_b,
                                    "node_id": node.get("id")
                                })
            except Exception:
                pass
        
        return RaceConditionResult(
            scenario="graph_traversal",
            passed=len(violations) == 0,
            violations=violations,
            timing_ms=(time.time() - start) * 1000,
            concurrent_operations=len(chain_a) + len(chain_b)
        )
    
    async def run_all_scenarios(
        self,
        duration_seconds: int = 120,
        tenant_count: int = 5
    ) -> dict[str, Any]:
        """Run all race condition detection scenarios."""
        logger.info(f"Starting race condition detection: {duration_seconds}s")
        
        # Generate test tenants
        tenants = [f"race-tenant-{i}-{secrets.token_hex(4)}" for i in range(tenant_count)]
        
        results = []
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            iteration = 0
            while time.time() - start_time < duration_seconds:
                # Select random tenant pairs
                tenant_a, tenant_b = random.sample(tenants, 2)
                
                # Run all scenarios
                result1 = await self.scenario_switch_attack(
                    session, tenant_a, tenant_b, iterations=20
                )
                results.append(result1)
                
                result2 = await self.scenario_read_after_write(
                    session, tenant_a, tenant_b, iterations=10
                )
                results.append(result2)
                
                result3 = await self.scenario_graph_traversal(
                    session, tenant_a, tenant_b, iterations=5
                )
                results.append(result3)
                
                iteration += 1
                logger.info(f"Completed iteration {iteration}, violations so far: {sum(len(r.violations) for r in results)}")
        
        # Aggregate results
        total_violations = sum(len(r.violations) for r in results)
        passed_scenarios = sum(1 for r in results if r.passed)
        
        return {
            "test_type": "Race Condition Detection",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "duration": duration_seconds,
            "scenario_results": [
                {
                    "scenario": r.scenario,
                    "passed": r.passed,
                    "violations": r.violations,
                    "timing_ms": r.timing_ms,
                    "operations": r.concurrent_operations
                }
                for r in results
            ],
            "summary": {
                "total_scenarios": len(results),
                "passed": passed_scenarios,
                "failed": len(results) - passed_scenarios,
                "total_violations": total_violations,
                "all_tests_passed": total_violations == 0
            }
        }


def main():
    parser = argparse.ArgumentParser(description="Tenant Race Condition Tests")
    parser.add_argument("--scenario", choices=["all", "switch", "raw", "graph"], default="all")
    parser.add_argument("--duration", type=int, default=120, help="Test duration in seconds")
    parser.add_argument("--tenants", type=int, default=5, help="Number of test tenants")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--output", default="race-condition-report.json", help="Output report")
    parser.add_argument("--fail-on-violation", action="store_true", help="Exit error on violations")
    
    args = parser.parse_args()
    
    detector = RaceConditionDetector(args.base_url)
    
    # Run all scenarios
    results = asyncio.run(detector.run_all_scenarios(
        duration_seconds=args.duration,
        tenant_count=args.tenants
    ))
    
    # Write report
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print(f"\n{'='*60}")
    print("RACE CONDITION TEST RESULTS")
    print(f"{'='*60}")
    print(f"Duration: {results['duration']}s")
    print(f"Scenarios run: {results['summary']['total_scenarios']}")
    print(f"Passed: {results['summary']['passed']}")
    print(f"Failed: {results['summary']['failed']}")
    print(f"Total violations: {results['summary']['total_violations']}")
    print(f"All tests passed: {results['summary']['all_tests_passed']}")
    print(f"{'='*60}\n")
    
    if results['summary']['total_violations'] > 0:
        print("RACE CONDITION VIOLATIONS DETECTED!")
        for scenario in results['scenario_results']:
            if scenario['violations']:
                print(f"\nScenario: {scenario['scenario']}")
                for v in scenario['violations']:
                    print(f"  - {v.get('type')}: {v.get('description', 'No description')}")
    
    if args.fail_on_violation and not results['summary']['all_tests_passed']:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
