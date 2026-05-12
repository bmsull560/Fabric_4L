#!/usr/bin/env python3
"""Fail CI if deprecated k8s/alertmanager.yml reappears."""
from pathlib import Path
import sys

path = Path("k8s/alertmanager.yml")
if path.exists():
    print("ERROR: Deprecated manifest detected: k8s/alertmanager.yml")
    print("Use canonical manifests: k8s/base/monitoring-alertmanager.yml (prod overlay) and k8s/monitoring-alertmanager.yml (compatibility).")
    sys.exit(1)
print("OK: Deprecated k8s/alertmanager.yml is absent.")
