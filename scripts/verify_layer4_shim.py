import sys
sys.path.insert(0, 'c:/Users/BBB/Fabric_4L/packages/shared/src')
sys.path.insert(0, 'c:/Users/BBB/Fabric_4L')

try:
    from value_fabric.layer4.observability import Layer4EventContext
    print("Shim observability import: OK")
except Exception as e:
    print(f"Shim observability import: FAIL - {e}")

try:
    from value_fabric.layer4.database_facade import validate_tenant_id
    print("Shim database_facade import: OK")
except Exception as e:
    print(f"Shim database_facade import: FAIL - {e}")

try:
    from value_fabric.layer4.database import get_db_from_context
    print("Shim database import: OK")
except Exception as e:
    print(f"Shim database import: FAIL - {e}")
