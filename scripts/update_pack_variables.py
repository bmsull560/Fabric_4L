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
