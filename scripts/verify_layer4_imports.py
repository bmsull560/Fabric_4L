import sys

# Simulate the namespace package path
sys.path.insert(0, 'c:/Users/BBB/Fabric_4L/services/layer4-agents/src')

# Test direct imports
try:
    from observability import Layer4EventContext, Layer4LifecycleLogger
    print("Direct observability import: OK")
except Exception as e:
    print(f"Direct observability import: FAIL - {e}")

# Test shim imports
try:
    import value_fabric.layer4
    print(f"value_fabric.layer4.__path__: {value_fabric.layer4.__path__}")
    from value_fabric.layer4.observability import Layer4EventContext as LEC2
    print("Shim observability import: OK")
except Exception as e:
    print(f"Shim observability import: FAIL - {e}")

# Test database_facade
try:
    from database_facade import validate_tenant_id
    print("Direct database_facade import: OK")
except Exception as e:
    print(f"Direct database_facade import: FAIL - {e}")

# Test database (should be in services/src)
try:
    import database
    print("Direct database import: OK")
except Exception as e:
    print(f"Direct database import: FAIL - {e}")
