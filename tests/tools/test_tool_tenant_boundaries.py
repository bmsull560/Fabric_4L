"""
Tool Invocation Boundary Tests (Suite 7).

Verifies that all agent tools enforce tenant boundaries and cannot be used
to access or modify data from other tenants.

Test Strategy:
- Verify all tools require tenant context
- Test cross-tenant tool invocation attempts
- Validate tool parameter sanitization
- Test tool result filtering by tenant
- Verify tool audit logging includes tenant_id

Critical Security Property:
    Tool invoked by tenant A MUST NOT access tenant B's data
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4
from fastapi import HTTPException, status

from value_fabric.shared.identity.context import RequestContext
from value_fabric.layer4_agents.src.tools.registry import ToolRegistry, ToolCategory


# ═══════════════════════════════════════════════════════════════════════════
# Test Suite: Tool Registration and Discovery
# ═══════════════════════════════════════════════════════════════════════════


class TestToolRegistration:
    """Verify tool registration enforces tenant scoping."""
    
    def test_all_tools_require_tenant_context_parameter(self):
        """All registered tools must accept tenant_id parameter.
        
        Rationale: Tools without tenant_id cannot enforce tenant isolation.
        """
        registry = ToolRegistry()
        
        for tool_name, tool_func in registry.get_all_tools().items():
            # Check function signature
            import inspect
            sig = inspect.signature(tool_func)
            
            # Must have tenant_id parameter
            assert "tenant_id" in sig.parameters, \
                f"Tool {tool_name} missing tenant_id parameter"
            
            # tenant_id should be UUID type
            param = sig.parameters["tenant_id"]
            assert param.annotation in (UUID, "UUID", UUID | None), \
                f"Tool {tool_name} tenant_id should be UUID type"
    
    def test_tool_metadata_includes_tenant_scoping_flag(self):
        """Tool metadata must indicate if tool is tenant-scoped.
        
        Rationale: Operators need to know which tools access tenant data.
        """
        registry = ToolRegistry()
        
        for tool_name in registry.get_all_tools().keys():
            metadata = registry.get_tool_metadata(tool_name)
            
            assert "tenant_scoped" in metadata, \
                f"Tool {tool_name} missing tenant_scoped metadata"
            
            # Most tools should be tenant-scoped
            if tool_name not in ["health_check", "list_tools"]:
                assert metadata["tenant_scoped"] is True, \
                    f"Tool {tool_name} should be tenant-scoped"
    
    def test_tool_discovery_filtered_by_tenant_permissions(self):
        """Tool discovery must be filtered by tenant permissions.
        
        Rationale: Tenants should only see tools they have permission to use.
        """
        registry = ToolRegistry()
        
        # Tenant with limited permissions
        context = RequestContext(
            tenant_id=uuid4(),
            user_id=uuid4(),
            permissions=frozenset(["read"])
        )
        
        available_tools = registry.get_available_tools(context)
        
        # Should not include admin tools
        admin_tools = ["delete_tenant", "suspend_tenant", "grant_permission"]
        for admin_tool in admin_tools:
            assert admin_tool not in available_tools, \
                f"Non-admin user should not see {admin_tool}"


# ═══════════════════════════════════════════════════════════════════════════
# Test Suite: Tool Invocation Tenant Isolation
# ═══════════════════════════════════════════════════════════════════════════


class TestToolInvocationIsolation:
    """Verify tool invocations enforce tenant boundaries."""
    
    @pytest.mark.asyncio
    async def test_tool_cannot_access_another_tenants_data(self):
        """Tool invoked by tenant A must not access tenant B's data.
        
        Attack scenario: Tenant A tries to read tenant B's entities.
        """
        from value_fabric.layer4_agents.src.tools.knowledge import get_entity
        
        tenant_a = uuid4()
        tenant_b = uuid4()
        entity_id = "entity-123"
        
        # Mock database to return entity for tenant B
        with patch("value_fabric.layer4_agents.src.tools.knowledge.db_session") as mock_db:
            mock_result = MagicMock()
            mock_result.tenant_id = tenant_b
            mock_result.id = entity_id
            mock_result.name = "Tenant B Entity"
            
            mock_db.query().filter().first.return_value = mock_result
            
            # Tenant A tries to get entity
            result = await get_entity(
                tenant_id=tenant_a,
                entity_id=entity_id
            )
            
            # Should return None (not found) rather than tenant B's entity
            assert result is None or result["tenant_id"] == str(tenant_a)
    
    @pytest.mark.asyncio
    async def test_tool_cannot_modify_another_tenants_data(self):
        """Tool invoked by tenant A must not modify tenant B's data.
        
        Attack scenario: Tenant A tries to update tenant B's entity.
        """
        from value_fabric.layer4_agents.src.tools.knowledge import update_entity
        
        tenant_a = uuid4()
        tenant_b = uuid4()
        entity_id = "entity-123"
        
        # Mock database
        with patch("value_fabric.layer4_agents.src.tools.knowledge.db_session") as mock_db:
            # Entity belongs to tenant B
            mock_entity = MagicMock()
            mock_entity.tenant_id = tenant_b
            mock_entity.id = entity_id
            
            mock_db.query().filter().first.return_value = mock_entity
            
            # Tenant A tries to update
            with pytest.raises(HTTPException) as exc_info:
                await update_entity(
                    tenant_id=tenant_a,
                    entity_id=entity_id,
                    updates={"name": "Malicious Update"}
                )
            
            # Should raise 404 (not found) or 403 (forbidden)
            assert exc_info.value.status_code in (
                status.HTTP_404_NOT_FOUND,
                status.HTTP_403_FORBIDDEN
            )
    
    @pytest.mark.asyncio
    async def test_tool_cannot_delete_another_tenants_data(self):
        """Tool invoked by tenant A must not delete tenant B's data.
        
        Attack scenario: Tenant A tries to delete tenant B's entity.
        """
        from value_fabric.layer4_agents.src.tools.knowledge import delete_entity
        
        tenant_a = uuid4()
        tenant_b = uuid4()
        entity_id = "entity-123"
        
        # Mock database
        with patch("value_fabric.layer4_agents.src.tools.knowledge.db_session") as mock_db:
            # Entity belongs to tenant B
            mock_entity = MagicMock()
            mock_entity.tenant_id = tenant_b
            
            mock_db.query().filter().first.return_value = mock_entity
            
            # Tenant A tries to delete
            with pytest.raises(HTTPException) as exc_info:
                await delete_entity(
                    tenant_id=tenant_a,
                    entity_id=entity_id
                )
            
            # Should raise 404 or 403
            assert exc_info.value.status_code in (
                status.HTTP_404_NOT_FOUND,
                status.HTTP_403_FORBIDDEN
            )
            
            # Verify delete was not called
            mock_db.delete.assert_not_called()


# ═══════════════════════════════════════════════════════════════════════════
# Test Suite: Tool Parameter Validation
# ═══════════════════════════════════════════════════════════════════════════


class TestToolParameterValidation:
    """Verify tool parameters are validated and sanitized."""
    
    @pytest.mark.asyncio
    async def test_tool_rejects_sql_injection_in_parameters(self):
        """Tool parameters with SQL injection attempts must be rejected.
        
        Attack scenario: Tenant provides SQL in entity_id parameter.
        """
        from value_fabric.layer4_agents.src.tools.knowledge import get_entity
        
        tenant_id = uuid4()
        malicious_entity_id = "' OR '1'='1"
        
        with pytest.raises(ValueError, match="Invalid.*entity_id"):
            await get_entity(
                tenant_id=tenant_id,
                entity_id=malicious_entity_id
            )
    
    @pytest.mark.asyncio
    async def test_tool_rejects_path_traversal_in_parameters(self):
        """Tool parameters with path traversal attempts must be rejected.
        
        Attack scenario: Tenant provides path traversal in file parameter.
        """
        from value_fabric.layer4_agents.src.tools.files import read_file
        
        tenant_id = uuid4()
        malicious_path = "../../etc/passwd"
        
        with pytest.raises(ValueError, match="Invalid.*path"):
            await read_file(
                tenant_id=tenant_id,
                file_path=malicious_path
            )
    
    @pytest.mark.asyncio
    async def test_tool_rejects_oversized_parameters(self):
        """Tool parameters exceeding size limits must be rejected.
        
        Attack scenario: Tenant provides huge parameter to DoS.
        """
        from value_fabric.layer4_agents.src.tools.knowledge import search_entities
        
        tenant_id = uuid4()
        huge_query = "A" * 100000  # 100KB query
        
        with pytest.raises(ValueError, match="Query too large"):
            await search_entities(
                tenant_id=tenant_id,
                query=huge_query
            )
    
    @pytest.mark.asyncio
    async def test_tool_validates_tenant_id_format(self):
        """Tool must validate tenant_id is valid UUID.
        
        Rationale: Invalid tenant_id could cause downstream errors.
        """
        from value_fabric.layer4_agents.src.tools.knowledge import get_entity
        
        invalid_tenant_id = "not-a-uuid"
        
        with pytest.raises((ValueError, TypeError)):
            await get_entity(
                tenant_id=invalid_tenant_id,  # type: ignore
                entity_id="entity-123"
            )


# ═══════════════════════════════════════════════════════════════════════════
# Test Suite: Tool Result Filtering
# ═══════════════════════════════════════════════════════════════════════════


class TestToolResultFiltering:
    """Verify tool results are filtered by tenant."""
    
    @pytest.mark.asyncio
    async def test_search_tool_only_returns_tenant_results(self):
        """Search tool must only return results for requesting tenant.
        
        Rationale: Search across all tenants would leak data.
        """
        from value_fabric.layer4_agents.src.tools.knowledge import search_entities
        
        tenant_a = uuid4()
        tenant_b = uuid4()
        
        # Mock database with mixed results
        with patch("value_fabric.layer4_agents.src.tools.knowledge.db_session") as mock_db:
            mock_results = [
                MagicMock(tenant_id=tenant_a, id="a1", name="Tenant A Entity 1"),
                MagicMock(tenant_id=tenant_b, id="b1", name="Tenant B Entity 1"),
                MagicMock(tenant_id=tenant_a, id="a2", name="Tenant A Entity 2"),
            ]
            
            mock_db.query().filter().all.return_value = mock_results
            
            # Tenant A searches
            results = await search_entities(
                tenant_id=tenant_a,
                query="Entity"
            )
            
            # Should only get tenant A results
            assert len(results) == 2
            assert all(r["tenant_id"] == str(tenant_a) for r in results)
    
    @pytest.mark.asyncio
    async def test_list_tool_only_returns_tenant_items(self):
        """List tool must only return items for requesting tenant.
        
        Rationale: Listing all items would leak data.
        """
        from value_fabric.layer4_agents.src.tools.knowledge import list_entities
        
        tenant_a = uuid4()
        tenant_b = uuid4()
        
        # Mock database
        with patch("value_fabric.layer4_agents.src.tools.knowledge.db_session") as mock_db:
            mock_results = [
                MagicMock(tenant_id=tenant_a, id="a1"),
                MagicMock(tenant_id=tenant_a, id="a2"),
                MagicMock(tenant_id=tenant_b, id="b1"),
            ]
            
            mock_db.query().filter().all.return_value = mock_results
            
            # Tenant A lists
            results = await list_entities(tenant_id=tenant_a)
            
            # Should only get tenant A items
            assert len(results) == 2
            assert all(r["tenant_id"] == str(tenant_a) for r in results)
    
    @pytest.mark.asyncio
    async def test_aggregate_tool_only_aggregates_tenant_data(self):
        """Aggregate tool must only aggregate data for requesting tenant.
        
        Rationale: Aggregating across tenants would leak statistics.
        """
        from value_fabric.layer4_agents.src.tools.analytics import count_entities
        
        tenant_a = uuid4()
        tenant_b = uuid4()
        
        # Mock database
        with patch("value_fabric.layer4_agents.src.tools.analytics.db_session") as mock_db:
            # Total count includes both tenants
            mock_db.query().count.return_value = 100
            
            # Filtered count for tenant A
            mock_db.query().filter().count.return_value = 30
            
            # Tenant A gets count
            count = await count_entities(tenant_id=tenant_a)
            
            # Should only count tenant A entities
            assert count == 30


# ═══════════════════════════════════════════════════════════════════════════
# Test Suite: Tool Audit Logging
# ═══════════════════════════════════════════════════════════════════════════


class TestToolAuditLogging:
    """Verify tool invocations are audited with tenant context."""
    
    @pytest.mark.asyncio
    async def test_tool_invocation_logged_with_tenant_id(self):
        """Tool invocations must be logged with tenant_id.
        
        Rationale: Audit trail must show which tenant invoked which tool.
        """
        from value_fabric.layer4_agents.src.tools.knowledge import get_entity
        from shared.audit import emit_audit_event
        
        tenant_id = uuid4()
        entity_id = "entity-123"
        
        with patch("value_fabric.layer4_agents.src.tools.knowledge.emit_audit_event") as mock_audit:
            with patch("value_fabric.layer4_agents.src.tools.knowledge.db_session"):
                await get_entity(
                    tenant_id=tenant_id,
                    entity_id=entity_id
                )
                
                # Verify audit event emitted
                assert mock_audit.called
                call_kwargs = mock_audit.call_args.kwargs
                
                # Must include tenant_id
                assert call_kwargs.get("tenant_id") == tenant_id
                assert call_kwargs.get("resource_type") == "entity"
                assert call_kwargs.get("resource_id") == entity_id
    
    @pytest.mark.asyncio
    async def test_failed_tool_invocation_logged(self):
        """Failed tool invocations must be logged.
        
        Rationale: Failed attempts may indicate attack.
        """
        from value_fabric.layer4_agents.src.tools.knowledge import delete_entity
        
        tenant_a = uuid4()
        tenant_b = uuid4()
        
        with patch("value_fabric.layer4_agents.src.tools.knowledge.emit_audit_event") as mock_audit:
            with patch("value_fabric.layer4_agents.src.tools.knowledge.db_session") as mock_db:
                # Entity belongs to tenant B
                mock_entity = MagicMock()
                mock_entity.tenant_id = tenant_b
                mock_db.query().filter().first.return_value = mock_entity
                
                # Tenant A tries to delete
                try:
                    await delete_entity(
                        tenant_id=tenant_a,
                        entity_id="entity-123"
                    )
                except HTTPException:
                    pass
                
                # Verify failure logged
                assert mock_audit.called
                call_kwargs = mock_audit.call_args.kwargs
                assert call_kwargs.get("outcome") == "failure"
                assert call_kwargs.get("tenant_id") == tenant_a


# ═══════════════════════════════════════════════════════════════════════════
# Test Suite: Tool Permission Enforcement
# ═══════════════════════════════════════════════════════════════════════════


class TestToolPermissionEnforcement:
    """Verify tools enforce permission requirements."""
    
    @pytest.mark.asyncio
    async def test_write_tool_requires_write_permission(self):
        """Write tools must require write permission.
        
        Rationale: Read-only users should not be able to modify data.
        """
        from value_fabric.layer4_agents.src.tools.knowledge import update_entity
        
        # Context with only read permission
        context = RequestContext(
            tenant_id=uuid4(),
            user_id=uuid4(),
            permissions=frozenset(["read"])
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await update_entity(
                tenant_id=context.tenant_id,
                entity_id="entity-123",
                updates={"name": "New Name"},
                context=context
            )
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    
    @pytest.mark.asyncio
    async def test_delete_tool_requires_delete_permission(self):
        """Delete tools must require delete permission.
        
        Rationale: Write permission should not grant delete access.
        """
        from value_fabric.layer4_agents.src.tools.knowledge import delete_entity
        
        # Context with read and write, but not delete
        context = RequestContext(
            tenant_id=uuid4(),
            user_id=uuid4(),
            permissions=frozenset(["read", "write"])
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await delete_entity(
                tenant_id=context.tenant_id,
                entity_id="entity-123",
                context=context
            )
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    
    @pytest.mark.asyncio
    async def test_admin_tool_requires_admin_permission(self):
        """Admin tools must require admin permission.
        
        Rationale: Regular users should not access admin tools.
        """
        from value_fabric.layer4_agents.src.tools.admin import suspend_tenant
        
        # Context without admin permission
        context = RequestContext(
            tenant_id=uuid4(),
            user_id=uuid4(),
            permissions=frozenset(["read", "write", "delete"])
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await suspend_tenant(
                tenant_id=uuid4(),
                context=context
            )
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


# ═══════════════════════════════════════════════════════════════════════════
# Test Suite: Tool Chaining and Composition
# ═══════════════════════════════════════════════════════════════════════════


class TestToolChaining:
    """Verify tool chaining maintains tenant isolation."""
    
    @pytest.mark.asyncio
    async def test_chained_tools_maintain_tenant_context(self):
        """Chained tools must maintain tenant context.
        
        Rationale: Tool A calling tool B must pass tenant_id.
        """
        from value_fabric.layer4_agents.src.tools.workflows import analyze_entity
        
        tenant_id = uuid4()
        entity_id = "entity-123"
        
        with patch("value_fabric.layer4_agents.src.tools.knowledge.get_entity") as mock_get:
            with patch("value_fabric.layer4_agents.src.tools.analytics.compute_metrics") as mock_compute:
                mock_get.return_value = {"id": entity_id, "tenant_id": str(tenant_id)}
                mock_compute.return_value = {"score": 0.95}
                
                # analyze_entity calls get_entity then compute_metrics
                await analyze_entity(
                    tenant_id=tenant_id,
                    entity_id=entity_id
                )
                
                # Verify both tools called with tenant_id
                mock_get.assert_called_with(tenant_id=tenant_id, entity_id=entity_id)
                mock_compute.assert_called_with(tenant_id=tenant_id, entity_data=mock_get.return_value)
    
    @pytest.mark.asyncio
    async def test_tool_cannot_escalate_permissions_via_chaining(self):
        """Tool chaining must not allow permission escalation.
        
        Attack scenario: Read-only tool chains to write tool.
        """
        from value_fabric.layer4_agents.src.tools.workflows import read_and_update
        
        # Context with only read permission
        context = RequestContext(
            tenant_id=uuid4(),
            user_id=uuid4(),
            permissions=frozenset(["read"])
        )
        
        # read_and_update tries to call update_entity
        with pytest.raises(HTTPException) as exc_info:
            await read_and_update(
                tenant_id=context.tenant_id,
                entity_id="entity-123",
                context=context
            )
        
        # Should fail at permission check
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
