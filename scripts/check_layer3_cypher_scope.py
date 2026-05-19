#!/usr/bin/env python3
from __future__ import annotations
import argparse, ast, json, re, sys
from dataclasses import dataclass
from pathlib import Path

ROOTS=("services/layer3-knowledge/src/api/routes","services/layer3-knowledge/src/services")
MARKER="strict-scoped-query-execution"
SAFE_EXECUTION_CALL_MARKERS=("run_scoped_query","run_validated_query","execute_tenant_query","execute_tenant_cypher")
INV_PATH="services/layer3-knowledge/security/layer3_cypher_runtime_inventory.json"
RUN_PAT=re.compile(r"\.(run|execute_query)\s*\(")
DYNAMIC_PATTERNS={"target_label":re.compile(r"target_label"),"rel_type":re.compile(r"rel_type|relationship_types?"),"sort_clause":re.compile(r"sort_(?:by|order|dir)|ORDER BY \{")}

@dataclass(frozen=True)
class Entry:
    key:str; path:str; line:int; function:str; marker:bool; dynamic:list[str]

def discover(root:Path)->list[Entry]:
    entries=[]
    for rp in ROOTS:
        for p in sorted((root/rp).rglob('*.py')):
            text=p.read_text(encoding='utf-8')
            lines=text.splitlines()
            try: tree=ast.parse(text)
            except SyntaxError: continue
            for n in ast.walk(tree):
                if not isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)): continue
                seg=ast.get_source_segment(text,n) or ''
                if not RUN_PAT.search(seg): continue
                lineno=n.lineno
                window='\n'.join(lines[max(0,lineno-8):min(len(lines),lineno+20)])
                marker=(MARKER in window) or any(m in seg for m in SAFE_EXECUTION_CALL_MARKERS)
                dyn=[k for k,pat in DYNAMIC_PATTERNS.items() if pat.search(seg)]
                rel=str(p.relative_to(root))
                key=f"{rel}:{n.name}"
                entries.append(Entry(key,rel,lineno,n.name,marker,dyn))
    return entries

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',default='.')
    ap.add_argument('--warnings-as-errors', action='store_true')
    ap.add_argument('--paths', nargs='*', default=[])
    args=ap.parse_args(argv)
    root=Path(args.root).resolve()
    entries=discover(root)
    inv_file=root/INV_PATH
    if not inv_file.exists():
        print(f"ERROR: inventory missing: {INV_PATH}")
        return 1
    inv=json.loads(inv_file.read_text(encoding='utf-8'))
    known={i['key']:i for i in inv.get('paths',[])}
    errors=[]
    for e in entries:
        rec=known.get(e.key)
        if rec is None:
            errors.append(f"UNKNOWN new runtime path: {e.key}")
            continue
        status=rec.get('status')
        if status in {'unknown','unsafe'}:
            errors.append(f"{status.upper()} runtime path present: {e.key}")
        if status=='safe':
            if rec.get('requires_inline_marker', True) and not e.marker:
                errors.append(f"SAFE path missing inline marker ({MARKER}): {e.key}")
            tests=rec.get('test_evidence') or []
            if not tests:
                errors.append(f"SAFE path missing test_evidence: {e.key}")
            expected=set(rec.get('dynamic_fragments',[]))
            actual=set(e.dynamic)
            if expected!=actual:
                errors.append(f"dynamic fragment mismatch for {e.key}: expected {sorted(expected)} got {sorted(actual)}")
    inv_keys=set(known)
    discovered={e.key for e in entries}
    stale=sorted(inv_keys-discovered)
    if stale:
        print("WARN: stale inventory entries:")
        for s in stale: print(f"  - {s}")
    if errors:
        for err in errors: print(f"ERROR: {err}")
        print(f"Layer 3 Cypher scope scan complete: {len(errors)} error(s), 0 warning(s), {len(errors)} total finding(s).")
        return 1
    print(f"Layer 3 Cypher scope scan complete: 0 error(s), 0 warning(s), 0 total finding(s).")
    return 0

if __name__=='__main__':
    raise SystemExit(main())
