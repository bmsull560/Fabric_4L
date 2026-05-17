"""Targeted tests to boost coverage on under-covered modules."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ===========================================================================
# startup_dependencies
# ===========================================================================

class TestStartupDependencies:
    def test_require_tenant_context_returns_id(self):
        from layer2_extraction.startup_dependencies import require_tenant_context

        class _Ctx:
            tenant_id = "t1"

        assert require_tenant_context(_Ctx()) == "t1"

    def test_require_tenant_context_raises_without_id(self):
        from layer2_extraction.startup_dependencies import require_tenant_context

        class _Ctx:
            tenant_id = None

        with pytest.raises(ValueError, match="Tenant context required"):
            require_tenant_context(_Ctx())

    def test_require_tenant_context_raises_missing_attr(self):
        from layer2_extraction.startup_dependencies import require_tenant_context

        with pytest.raises(ValueError, match="Tenant context required"):
            require_tenant_context(object())

    def test_verify_startup_dependencies_dev_permissive(self, monkeypatch):
        import importlib.util
        monkeypatch.setattr(importlib.util, "find_spec", lambda name: None)
        from layer2_extraction.startup_dependencies import verify_startup_dependencies
        verify_startup_dependencies(environment="development")  # should not raise

    def test_verify_startup_dependencies_prod_raises(self, monkeypatch):
        import importlib.util
        monkeypatch.setattr(importlib.util, "find_spec", lambda name: None)
        from layer2_extraction.startup_dependencies import verify_startup_dependencies
        with pytest.raises(RuntimeError):
            verify_startup_dependencies(environment="production")


# ===========================================================================
# coreference_resolver.py  (the name-dedup resolver)
# ===========================================================================

class TestCoreferenceResolverNameDedup:
    def setup_method(self):
        from layer2_extraction.coreference.coreference_resolver import CoreferenceResolver
        self.resolver = CoreferenceResolver()

    def test_empty_list(self):
        assert self.resolver.resolve([]) == []

    def test_single_entity_passthrough(self):
        e = {"name": "Analytics", "entity_type": "capability"}
        result = self.resolver.resolve([e])
        assert result == [e]

    def test_deduplicates_same_name_and_type(self):
        e1 = {"name": "Analytics", "entity_type": "capability"}
        e2 = {"name": "Analytics", "entity_type": "capability"}
        result = self.resolver.resolve([e1, e2])
        assert len(result) == 1
        assert result[0] is e1

    def test_case_insensitive_dedup(self):
        e1 = {"name": "Analytics Engine", "entity_type": "capability"}
        e2 = {"name": "analytics engine", "entity_type": "capability"}
        result = self.resolver.resolve([e1, e2])
        assert len(result) == 1

    def test_different_types_not_deduped(self):
        e1 = {"name": "Analytics", "entity_type": "capability"}
        e2 = {"name": "Analytics", "entity_type": "use_case"}
        result = self.resolver.resolve([e1, e2])
        assert len(result) == 2

    def test_entity_without_identity_fields_passthrough(self):
        e = {"description": "no name or type"}
        result = self.resolver.resolve([e])
        assert result == [e]

    def test_merges_provenance_dict(self):
        e1 = {"name": "A", "entity_type": "cap", "provenance": ["src1"]}
        e2 = {"name": "A", "entity_type": "cap", "provenance": ["src2"]}
        result = self.resolver.resolve([e1, e2])
        assert len(result) == 1
        assert "src2" in result[0]["provenance"]

    def test_cross_tenant_raises(self):
        e1 = {"name": "A", "entity_type": "cap", "tenant_id": "t1"}
        e2 = {"name": "A", "entity_type": "cap", "tenant_id": "t2"}
        with pytest.raises(ValueError, match="Cross-tenant"):
            self.resolver.resolve([e1, e2])

    def test_are_semantically_equivalent_always_false(self):
        e1 = {"name": "A", "entity_type": "cap"}
        e2 = {"name": "A", "entity_type": "cap"}
        assert self.resolver.are_semantically_equivalent(e1, e2) is False

    def test_attr_style_entities(self):
        class _E:
            def __init__(self, name, etype):
                self.name = name
                self.entity_type = etype
        e1 = _E("Analytics", "capability")
        e2 = _E("Analytics", "capability")
        result = self.resolver.resolve([e1, e2])
        assert len(result) == 1

    def test_merges_provenance_attr_style(self):
        class _E:
            def __init__(self, name, etype, prov):
                self.name = name
                self.entity_type = etype
                self.provenance = prov
        e1 = _E("A", "cap", ["src1"])
        e2 = _E("A", "cap", ["src2"])
        result = self.resolver.resolve([e1, e2])
        assert len(result) == 1
        assert "src2" in result[0].provenance

    def test_get_key_fields_dict(self):
        from layer2_extraction.coreference.coreference_resolver import CoreferenceResolver
        name, etype = CoreferenceResolver._get_key_fields({"name": "Foo", "entity_type": "bar"})
        assert name == "foo"
        assert etype == "bar"

    def test_get_key_fields_missing(self):
        from layer2_extraction.coreference.coreference_resolver import CoreferenceResolver
        name, etype = CoreferenceResolver._get_key_fields({})
        assert name is None
        assert etype is None


# ===========================================================================
# ExtractionCache (in-memory fallback path)
# ===========================================================================

class TestExtractionCacheInMemory:
    def setup_method(self):
        from layer2_extraction.extraction.cache import ExtractionCache
        # No redis_url → uses in-memory LRU fallback
        self.cache = ExtractionCache(redis_url=None)

    @pytest.mark.asyncio
    async def test_get_miss_returns_none(self):
        result = await self.cache.get("text", "endpoint")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_then_get_returns_value(self):
        await self.cache.set("hello", "ep1", {"data": 42})
        result = await self.cache.get("hello", "ep1")
        assert result == {"data": 42}

    @pytest.mark.asyncio
    async def test_different_endpoints_separate_keys(self):
        await self.cache.set("text", "ep1", "value1")
        await self.cache.set("text", "ep2", "value2")
        assert await self.cache.get("text", "ep1") == "value1"
        assert await self.cache.get("text", "ep2") == "value2"

    @pytest.mark.asyncio
    async def test_different_models_separate_keys(self):
        await self.cache.set("text", "ep", "v1", model="gpt-4o")
        await self.cache.set("text", "ep", "v2", model="gpt-4o-mini")
        assert await self.cache.get("text", "ep", model="gpt-4o") == "v1"
        assert await self.cache.get("text", "ep", model="gpt-4o-mini") == "v2"

    @pytest.mark.asyncio
    async def test_close_no_error(self):
        await self.cache.close()  # should not raise

    def test_make_key_deterministic(self):
        k1 = self.cache._make_key("t", "ep", "gpt-4o", 0.0)
        k2 = self.cache._make_key("t", "ep", "gpt-4o", 0.0)
        assert k1 == k2

    def test_make_key_differs_on_text(self):
        k1 = self.cache._make_key("text1", "ep", "gpt-4o", 0.0)
        k2 = self.cache._make_key("text2", "ep", "gpt-4o", 0.0)
        assert k1 != k2


class TestExtractionCacheRedisPath:
    """Tests for the Redis-backed path of ExtractionCache.

    Uses patch("redis.asyncio.from_url") so __init__ runs normally and the
    real _make_key, TTL, and pickle serialization paths are exercised.
    """

    def _make_cache(self, mock_redis: AsyncMock):
        from layer2_extraction.extraction.cache import ExtractionCache
        with patch("redis.asyncio.from_url", return_value=mock_redis):
            return ExtractionCache(redis_url="redis://localhost:6379")

    @pytest.mark.asyncio
    async def test_redis_get_returns_deserialized_value(self):
        import pickle
        from layer2_extraction.extraction.cache import ExtractionCache

        stored = {"result": "ok"}
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=pickle.dumps(stored))

        cache = self._make_cache(mock_redis)
        result = await cache.get("some text", "my_endpoint")

        assert result == stored
        # Verify the real key was constructed (not a stub)
        call_args = mock_redis.get.call_args[0][0]
        assert isinstance(call_args, str) and len(call_args) > 0

    @pytest.mark.asyncio
    async def test_redis_get_miss_returns_none(self):
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)

        cache = self._make_cache(mock_redis)
        result = await cache.get("some text", "my_endpoint")
        assert result is None

    @pytest.mark.asyncio
    async def test_redis_get_exception_falls_to_fallback(self):
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=Exception("redis down"))

        cache = self._make_cache(mock_redis)
        # Fallback is in-memory; no prior set → miss
        result = await cache.get("some text", "my_endpoint")
        assert result is None

    @pytest.mark.asyncio
    async def test_redis_set_calls_setex_with_correct_ttl(self):
        from layer2_extraction.extraction.cache import LLM_CACHE_TTL_SECONDS
        import pickle

        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock()

        cache = self._make_cache(mock_redis)
        await cache.set("some text", "my_endpoint", {"data": 42})

        mock_redis.setex.assert_called_once()
        key, ttl, raw = mock_redis.setex.call_args[0]
        assert isinstance(key, str) and len(key) > 0
        assert ttl == LLM_CACHE_TTL_SECONDS
        assert pickle.loads(raw) == {"data": 42}

    @pytest.mark.asyncio
    async def test_redis_set_exception_does_not_raise(self):
        """A Redis setex failure is swallowed; the value is not stored."""
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock(side_effect=Exception("redis down"))
        mock_redis.get = AsyncMock(return_value=None)

        cache = self._make_cache(mock_redis)
        # Should not raise even when Redis is unavailable
        await cache.set("some text", "my_endpoint", "value")
        # Value is not retrievable (no fallback when Redis init succeeded)
        result = await cache.get("some text", "my_endpoint")
        assert result is None

    @pytest.mark.asyncio
    async def test_redis_close(self):
        mock_redis = AsyncMock()
        mock_redis.close = AsyncMock()

        cache = self._make_cache(mock_redis)
        await cache.close()
        mock_redis.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_close_exception_suppressed(self):
        mock_redis = AsyncMock()
        mock_redis.close = AsyncMock(side_effect=Exception("close error"))

        cache = self._make_cache(mock_redis)
        await cache.close()  # should not raise


# ===========================================================================
# Layer3KnowledgeClient + _CircuitBreaker
# ===========================================================================

class TestCircuitBreaker:
    def setup_method(self):
        from layer2_extraction.integration.layer3_client import _CircuitBreaker
        self.cb = _CircuitBreaker(failure_threshold=3, recovery_timeout_seconds=30.0)

    def test_initial_state_closed(self):
        assert self.cb._state == "closed"
        assert self.cb.can_attempt() is True

    def test_record_success_resets(self):
        self.cb._failures = 2
        self.cb._state = "half_open"
        self.cb.record_success()
        assert self.cb._failures == 0
        assert self.cb._state == "closed"

    def test_record_failure_increments(self):
        self.cb.record_failure()
        assert self.cb._failures == 1
        assert self.cb._state == "closed"

    def test_record_failure_opens_at_threshold(self):
        for _ in range(3):
            self.cb.record_failure()
        assert self.cb._state == "open"
        assert self.cb.can_attempt() is False

    def test_half_open_after_recovery_timeout(self):
        import time
        for _ in range(3):
            self.cb.record_failure()
        self.cb._last_failure_time = time.monotonic() - 31.0
        assert self.cb.can_attempt() is True
        assert self.cb._state == "half_open"

    def test_open_before_recovery_timeout(self):
        import time
        for _ in range(3):
            self.cb.record_failure()
        self.cb._last_failure_time = time.monotonic() - 1.0
        assert self.cb.can_attempt() is False


class TestLayer3KnowledgeClient:
    def _make_client(self, mock_http=None):
        from layer2_extraction.integration.layer3_client import Layer3KnowledgeClient
        http = mock_http or AsyncMock()
        http.__aenter__ = AsyncMock(return_value=http)
        http.__aexit__ = AsyncMock(return_value=False)
        return Layer3KnowledgeClient(
            base_url="http://test-layer3:8003",
            api_key="key",
            client=http,
        )

    @pytest.mark.asyncio
    async def test_health_check_healthy(self):
        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=MagicMock(status_code=200))
        client = self._make_client(mock_http)
        assert await client.health_check(force=True) is True

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self):
        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=MagicMock(status_code=503))
        client = self._make_client(mock_http)
        assert await client.health_check(force=True) is False

    @pytest.mark.asyncio
    async def test_health_check_exception_returns_false(self):
        mock_http = AsyncMock()
        mock_http.get = AsyncMock(side_effect=Exception("network error"))
        client = self._make_client(mock_http)
        assert await client.health_check(force=True) is False

    @pytest.mark.asyncio
    async def test_health_check_cached(self):
        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=MagicMock(status_code=200))
        client = self._make_client(mock_http)
        await client.health_check(force=True)
        await client.health_check()  # should use cache
        assert mock_http.get.call_count == 1

    @pytest.mark.asyncio
    async def test_health_check_circuit_open_returns_false(self):
        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=MagicMock(status_code=200))
        client = self._make_client(mock_http)
        # Force circuit open
        client._circuit._state = "open"
        import time
        client._circuit._last_failure_time = time.monotonic()
        result = await client.health_check(force=True)
        assert result is False

    @pytest.mark.asyncio
    async def test_ingest_rdf_data_success(self):
        from layer2_extraction.integration.layer3_client import IngestionResponse
        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=MagicMock(status_code=200))
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "success": True, "ingestion_id": "job-1",
            "entities_loaded": 3, "relationships_loaded": 1, "message": "ok",
        }
        mock_http.post = AsyncMock(return_value=mock_resp)
        client = self._make_client(mock_http)
        result = await client.ingest_rdf_data(
            rdf_data="<rdf/>", source_url="http://x.com", extraction_job_id="job-1"
        )
        assert result.success is True
        assert result.entities_loaded == 3

    @pytest.mark.asyncio
    async def test_ingest_rdf_data_health_fail_returns_error(self):
        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=MagicMock(status_code=503))
        client = self._make_client(mock_http)
        result = await client.ingest_rdf_data(
            rdf_data="<rdf/>", source_url="http://x.com", extraction_job_id="job-1"
        )
        assert result.success is False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_ingest_rdf_data_post_exception(self):
        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=MagicMock(status_code=200))
        mock_http.post = AsyncMock(side_effect=Exception("timeout"))
        client = self._make_client(mock_http)
        result = await client.ingest_rdf_data(
            rdf_data="<rdf/>", source_url="http://x.com", extraction_job_id="job-1"
        )
        assert result.success is False
        assert "timeout" in result.error

    @pytest.mark.asyncio
    async def test_batch_ingest_empty_returns_empty(self):
        client = self._make_client()
        result = await client.batch_ingest_rdf_data([])
        assert result == []

    @pytest.mark.asyncio
    async def test_batch_ingest_health_fail(self):
        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=MagicMock(status_code=503))
        client = self._make_client(mock_http)
        items = [{"rdf_data": "<x/>", "source_url": "http://x.com", "extraction_job_id": "j1"}]
        result = await client.batch_ingest_rdf_data(items)
        assert len(result) == 1
        assert result[0].success is False

    @pytest.mark.asyncio
    async def test_batch_ingest_success(self):
        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=MagicMock(status_code=200))
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"results": [
            {"success": True, "ingestion_id": "j1", "entities_loaded": 2,
             "relationships_loaded": 0, "message": "ok"},
        ]}
        mock_http.post = AsyncMock(return_value=mock_resp)
        client = self._make_client(mock_http)
        items = [{"rdf_data": "<x/>", "source_url": "http://x.com", "extraction_job_id": "j1"}]
        result = await client.batch_ingest_rdf_data(items)
        assert len(result) == 1
        assert result[0].success is True

    @pytest.mark.asyncio
    async def test_batch_ingest_post_exception(self):
        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=MagicMock(status_code=200))
        mock_http.post = AsyncMock(side_effect=Exception("network error"))
        client = self._make_client(mock_http)
        items = [{"rdf_data": "<x/>", "source_url": "http://x.com", "extraction_job_id": "j1"}]
        result = await client.batch_ingest_rdf_data(items)
        assert result[0].success is False

    @pytest.mark.asyncio
    async def test_get_ingestion_status_success(self):
        mock_http = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "ingestion_id": "j1", "status": "completed",
            "progress_percent": 100.0, "entities_processed": 5, "entities_total": 5,
        }
        mock_http.get = AsyncMock(return_value=mock_resp)
        client = self._make_client(mock_http)
        status = await client.get_ingestion_status("j1")
        assert status.status == "completed"

    @pytest.mark.asyncio
    async def test_get_ingestion_status_exception(self):
        mock_http = AsyncMock()
        mock_http.get = AsyncMock(side_effect=Exception("timeout"))
        client = self._make_client(mock_http)
        status = await client.get_ingestion_status("j1")
        assert status.status == "error"
        assert "timeout" in status.error_message

    @pytest.mark.asyncio
    async def test_close_owned_client(self):
        mock_http = AsyncMock()
        mock_http.aclose = AsyncMock()
        client = self._make_client(mock_http)
        client._owns_client = True
        await client.close()
        mock_http.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_unowned_client_not_closed(self):
        mock_http = AsyncMock()
        mock_http.aclose = AsyncMock()
        client = self._make_client(mock_http)
        client._owns_client = False
        await client.close()
        mock_http.aclose.assert_not_called()


# ===========================================================================
# llm_extractor helpers + EntityExtractor
# ===========================================================================

class TestLLMExtractorHelpers:
    def test_effective_confidence_no_logprob(self):
        from layer2_extraction.extraction.llm_extractor import _effective_confidence
        assert _effective_confidence(0.8) == 0.8

    def test_effective_confidence_with_logprob(self):
        from layer2_extraction.extraction.llm_extractor import _effective_confidence
        result = _effective_confidence(0.8, 0.6)
        expected = 0.7 * 0.8 + 0.3 * 0.6
        assert abs(result - expected) < 1e-9

    def test_effective_confidence_clamped_high(self):
        from layer2_extraction.extraction.llm_extractor import _effective_confidence
        assert _effective_confidence(1.0, 1.0) == 1.0

    def test_effective_confidence_clamped_low(self):
        from layer2_extraction.extraction.llm_extractor import _effective_confidence
        assert _effective_confidence(0.0, 0.0) == 0.0

    def test_strict_array_tool_structure(self):
        from layer2_extraction.extraction.llm_extractor import _strict_array_tool
        tools = _strict_array_tool("fn", "desc", "items", {"type": "string"})
        assert len(tools) == 1
        assert tools[0]["type"] == "function"
        assert tools[0]["function"]["name"] == "fn"
        assert tools[0]["function"]["strict"] is True

    def test_logprob_confidence_returns_none_on_no_logprobs(self):
        from layer2_extraction.extraction.llm_extractor import _logprob_confidence_from_response
        mock_resp = MagicMock()
        mock_resp.choices[0].logprobs = None
        assert _logprob_confidence_from_response(mock_resp) is None

    def test_logprob_confidence_returns_none_on_exception(self):
        from layer2_extraction.extraction.llm_extractor import _logprob_confidence_from_response
        assert _logprob_confidence_from_response(None) is None


class TestEntityExtractor:
    def _make_extractor(self, mock_response=None):
        from layer2_extraction.extraction.llm_extractor import EntityExtractor
        mock_client = AsyncMock()
        mock_client.chat_completion_structured = AsyncMock(
            return_value=(mock_response, None)
        )
        return EntityExtractor(api_key="test", client=mock_client)

    @pytest.mark.asyncio
    async def test_extract_returns_empty_on_none_response(self):
        extractor = self._make_extractor(mock_response=None)
        result = await extractor.extract("some text")
        assert result["capabilities"] == []
        assert result["use_cases"] == []

    @pytest.mark.asyncio
    async def test_extract_capabilities_cached(self):
        from layer2_extraction.extraction.llm_extractor import EntityExtractor
        from layer2_extraction.extraction.cache import ExtractionCache
        from layer2_extraction.models.extraction_response import CapabilityExtractionResponse

        cache = ExtractionCache(redis_url=None)
        mock_response = MagicMock(spec=CapabilityExtractionResponse)
        mock_response.capabilities = []
        await cache.set("text", "extract_capabilities", mock_response, model="gpt-4o")

        mock_client = AsyncMock()
        mock_client.chat_completion_structured = AsyncMock(return_value=(None, None))
        extractor = EntityExtractor(api_key="test", client=mock_client, cache=cache)
        result = await extractor._extract_capabilities("text", "", "", 0.0)
        # Should return from cache without calling client
        mock_client.chat_completion_structured.assert_not_called()
        assert result == []

    @pytest.mark.asyncio
    async def test_extract_all_fail_raises(self):
        from layer2_extraction.extraction.llm_extractor import EntityExtractor, LLMExtractionError
        from pydantic import ValidationError

        mock_client = AsyncMock()
        mock_client.chat_completion_structured = AsyncMock(
            side_effect=ValidationError.from_exception_data("test", [])
        )
        extractor = EntityExtractor(api_key="test", client=mock_client)
        with pytest.raises((LLMExtractionError, Exception)):
            await extractor.extract("text")

    @pytest.mark.asyncio
    async def test_prepare_entities_filters_by_confidence(self):
        from layer2_extraction.extraction.llm_extractor import EntityExtractor
        from layer2_extraction.models.ontology import Capability

        extractor = EntityExtractor(api_key="test")
        c1 = Capability(id="c1", name="High Conf", description="A capability description", confidence=0.9)
        c2 = Capability(id="c2", name="Low Conf", description="A capability description", confidence=0.3)
        result = extractor._prepare_entities([c1, c2], "http://x.com", "job-1", 0.5)
        assert len(result) == 1
        assert result[0].name == "High Conf"

    @pytest.mark.asyncio
    async def test_prepare_entities_tags_job_id(self):
        from layer2_extraction.extraction.llm_extractor import EntityExtractor
        from layer2_extraction.models.ontology import Capability

        extractor = EntityExtractor(api_key="test")
        c = Capability(id="c1", name="Cap Name", description="A capability description", confidence=0.8)
        result = extractor._prepare_entities([c], "http://x.com", "job-42", 0.0)
        assert result[0].extraction_job_id == "job-42"

    @pytest.mark.asyncio
    async def test_extract_with_schema_returns_schema_instance(self):
        from layer2_extraction.extraction.llm_extractor import EntityExtractor
        from pydantic import BaseModel

        class _Schema(BaseModel):
            pass

        extractor = EntityExtractor(api_key="test")
        result = await extractor.extract_with_schema("text", _Schema)
        assert isinstance(result, _Schema)


class TestRelationshipExtractor:
    @pytest.mark.asyncio
    async def test_extract_relationships_too_few_entities(self):
        from layer2_extraction.extraction.llm_extractor import RelationshipExtractor
        extractor = RelationshipExtractor(api_key="test")
        result = await extractor.extract_relationships("text", {"capabilities": []})
        assert result == []

    @pytest.mark.asyncio
    async def test_extract_relationships_none_response(self):
        from layer2_extraction.extraction.llm_extractor import RelationshipExtractor
        from layer2_extraction.models.ontology import Capability

        mock_client = AsyncMock()
        mock_client.chat_completion_structured = AsyncMock(return_value=(None, None))
        extractor = RelationshipExtractor(api_key="test", client=mock_client)
        caps = [
            Capability(id="c1", name="Cap One", description="A capability description", confidence=0.8),
            Capability(id="c2", name="Cap Two", description="A capability description", confidence=0.8),
        ]
        result = await extractor.extract_relationships("text", {"capabilities": caps})
        assert result == []

    @pytest.mark.asyncio
    async def test_extract_relationships_with_schema(self):
        from layer2_extraction.extraction.llm_extractor import RelationshipExtractor
        from pydantic import BaseModel

        class _Schema(BaseModel):
            pass

        extractor = RelationshipExtractor(api_key="test")
        result = await extractor.extract_relationships_with_schema("text", _Schema)
        assert isinstance(result, _Schema)
