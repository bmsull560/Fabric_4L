import subprocess
import os

# Get list of deleted files from git
result = subprocess.run(
    ['git', '-C', 'c:/Users/BBB/Fabric_4L', 'status', '--short'],
    capture_output=True, text=True
)

deleted_files = []
for line in result.stdout.split('\n'):
    if line.startswith(' D value_fabric/'):
        deleted_files.append(line[3:])

# Check which deleted files have equivalents in services/
no_equivalent = []
have_equivalent = []

for f in deleted_files:
    if not f.endswith('.py'):
        continue
    # Try to find equivalent in services
    parts = f.replace('value_fabric/', '').split('/')
    # Map layer names
    layer_map = {
        'layer1': 'layer1-ingestion',
        'layer1_ingestion': 'layer1-ingestion',
        'layer2': 'layer2-extraction',
        'layer3': 'layer3-knowledge',
        'layer3_knowledge': 'layer3-knowledge',
        'layer4': 'layer4-agents',
        'layer5': 'layer5-ground-truth',
        'layer5_ground_truth': 'layer5-ground-truth',
        'layer6': 'layer6-benchmarks',
        'layer6_benchmarks': 'layer6-benchmarks',
    }
    
    if parts[0] in layer_map:
        service_dir = f"services/{layer_map[parts[0]]}/src"
        # Try different equivalent paths
        equiv_paths = [
            '/'.join([service_dir] + parts[1:]),
        ]
        found = False
        for ep in equiv_paths:
            full_path = f"c:/Users/BBB/Fabric_4L/{ep}"
            if os.path.exists(full_path):
                have_equivalent.append((f, ep))
                found = True
                break
        if not found:
            no_equivalent.append(f)
    else:
        no_equivalent.append(f)

print(f"Deleted files with equivalents in services/: {len(have_equivalent)}")
for orig, equiv in have_equivalent[:20]:
    print(f"  {orig} -> {equiv}")
if len(have_equivalent) > 20:
    print(f"  ... and {len(have_equivalent) - 20} more")

print(f"\nDeleted files with NO equivalents in services/: {len(no_equivalent)}")
for f in no_equivalent[:50]:
    print(f"  {f}")
if len(no_equivalent) > 50:
    print(f"  ... and {len(no_equivalent) - 50} more")
