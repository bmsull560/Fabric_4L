import yaml
with open(".fabric/prod-gates.policy.yaml") as f:
    data = yaml.safe_load(f)
for name, p in data["profiles"].items():
    print(f"{name}: {len(p['gates'])} gates")
