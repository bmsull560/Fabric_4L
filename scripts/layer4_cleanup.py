import os
import shutil

# 1. Move observability.py
shutil.move(
    'c:/Users/BBB/Fabric_4L/value_fabric/layer4/observability.py',
    'c:/Users/BBB/Fabric_4L/services/layer4-agents/src/observability.py'
)
print("Moved observability.py")

# 2. Move database_facade.py
shutil.move(
    'c:/Users/BBB/Fabric_4L/value_fabric/layer4/database_facade.py',
    'c:/Users/BBB/Fabric_4L/services/layer4-agents/src/database_facade.py'
)
print("Moved database_facade.py")

# 3. Delete database.py (canonical exists in services)
os.remove('c:/Users/BBB/Fabric_4L/value_fabric/layer4/database.py')
print("Deleted value_fabric/layer4/database.py")

# 4. Move test file
shutil.move(
    'c:/Users/BBB/Fabric_4L/value_fabric/layer4/tests/test_observability_schema.py',
    'c:/Users/BBB/Fabric_4L/services/layer4-agents/tests/unit/test_observability_schema_legacy.py'
)
print("Moved test_observability_schema.py")

# 5. Remove empty tests directory
os.rmdir('c:/Users/BBB/Fabric_4L/value_fabric/layer4/tests')
print("Removed empty value_fabric/layer4/tests/")

print("Done.")
