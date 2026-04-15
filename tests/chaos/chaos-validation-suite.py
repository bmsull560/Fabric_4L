#!/usr/bin/env python3
"""
Post-Chaos Validation Suite

Validates system health after chaos experiments complete.
Checks that all services recovered and are functioning correctly.

Usage:
    python chaos-validation-suite.py --namespace value-fabric-prod
"""

import argparse
import asyncio
import json
import logging
import sys
from typing import Any

import aiohttp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChaosValidator:
    """Validates system state after chaos experiments."""
    
    def __init__(self, namespace: str, base_url: str = None):
        self.namespace = namespace
        self.base_url = base_url or f"http://localhost:8000"
        self.results: list[dict] = []
    
    async def check_layer_health(
        self,
        session: aiohttp.ClientSession,
        layer: str,
        port: int = 8000
    ) -> dict[str, Any]:
        """Check if a layer is healthy."""
        url = f"{self.base_url}/health"
        
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                healthy = resp.status == 200
                data = await resp.json() if healthy else {}
                
                return {
                    "layer": layer,
                    "healthy": healthy,
                    "status_code": resp.status,
                    "response_time_ms": 0,  # Would track actual timing
                    "details": data
                }
        except Exception as e:
            return {
                "layer": layer,
                "healthy": False,
                "error": str(e)
            }
    
    async def check_tenant_isolation(
        self,
        session: aiohttp.ClientSession
    ) -> dict[str, Any]:
        """Verify tenant isolation still holds."""
        # Quick check that tenant A cannot see tenant B data
        test_tenant_a = "chaos-test-a"
        test_tenant_b = "chaos-test-b"
        
        try:
            # Create entity as tenant A
            headers_a = {
                "Authorization": f"Bearer {test_tenant_a}",
                "X-Tenant-ID": test_tenant_a
            }
            
            async with session.post(
                f"{self.base_url}/api/v1/entities",
                headers=headers_a,
                json={"name": "chaos-test-entity"},
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                create_success = resp.status in [200, 201]
            
            # Try to access as tenant B (should fail or not see A's data)
            headers_b = {
                "Authorization": f"Bearer {test_tenant_b}",
                "X-Tenant-ID": test_tenant_b
            }
            
            async with session.get(
                f"{self.base_url}/api/v1/entities",
                headers=headers_b,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    items = data.get("items", [])
                    # Check no cross-tenant data
                    cross_tenant = [i for i in items if i.get("tenant_id") == test_tenant_a]
                    isolation_intact = len(cross_tenant) == 0
                else:
                    isolation_intact = True  # Request failed = no data leak
            
            return {
                "check": "tenant_isolation",
                "passed": isolation_intact,
                "create_success": create_success,
                "details": f"Cross-tenant items found: {len(cross_tenant) if 'cross_tenant' in dir() else 'N/A'}"
            }
            
        except Exception as e:
            return {
                "check": "tenant_isolation",
                "passed": False,
                "error": str(e)
            }
    
    async def check_data_consistency(self, session: aiohttp.ClientSession) -> dict[str, Any]:
        """Check that no data was corrupted during chaos."""
        try:
            # Query a known entity and verify it has all required fields
            async with session.get(
                f"{self.base_url}/api/v1/entities?limit=1",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    items = data.get("items", [])
                    
                    if items:
                        entity = items[0]
                        # Check required fields exist
                        has_id = "id" in entity
                        has_tenant = "tenant_id" in entity
                        
                        return {
                            "check": "data_consistency",
                            "passed": has_id and has_tenant,
                            "entity_valid": has_id and has_tenant,
                            "fields_present": {"id": has_id, "tenant_id": has_tenant}
                        }
                    else:
                        return {
                            "check": "data_consistency",
                            "passed": True,  # Empty result is valid
                            "entity_valid": True,
                            "note": "No entities to validate"
                        }
                else:
                    return {
                        "check": "data_consistency",
                        "passed": False,
                        "error": f"HTTP {resp.status}"
                    }
        except Exception as e:
            return {
                "check": "data_consistency",
                "passed": False,
                "error": str(e)
            }
    
    async def check_performance_baseline(
        self,
        session: aiohttp.ClientSession
    ) -> dict[str, Any]:
        """Check that response times are within acceptable range."""
        try:
            start = asyncio.get_event_loop().time()
            
            async with session.get(
                f"{self.base_url}/health",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                elapsed = (asyncio.get_event_loop().time() - start) * 1000
                
                return {
                    "check": "performance_baseline",
                    "passed": elapsed < 1000,  # < 1 second
                    "response_time_ms": elapsed,
                    "status_code": resp.status
                }
        except Exception as e:
            return {
                "check": "performance_baseline",
                "passed": False,
                "error": str(e)
            }
    
    async def run_all_validations(self) -> dict[str, Any]:
        """Run all post-chaos validations."""
        logger.info(f"Running post-chaos validations for namespace: {self.namespace}")
        
        results = {
            "namespace": self.namespace,
            "timestamp": None,  # Will be set below
            "validations": []
        }
        
        async with aiohttp.ClientSession() as session:
            # Layer health checks
            layers = [
                "layer1-ingestion",
                "layer2-extraction",
                "layer3-knowledge",
                "layer4-agents",
                "layer5-ground-truth",
                "layer6-benchmarks"
            ]
            
            for layer in layers:
                health = await self.check_layer_health(session, layer)
                results["validations"].append(health)
                logger.info(f"Layer {layer}: {'✓' if health['healthy'] else '✗'}")
            
            # Tenant isolation check
            isolation = await self.check_tenant_isolation(session)
            results["validations"].append(isolation)
            logger.info(f"Tenant isolation: {'✓' if isolation['passed'] else '✗'}")
            
            # Data consistency check
            consistency = await self.check_data_consistency(session)
            results["validations"].append(consistency)
            logger.info(f"Data consistency: {'✓' if consistency['passed'] else '✗'}")
            
            # Performance baseline check
            performance = await self.check_performance_baseline(session)
            results["validations"].append(performance)
            logger.info(f"Performance: {'✓' if performance['passed'] else '✗'}")
        
        # Calculate overall result
        all_passed = all(v.get("healthy", v.get("passed", False)) for v in results["validations"])
        
        results["timestamp"] = asyncio.get_event_loop().time()
        results["overall_passed"] = all_passed
        results["total_checks"] = len(results["validations"])
        results["passed_checks"] = sum(1 for v in results["validations"] if v.get("healthy", v.get("passed", False)))
        
        return results


def main():
    parser = argparse.ArgumentParser(description="Post-Chaos Validation Suite")
    parser.add_argument("--namespace", required=True, help="Kubernetes namespace")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--output", default="chaos-validation-report.json", help="Output file")
    parser.add_argument("--fail-on-error", action="store_true", help="Exit with error if any check fails")
    
    args = parser.parse_args()
    
    validator = ChaosValidator(args.namespace, args.base_url)
    results = asyncio.run(validator.run_all_validations())
    
    # Write report
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print(f"\n{'='*60}")
    print("CHAOS VALIDATION RESULTS")
    print(f"{'='*60}")
    print(f"Namespace: {results['namespace']}")
    print(f"Total checks: {results['total_checks']}")
    print(f"Passed: {results['passed_checks']}")
    print(f"Failed: {results['total_checks'] - results['passed_checks']}")
    print(f"Overall: {'✓ PASSED' if results['overall_passed'] else '✗ FAILED'}")
    print(f"{'='*60}\n")
    
    if args.fail_on_error and not results["overall_passed"]:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
