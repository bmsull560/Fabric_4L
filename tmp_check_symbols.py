import ast, os

def get_exports(init_path):
    with open(init_path, 'r', encoding='utf-8', errors='ignore') as f:
        tree = ast.parse(f.read())
    exports = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                exports.append((node.module, alias.name, alias.asname))
    return exports

def get_file_symbols(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        tree = ast.parse(f.read())
    symbols = set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            symbols.add(node.name)
    return symbols

root_exports = get_exports('shared/identity/__init__.py')
vf_exports = get_exports('value-fabric/shared/identity/__init__.py')

print("=== ROOT-ONLY EXPORTS ===")
root_symbols = {e[1] for e in root_exports}
vf_symbols = {e[1] for e in vf_exports}
only_root = root_symbols - vf_symbols
print(only_root)

# Check if root-only symbols exist in VF files
print("\n=== CHECKING ROOT-ONLY SYMBOLS IN VF FILES ===")
vf_dir = 'value-fabric/shared/identity'
all_vf_symbols = {}
for f in os.listdir(vf_dir):
    if f.endswith('.py') and f != '__init__.py':
        syms = get_file_symbols(os.path.join(vf_dir, f))
        all_vf_symbols[f] = syms

for sym in sorted(only_root):
    found = False
    for f, syms in all_vf_symbols.items():
        if sym in syms:
            print(f"  {sym}: found in {f}")
            found = True
            break
    if not found:
        print(f"  {sym}: NOT FOUND in any VF file")
