# Contract Test Directory Overlap Inventory

Generated on 2026-05-12 to compare `tests/contract/` and `tests/contracts/` before consolidation.

## Basename overlap

- `test_entity_contract.py`
- `test_layer3_contract.py`
- `test_layer5_contract.py`

## Function-name overlap (same basename in both directories)

### `test_entity_contract.py`
All `test_` function names overlap between both directories.

### `test_layer3_contract.py`
No `test_` functions are defined in either file (module-level schema/fixture scaffolding only).

### `test_layer5_contract.py`
No `test_` functions are defined in either file (module-level schema/fixture scaffolding only).

## Unique modules in `tests/contracts/` moved to canonical location

- `tests/contracts/test_retention_deletion_contract.py` → `tests/contract/test_retention_deletion_contract.py`
- `tests/contracts/gate/test_phase1_contracts.py` → `tests/contract/gate/test_phase1_contracts.py`
