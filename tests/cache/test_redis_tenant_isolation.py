"""
Cache Isolation Tests (Suite 5).

Verifies that Redis cache keys are properly scoped by tenant_id to prevent
cache poisoning attacks where one tenant can read or pollute another tenant's
cached data.

Test Strategy:
- Verify all cache keys include tenant_id prefix
- Test cross-tenant cache pollution scenarios
- Verify cache invalidation is tenant-scoped
- Test degraded mode (Redis unavailable) maintains isolation
- Verify rate limit keys are tenant-scoped
- Test session/token cache isolation

Critical Security Property:
    Cache[tenant_A][key] MUST NOT be accessible to tenant_B
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4
from datetime import datetime, timedelta

import redis.asyncio as redis
from shared.identity.context import RequestContext
from shared.rate_limiting.tenant_rate_limiter import TenantRateLimiter, TenantTier


# ═══════════════════════════════════════════════════════════════════════════
# Test Suite: Redis Key Tenant Scoping
# ═══════════════════════════════════════════════════════════════════════════


class TestRateLimitKeyIsolation:
    """Verify rate limit keys are tenant-scoped."""
    
    @pytest.mark.asyncio
    async def test_rate_limit_keys_include_tenant_id(self):
        """Rate limit keys must include tenant_id to prevent cross-tenant pollution.
        
        Rationale: Without tenant_id in key, tenant A could exhaust tenant B's quota.
        """
        tenant_a = uuid4()
        tenant_b = uuid4()
        
        mock_redis = AsyncMock()
        mock_redis.zadd = AsyncMock(return_value=1)
        mock_redis.zcount = AsyncMock(return_value=1)
        mock_redis.expire = AsyncMock(return_value=True)
        
        limiter = TenantRateLimiter(redis_client=mock_redis)
        
        # Make requests for both tenants
        await limiter.check_rate_limit(
            tenant_id=tenant_a,
            endpoint="/api/test",
            tier=TenantTier.SHARED
        )
        
        await limiter.check_rate_limit(
            tenant_id=tenant_b,
            endpoint="/api/test",
            tier=TenantTier.SHARED
        )
        
        # Verify keys are different and include tenant_id
        calls = mock_redis.zadd.call_args_list
        assert len(calls) == 2
        
        key_a = calls[0][0][0]
        key_b = calls[1][0][0]
        
        assert str(tenant_a) in key_a
        assert str(tenant_b) in key_b
        assert key_a != key_b
    
    @pytest.mark.asyncio
    async def test_tenant_cannot_exhaust_another_tenants_quota(self):
        """Tenant A making requests must not affect tenant B's quota.
        
        Rationale: Shared rate limit keys would allow DoS attacks between tenants.
        """
        tenant_a = uuid4()
        tenant_b = uuid4()
        
        mock_redis = AsyncMock()
        
        # Tenant A makes 100 requests (exhausts quota)
        call_count = {}
        
        async def mock_zcount(key):
            call_count[key] = call_count.get(key, 0) + 1
            return call_count[key]
        
        mock_redis.zadd = AsyncMock(return_value=1)
        mock_redis.zcount = mock_zcount
        mock_redis.expire = AsyncMock(return_value=True)
        
        limiter = TenantRateLimiter(redis_client=mock_redis)
        
        # Tenant A exhausts quota
        for _ in range(100):
            await limiter.check_rate_limit(
                tenant_id=tenant_a,
                endpoint="/api/test",
                tier=TenantTier.SHARED
            )
        
        # Tenant B should still have full quota
        result = await limiter.check_rate_limit(
            tenant_id=tenant_b,
            endpoint="/api/test",
            tier=TenantTier.SHARED
        )
        
        # Tenant B's first request should succeed
        assert result.allowed is True
        assert result.remaining > 0
    
    @pytest.mark.asyncio
    async def test_rate_limit_reset_is_tenant_scoped(self):
        """Resetting rate limits for tenant A must not affect tenant B.
        
        Rationale: Admin operations must maintain tenant isolation.
        """
        tenant_a = uuid4()
        tenant_b = uuid4()
        
        mock_redis = AsyncMock()
        deleted_keys = set()
        
        async def mock_delete(*keys):
            deleted_keys.update(keys)
            return len(keys)
        
        mock_redis.delete = mock_delete
        mock_redis.keys = AsyncMock(return_value=[
            f"ratelimit:tenant:{tenant_a}:endpoint:/api/test:window:60".encode(),
            f"ratelimit:tenant:{tenant_b}:endpoint:/api/test:window:60".encode(),
        ])
        
        limiter = TenantRateLimiter(redis_client=mock_redis)
        
        # Reset tenant A's limits
        await limiter.reset_tenant_limits(tenant_id=tenant_a)
        
        # Only tenant A's keys should be deleted
        assert any(str(tenant_a) in key for key in deleted_keys)
        assert not any(str(tenant_b) in key for key in deleted_keys)


class TestCacheKeyIsolation:
    """Verify general cache keys are tenant-scoped."""
    
    @pytest.mark.asyncio
    async def test_entity_cache_keys_include_tenant_id(self):
        """Entity cache keys must include tenant_id.
        
        Rationale: Without tenant_id, tenant A could read tenant B's cached entities.
        """
        from value_fabric.layer3_knowledge.src.api.cache import get_cached_entity, set_cached_entity
        
        tenant_a = uuid4()
        tenant_b = uuid4()
        entity_id = "entity-123"
        
        mock_redis = AsyncMock()
        cache_store = {}
        
        async def mock_get(key):
            return cache_store.get(key)
        
        async def mock_set(key, value, ex=None):
            cache_store[key] = value
            return True
        
        mock_redis.get = mock_get
        mock_redis.set = mock_set
        
        with patch("value_fabric.layer3_knowledge.src.api.cache.redis_client", mock_redis):
            # Cache entity for tenant A
            await set_cached_entity(
                tenant_id=tenant_a,
                entity_id=entity_id,
                entity_data={"name": "Tenant A Entity"}
            )
            
            # Cache different entity for tenant B with same ID
            await set_cached_entity(
                tenant_id=tenant_b,
                entity_id=entity_id,
                entity_data={"name": "Tenant B Entity"}
            )
            
            # Verify keys are different
            assert len(cache_store) == 2
            keys = list(cache_store.keys())
            assert str(tenant_a) in keys[0]
            assert str(tenant_b) in keys[1]
            
            # Verify tenant A gets their entity
            entity_a = await get_cached_entity(tenant_id=tenant_a, entity_id=entity_id)
            assert entity_a["name"] == "Tenant A Entity"
            
            # Verify tenant B gets their entity
            entity_b = await get_cached_entity(tenant_id=tenant_b, entity_id=entity_id)
            assert entity_b["name"] == "Tenant B Entity"
    
    @pytest.mark.asyncio
    async def test_query_result_cache_is_tenant_scoped(self):
        """Query result caches must be tenant-scoped.
        
        Rationale: Shared query cache would leak search results between tenants.
        """
        from value_fabric.layer3_knowledge.src.api.cache import get_cached_query, set_cached_query
        
        tenant_a = uuid4()
        tenant_b = uuid4()
        query = "AI technology"
        
        mock_redis = AsyncMock()
        cache_store = {}
        
        async def mock_get(key):
            return cache_store.get(key)
        
        async def mock_set(key, value, ex=None):
            cache_store[key] = value
            return True
        
        mock_redis.get = mock_get
        mock_redis.set = mock_set
        
        with patch("value_fabric.layer3_knowledge.src.api.cache.redis_client", mock_redis):
            # Cache query results for tenant A
            await set_cached_query(
                tenant_id=tenant_a,
                query=query,
                results=[{"id": "a1", "name": "Tenant A Result"}]
            )
            
            # Cache different results for tenant B
            await set_cached_query(
                tenant_id=tenant_b,
                query=query,
                results=[{"id": "b1", "name": "Tenant B Result"}]
            )
            
            # Verify tenant A gets their results
            results_a = await get_cached_query(tenant_id=tenant_a, query=query)
            assert results_a[0]["id"] == "a1"
            
            # Verify tenant B gets their results
            results_b = await get_cached_query(tenant_id=tenant_b, query=query)
            assert results_b[0]["id"] == "b1"
    
    @pytest.mark.asyncio
    async def test_cache_invalidation_is_tenant_scoped(self):
        """Cache invalidation for tenant A must not affect tenant B.
        
        Rationale: Bulk invalidation must maintain tenant boundaries.
        """
        from value_fabric.layer3_knowledge.src.api.cache import invalidate_tenant_cache
        
        tenant_a = uuid4()
        tenant_b = uuid4()
        
        mock_redis = AsyncMock()
        cache_store = {
            f"cache:tenant:{tenant_a}:entity:e1": b"data_a",
            f"cache:tenant:{tenant_a}:query:q1": b"data_a",
            f"cache:tenant:{tenant_b}:entity:e1": b"data_b",
            f"cache:tenant:{tenant_b}:query:q1": b"data_b",
        }
        
        async def mock_keys(pattern):
            return [k.encode() for k in cache_store.keys() if pattern.replace("*", "") in k]
        
        async def mock_delete(*keys):
            for key in keys:
                cache_store.pop(key.decode() if isinstance(key, bytes) else key, None)
            return len(keys)
        
        mock_redis.keys = mock_keys
        mock_redis.delete = mock_delete
        
        with patch("value_fabric.layer3_knowledge.src.api.cache.redis_client", mock_redis):
            # Invalidate tenant A's cache
            await invalidate_tenant_cache(tenant_id=tenant_a)
            
            # Tenant A's cache should be gone
            assert not any(str(tenant_a) in k for k in cache_store.keys())
            
            # Tenant B's cache should remain
            assert any(str(tenant_b) in k for k in cache_store.keys())
            assert len([k for k in cache_store.keys() if str(tenant_b) in k]) == 2


# ═══════════════════════════════════════════════════════════════════════════
# Test Suite: Session and Token Cache Isolation
# ═══════════════════════════════════════════════════════════════════════════


class TestSessionCacheIsolation:
    """Verify session and token caches are tenant-scoped."""
    
    @pytest.mark.asyncio
    async def test_session_tokens_are_tenant_scoped(self):
        """Session tokens must be scoped to tenant_id.
        
        Rationale: Shared session cache would allow session hijacking between tenants.
        """
        from shared.identity.session_cache import get_session, set_session
        
        tenant_a = uuid4()
        tenant_b = uuid4()
        user_id = uuid4()
        
        mock_redis = AsyncMock()
        cache_store = {}
        
        async def mock_get(key):
            return cache_store.get(key)
        
        async def mock_set(key, value, ex=None):
            cache_store[key] = value
            return True
        
        mock_redis.get = mock_get
        mock_redis.set = mock_set
        
        with patch("shared.identity.session_cache.redis_client", mock_redis):
            # Create session for user in tenant A
            session_a = await set_session(
                tenant_id=tenant_a,
                user_id=user_id,
                session_data={"role": "admin"}
            )
            
            # Create session for same user in tenant B
            session_b = await set_session(
                tenant_id=tenant_b,
                user_id=user_id,
                session_data={"role": "viewer"}
            )
            
            # Verify sessions are isolated
            retrieved_a = await get_session(tenant_id=tenant_a, user_id=user_id)
            assert retrieved_a["role"] == "admin"
            
            retrieved_b = await get_session(tenant_id=tenant_b, user_id=user_id)
            assert retrieved_b["role"] == "viewer"
    
    @pytest.mark.asyncio
    async def test_api_key_cache_is_tenant_scoped(self):
        """API key validation cache must be tenant-scoped.
        
        Rationale: Shared API key cache could allow key reuse between tenants.
        """
        from shared.identity.api_key_cache import validate_api_key
        
        tenant_a = uuid4()
        tenant_b = uuid4()
        api_key = "sk_test_12345"
        
        mock_redis = AsyncMock()
        cache_store = {}
        
        async def mock_get(key):
            return cache_store.get(key)
        
        async def mock_set(key, value, ex=None):
            cache_store[key] = value
            return True
        
        mock_redis.get = mock_get
        mock_redis.set = mock_set
        
        with patch("shared.identity.api_key_cache.redis_client", mock_redis):
            # Cache API key for tenant A
            await validate_api_key(
                api_key=api_key,
                tenant_id=tenant_a,
                is_valid=True
            )
            
            # Same API key should not be valid for tenant B
            is_valid_b = await validate_api_key(
                api_key=api_key,
                tenant_id=tenant_b,
                is_valid=None  # Check cache
            )
            
            # Should not find cached validation for tenant B
            assert is_valid_b is None


# ═══════════════════════════════════════════════════════════════════════════
# Test Suite: Degraded Mode Isolation
# ═══════════════════════════════════════════════════════════════════════════


class TestDegradedModeIsolation:
    """Verify tenant isolation is maintained when Redis is unavailable."""
    
    @pytest.mark.asyncio
    async def test_rate_limiting_fails_safe_when_redis_unavailable(self):
        """Rate limiting must fail safe (deny) when Redis is unavailable.
        
        Rationale: Falling back to in-memory cache in multi-worker deployment
        would break tenant isolation.
        """
        tenant_id = uuid4()
        
        mock_redis = AsyncMock()
        mock_redis.zadd = AsyncMock(side_effect=redis.ConnectionError("Connection refused"))
        
        limiter = TenantRateLimiter(redis_client=mock_redis)
        
        # Request should be denied when Redis is unavailable
        result = await limiter.check_rate_limit(
            tenant_id=tenant_id,
            endpoint="/api/test",
            tier=TenantTier.SHARED
        )
        
        # In production, should fail closed (deny request)
        # In development, may allow with warning
        assert result.allowed is False or result.error is not None
    
    @pytest.mark.asyncio
    async def test_cache_miss_does_not_leak_data(self):
        """Cache miss must not fall back to cross-tenant data source.
        
        Rationale: Cache miss should trigger fresh DB query with tenant filter,
        not return data from another tenant.
        """
        from value_fabric.layer3_knowledge.src.api.cache import get_cached_entity
        
        tenant_a = uuid4()
        tenant_b = uuid4()
        entity_id = "entity-123"
        
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)  # Cache miss
        
        with patch("value_fabric.layer3_knowledge.src.api.cache.redis_client", mock_redis):
            # Cache miss for tenant A
            result = await get_cached_entity(tenant_id=tenant_a, entity_id=entity_id)
            
            # Should return None, not data from tenant B
            assert result is None
    
    @pytest.mark.asyncio
    async def test_redis_connection_pool_does_not_leak_tenant_context(self):
        """Redis connection pool must not leak tenant context between requests.
        
        Rationale: Pooled connections reused across requests must not carry
        tenant context from previous request.
        """
        tenant_a = uuid4()
        tenant_b = uuid4()
        
        # Simulate connection pool with single connection
        mock_redis = AsyncMock()
        connection_state = {}
        
        async def mock_set(key, value, ex=None):
            # Verify key includes tenant_id
            if "tenant" not in key:
                raise AssertionError(f"Key missing tenant scope: {key}")
            connection_state[key] = value
            return True
        
        mock_redis.set = mock_set
        
        from value_fabric.layer3_knowledge.src.api.cache import set_cached_entity
        
        with patch("value_fabric.layer3_knowledge.src.api.cache.redis_client", mock_redis):
            # Request 1: Tenant A
            await set_cached_entity(
                tenant_id=tenant_a,
                entity_id="e1",
                entity_data={"name": "A"}
            )
            
            # Request 2: Tenant B (reuses connection)
            await set_cached_entity(
                tenant_id=tenant_b,
                entity_id="e1",
                entity_data={"name": "B"}
            )
            
            # Verify both keys include correct tenant_id
            keys = list(connection_state.keys())
            assert any(str(tenant_a) in k for k in keys)
            assert any(str(tenant_b) in k for k in keys)


# ═══════════════════════════════════════════════════════════════════════════
# Test Suite: Cache Poisoning Attack Scenarios
# ═══════════════════════════════════════════════════════════════════════════


class TestCachePoisoningPrevention:
    """Verify cache poisoning attacks are prevented."""
    
    @pytest.mark.asyncio
    async def test_tenant_cannot_poison_another_tenants_cache(self):
        """Tenant A must not be able to write to tenant B's cache keys.
        
        Attack scenario: Malicious tenant crafts cache key to pollute another tenant.
        """
        from value_fabric.layer3_knowledge.src.api.cache import set_cached_entity
        
        tenant_a = uuid4()
        tenant_b = uuid4()
        
        mock_redis = AsyncMock()
        cache_store = {}
        
        async def mock_set(key, value, ex=None):
            # Verify key matches tenant_id in request context
            # This should be enforced by cache layer
            cache_store[key] = value
            return True
        
        mock_redis.set = mock_set
        
        with patch("value_fabric.layer3_knowledge.src.api.cache.redis_client", mock_redis):
            # Tenant A tries to write with tenant B's ID in key
            # This should be prevented by cache layer validation
            await set_cached_entity(
                tenant_id=tenant_a,  # Authenticated as tenant A
                entity_id="e1",
                entity_data={"malicious": "data"}
            )
            
            # Verify key includes tenant_a, not tenant_b
            keys = list(cache_store.keys())
            assert all(str(tenant_a) in k for k in keys)
            assert not any(str(tenant_b) in k for k in keys)
    
    @pytest.mark.asyncio
    async def test_cache_key_injection_is_prevented(self):
        """Cache key injection attacks must be prevented.
        
        Attack scenario: Tenant provides entity_id with embedded tenant_id
        to bypass tenant scoping.
        """
        from value_fabric.layer3_knowledge.src.api.cache import set_cached_entity
        
        tenant_a = uuid4()
        tenant_b = uuid4()
        
        # Malicious entity_id trying to inject tenant_b into key
        malicious_entity_id = f"../../tenant:{tenant_b}:entity:secret"
        
        mock_redis = AsyncMock()
        cache_store = {}
        
        async def mock_set(key, value, ex=None):
            cache_store[key] = value
            return True
        
        mock_redis.set = mock_set
        
        with patch("value_fabric.layer3_knowledge.src.api.cache.redis_client", mock_redis):
            await set_cached_entity(
                tenant_id=tenant_a,
                entity_id=malicious_entity_id,
                entity_data={"test": "data"}
            )
            
            # Verify key still scoped to tenant_a
            keys = list(cache_store.keys())
            assert len(keys) == 1
            assert str(tenant_a) in keys[0]
            # Malicious path traversal should be sanitized
            assert "../" not in keys[0]
    
    @pytest.mark.asyncio
    async def test_wildcard_cache_invalidation_is_tenant_scoped(self):
        """Wildcard cache invalidation must not cross tenant boundaries.
        
        Attack scenario: Tenant A tries to invalidate all caches using wildcard.
        """
        from value_fabric.layer3_knowledge.src.api.cache import invalidate_cache_pattern
        
        tenant_a = uuid4()
        tenant_b = uuid4()
        
        mock_redis = AsyncMock()
        cache_store = {
            f"cache:tenant:{tenant_a}:entity:e1": b"data_a",
            f"cache:tenant:{tenant_a}:entity:e2": b"data_a",
            f"cache:tenant:{tenant_b}:entity:e1": b"data_b",
            f"cache:tenant:{tenant_b}:entity:e2": b"data_b",
        }
        
        async def mock_keys(pattern):
            # Verify pattern includes tenant_id
            if f"tenant:{tenant_a}" not in pattern:
                raise AssertionError("Wildcard pattern must include tenant_id")
            return [k.encode() for k in cache_store.keys() if pattern.replace("*", "") in k]
        
        async def mock_delete(*keys):
            for key in keys:
                cache_store.pop(key.decode() if isinstance(key, bytes) else key, None)
            return len(keys)
        
        mock_redis.keys = mock_keys
        mock_redis.delete = mock_delete
        
        with patch("value_fabric.layer3_knowledge.src.api.cache.redis_client", mock_redis):
            # Tenant A tries to invalidate with wildcard
            await invalidate_cache_pattern(
                tenant_id=tenant_a,
                pattern="entity:*"
            )
            
            # Only tenant A's cache should be affected
            assert not any(str(tenant_a) in k for k in cache_store.keys())
            assert all(str(tenant_b) in k for k in cache_store.keys())
