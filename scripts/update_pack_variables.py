#!/usr/bin/env python3
"""Update pack variables.json files with canonicalName and name fields."""

import json
from pathlib import Path

def main():
    packs_dir = Path('packs')
    manifest_path = packs_dir / 'pack-manifest.json'

    # Load manifest
    with open(manifest_path) as f:
        manifest = json.load(f)

    # Update each pack's variables.json
    for pack in manifest['packs']:
        pack_id = pack['pack_id']
        pack_name = pack_id.replace('-v1', '')
        variables_path = packs_dir / pack_name / 'variables.json'

        with open(variables_path) as f:
            data = json.load(f)

        variables = data['variables']
        actual_count = len(variables)

        # Validate: collect all invalid records before mutation
        invalid_records = []
        for idx, var in enumerate(variables):
            missing_fields = []
            if 'variable_name' not in var and 'canonicalName' not in var:
                missing_fields.append('variable_name or canonicalName')
            if missing_fields:
                invalid_records.append({
                    'index': idx,
                    'record': var,
                    'missing_fields': missing_fields
                })

        if invalid_records:
            raise ValueError(
                f"Found {len(invalid_records)} variables missing required fields:\n" +
                "\n".join(
                    f"  [record {r['index']}] missing: {', '.join(r['missing_fields'])}"
                    for r in invalid_records[:10]  # Show first 10
                ) +
                (f"\n  ... and {len(invalid_records) - 10} more" if len(invalid_records) > 10 else "")
            )

        # Add canonicalName and name fields to each variable
        for var in variables:
            if 'canonicalName' not in var:
                var['canonicalName'] = var['variable_name']
            if 'name' not in var:
                var['name'] = var.get('display_name', var['variable_name'])

        # Save back
        with open(variables_path, 'w') as f:
            json.dump(data, f, indent=2)

        manifest_count = pack['variable_count']
        print(f'{pack_id}: {actual_count} variables (manifest says {manifest_count})')

        # Update manifest count
        pack['variable_count'] = actual_count

    # Recalculate totals
    total_vars = sum(p['variable_count'] for p in manifest['packs'])
    manifest['statistics']['total_variables'] = total_vars

    # Save manifest
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f'\nUpdated manifest: {total_vars} total variables')

if __name__ == '__main__':
    main()
