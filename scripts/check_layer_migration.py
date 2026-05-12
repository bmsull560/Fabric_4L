import os

layers = [
    ('layer1', 'layer1-ingestion'),
    ('layer2', 'layer2-extraction'),
    ('layer3', 'layer3-knowledge'),
    ('layer5', 'layer5-ground-truth'),
]

for vf_layer, service_dir in layers:
    vf_root = f'c:/Users/BBB/Fabric_4L/value_fabric/{vf_layer}'
    svc_root = f'c:/Users/BBB/Fabric_4L/services/{service_dir}/src'
    
    if not os.path.exists(vf_root):
        print(f"{vf_layer}: value_fabric dir missing")
        continue
    
    vf_count = 0
    for _, _, files in os.walk(vf_root):
        vf_count += sum(1 for f in files if f.endswith('.py'))
    
    svc_count = 0
    if os.path.exists(svc_root):
        for _, _, files in os.walk(svc_root):
            svc_count += sum(1 for f in files if f.endswith('.py'))
    
    print(f"{vf_layer}: {vf_count} files in value_fabric, {svc_count} files in services")
