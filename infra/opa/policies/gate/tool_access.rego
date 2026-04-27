# GATE Framework — Tool Access Policy
#
# Evaluates tool invocation requests against the agent's ABOM manifest.
# Deployed as an OPA bundle and queried at:
#   POST /v1/data/gate/tool_access
#
# Input schema:
#   {
#     "agent_type":     string,
#     "agent_id":       string,
#     "privilege_tier":  "standard" | "elevated" | "high_privilege",
#     "tool_name":      string,
#     "allowed_tools":  [string],
#     "denied_tools":   [string],
#     "invariants":     { "max_tool_calls_per_run": int, ... },
#     "tenant_id":      string | null,
#     "input_hash":     string
#   }

package gate.tool_access

import rego.v1

default allow := false

# ─── Deny rules (evaluated first) ───

deny contains reason if {
    input.tool_name in input.denied_tools
    reason := sprintf("Tool '%s' is in denied_tools for %s", [input.tool_name, input.agent_type])
}

deny contains reason if {
    not input.tool_name in input.allowed_tools
    reason := sprintf("Tool '%s' is not in allowed_tools for %s", [input.tool_name, input.agent_type])
}

deny contains reason if {
    input.privilege_tier == "high_privilege"
    not input.tool_name in input.allowed_tools
    reason := sprintf("high_privilege agent '%s' denied unlisted tool '%s'", [input.agent_type, input.tool_name])
}

# ─── Allow rule ───

allow if {
    count(deny) == 0
    input.tool_name in input.allowed_tools
}

# ─── Obligations ───

obligations contains "audit_required" if {
    input.privilege_tier == "high_privilege"
}

obligations contains "human_approval_required" if {
    some tool in input.invariants.require_human_approval
    tool == input.tool_name
}

# ─── Response ───

reason := concat("; ", deny) if {
    count(deny) > 0
}

reason := "allowed" if {
    count(deny) == 0
}
