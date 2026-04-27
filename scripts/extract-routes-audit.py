#!/usr/bin/env python3
"""
Route Extraction Script for Tri-Track Audit (Track A)
Parses App.tsx to extract all routes and their metadata.
"""

import re
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class RouteEntry:
    path: str
    component: str
    tier: str
    category: str  # 'authenticated', 'public', 'redirect'
    redirect_target: Optional[str] = None
    required_tier: Optional[str] = None

# Read App.tsx content
app_tsx_path = Path("frontend/client/src/App.tsx")
content = app_tsx_path.read_text(encoding='utf-8')

routes = []

# Pattern 1: AuthenticatedRoute with path
auth_route_pattern = re.compile(
    r'<Route\s+path="([^"]+)"[^>]*>\s*<AuthenticatedRoute[^>]*>\s*<([^/>\s]+)',
    re.DOTALL
)

# Pattern 2: Simple Route with Navigate (redirects)
redirect_pattern = re.compile(
    r'<Route\s+path="([^"]+)"[^>]*>\s*<Navigate\s+to="([^"]+)"',
    re.DOTALL
)

# Pattern 3: Route with just component (public routes)
public_route_pattern = re.compile(
    r'<Route\s+path="([^"]+)"[^>]*>\s*<([^/>\s]+)(?!.*Navigate)',
    re.DOTALL
)

# Pattern 4: Catch-all route
catchall_pattern = re.compile(r'<Route>\s*<AppShell')

# Extract requiredTier from AuthenticatedRoute
required_tier_pattern = re.compile(r'requiredTier="([^"]+)"')

# Find all AuthenticatedRoutes
for match in auth_route_pattern.finditer(content):
    path = match.group(1)
    component = match.group(2).strip()
    
    # Look for requiredTier in the surrounding context
    start_pos = max(0, match.start() - 500)
    context = content[start_pos:match.end()]
    tier_match = required_tier_pattern.search(context)
    required_tier = tier_match.group(1) if tier_match else "standard"
    
    routes.append(RouteEntry(
        path=path,
        component=component,
        tier="authenticated",
        category="authenticated",
        required_tier=required_tier
    ))

# Find redirects
for match in redirect_pattern.finditer(content):
    path = match.group(1)
    redirect_target = match.group(2)
    routes.append(RouteEntry(
        path=path,
        component="Navigate",
        tier="redirect",
        category="redirect",
        redirect_target=redirect_target
    ))

# Find public routes (Login, Signup, etc.)
public_components = {'Login', 'Signup', 'LandingPage'}
for match in public_route_pattern.finditer(content):
    path = match.group(1)
    component = match.group(2).strip()
    if component in public_components:
        routes.append(RouteEntry(
            path=path,
            component=component,
            tier="public",
            category="public"
        ))

# Add catch-all if present
if catchall_pattern.search(content):
    routes.append(RouteEntry(
        path="* (catch-all)",
        component="NotFound",
        tier="authenticated",
        category="authenticated"
    ))

# Remove duplicates while preserving order
seen = set()
unique_routes = []
for r in routes:
    key = (r.path, r.component)
    if key not in seen:
        seen.add(key)
        unique_routes.append(r)

# Sort by category and path
unique_routes.sort(key=lambda x: (x.category != "authenticated", x.category != "public", x.category != "redirect", x.path))

# Summary stats
auth_count = sum(1 for r in unique_routes if r.category == "authenticated")
public_count = sum(1 for r in unique_routes if r.category == "public")
redirect_count = sum(1 for r in unique_routes if r.category == "redirect")

print(f"Route Extraction Summary")
print(f"=" * 50)
print(f"Authenticated routes: {auth_count}")
print(f"Public routes: {public_count}")
print(f"Redirect routes: {redirect_count}")
print(f"Total: {len(unique_routes)}")
print()

# Write JSON output
output_path = Path("audit-output/track-a-route-extraction.json")
routes_data = [asdict(r) for r in unique_routes]
output_path.write_text(json.dumps({
    "summary": {
        "authenticated": auth_count,
        "public": public_count,
        "redirect": redirect_count,
        "total": len(unique_routes)
    },
    "routes": routes_data
}, indent=2), encoding='utf-8')

print(f"Routes saved to: {output_path}")

# Print sample
print("\nFirst 10 routes:")
for r in unique_routes[:10]:
    tier_info = f" (tier: {r.required_tier})" if r.required_tier else ""
    redirect_info = f" -> {r.redirect_target}" if r.redirect_target else ""
    print(f"  {r.path:40s} | {r.component:25s} | {r.category}{tier_info}{redirect_info}")
