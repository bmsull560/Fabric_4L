#!/usr/bin/env python3
import os
paths = [
    "c:/Users/BBB/Fabric_4L/signoff-evidence/phase-07-frontend/frontend-unit-tests.txt",
    "c:/Users/BBB/Fabric_4L/signoff-evidence/phase-04-contracts/contract-static-tests.txt",
]
for p in paths:
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            content = f.read()
        print(f"=== {os.path.basename(p)} ===")
        print(content[:1500])
        print()
    else:
        print(f"=== {os.path.basename(p)} === NOT FOUND")
