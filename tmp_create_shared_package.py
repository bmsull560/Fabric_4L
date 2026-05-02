import os, shutil, hashlib

TARGET = "packages/shared/src/value_fabric/shared"
SOURCES = [
    ("value-fabric/shared", "vf"),
    ("shared", "root"),
]

def file_hash(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

os.makedirs(TARGET, exist_ok=True)

# Track which files we've handled
handled = set()

# First pass: copy from vf (preferred base for overlapping modules)
for src_dir, label in SOURCES:
    for root, dirs, files in os.walk(src_dir):
        for f in files:
            if f.endswith(".pyc"):
                continue
            src_path = os.path.join(root, f)
            rel = os.path.relpath(src_path, src_dir)
            dst_path = os.path.join(TARGET, rel)
            
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            
            if rel in handled:
                # File exists from previous source; check if different
                if file_hash(src_path) != file_hash(dst_path):
                    print(f"DIFF: {rel} (will need merge)")
                continue
            
            shutil.copy2(src_path, dst_path)
            handled.add(rel)

print(f"Created {TARGET} with {len(handled)} files")
