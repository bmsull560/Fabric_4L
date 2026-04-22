#!/usr/bin/env python3
"""Comprehensive audit and fix of all pack variable references."""

import json
import re
from pathlib import Path

def get_formula_variables(formula):
    """Extract variable names from formula expression."""
    return set(formula.get('expression', {}).get('variables', []))


def get_pack_prefix(pack_name, existing_variables):
    """Derive pack prefix from existing variable IDs (e.g., 'ai-var-001' -> 'ai').
    
    Falls back to first two chars of pack name if no variables exist.
    """
    if existing_variables:
        # Extract prefix from first existing variable ID
        first_var_id = existing_variables[0].get('variable_id', '')
        if '-var-' in first_var_id:
            return first_var_id.split('-var-')[0]
    # Fallback: use pack name abbreviation
    return pack_name[:2].replace('-', '')

def main():
    packs_dir = Path('packs')
    manifest_path = packs_dir / 'pack-manifest.json'

    with open(manifest_path, encoding='utf-8') as f:
        manifest = json.load(f)

    total_added = 0

    for pack in manifest['packs']:
        pack_id = pack['pack_id']
        pack_name = re.sub(r'-v\d+$', '', pack_id)  # Strip version suffix like pack loader
        pack_path = packs_dir / pack_name

        print(f"\n{'='*60}")
        print(f"Processing: {pack_id}")
        print('='*60)

        # Load variables
        variables_path = pack_path / 'variables.json'
        with open(variables_path, encoding='utf-8') as f:
            var_data = json.load(f)
        variables = var_data['variables']

        # Load formulas
        formulas_path = pack_path / 'formulas.json'
        with open(formulas_path, encoding='utf-8') as f:
            formula_data = json.load(f)
        formulas = formula_data['formulas']

        # Validate: check for formula references to non-existent variables
        valid_formula_ids = {f['formula_id'] for f in formulas}
        referenced_vars = set()
        for formula in formulas:
            refs = get_formula_variables(formula)
            # Validate each referenced formula exists
            for ref_formula_id in formula.get('expression', {}).get('sub_formulas', []):
                if ref_formula_id not in valid_formula_ids:
                    print(f"  ⚠️  Formula '{formula['formula_id']}' references non-existent sub-formula '{ref_formula_id}'")
            referenced_vars.update(refs)

        # Get existing variable names
        existing_vars = {v['variable_name'] for v in variables}

        # Find missing variables
        missing = referenced_vars - existing_vars

        if missing:
            print(f"Missing variables: {missing}")

            # Add placeholder variables for missing ones
            next_id = max((int(v['variable_id'].split('-')[-1]) for v in variables), default=0) + 1
            pack_prefix = get_pack_prefix(pack_name, variables)

            for var_name in missing:
                var = {
                    "variable_id": f"{pack_prefix}-var-{next_id:03d}",
                    "variable_name": var_name,
                    "display_name": var_name.replace('_', ' '),
                    "description": f"Auto-generated variable for {var_name}",
                    "data_type": "CURRENCY",
                    "unit_of_measure": "USD",
                    "valid_range": {"min": 0, "max": 100000000},
                    "default_value": 1000000,
                    "source_type": "USER_INPUT",
                    "validation_rules": [{"type": "range", "min": 0, "max": 100000000}],
                    "tags": ["auto-generated"],
                    "used_in_formulas": [],
                    "canonicalName": var_name,
                    "name": var_name.replace('_', ' ')
                }

                # Find which formulas use this variable
                for formula in formulas:
                    if var_name in get_formula_variables(formula):
                        var['used_in_formulas'].append(formula['formula_id'])

                variables.append(var)
                next_id += 1
                total_added += 1
                print(f"  Added: {var_name} ({var['variable_id']})")

            # Save variables.json
            with open(variables_path, 'w') as f:
                json.dump(var_data, f, indent=2)

            # Update manifest count
            pack['variable_count'] = len(variables)
            print(f"  Updated count: {pack['variable_count']} variables")
        else:
            print("✅ All formula references valid")

    # Recalculate totals
    total_vars = sum(p['variable_count'] for p in manifest['packs'])
    manifest['statistics']['total_variables'] = total_vars

    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"\n{'='*60}")
    print(f"SUMMARY: Added {total_added} variables across all packs")
    print(f"Total variables in ecosystem: {total_vars}")
    print('='*60)

if __name__ == '__main__':
    main()
