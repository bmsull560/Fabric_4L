package main

workload_kinds := {"Deployment", "StatefulSet", "DaemonSet"}

is_workload {
  workload_kinds[input.kind]
}

podspec := object.get(object.get(input.spec, "template", {}), "spec", {})

containers[c] {
  c := object.get(podspec, "containers", [])[_]
}

containers[c] {
  c := object.get(podspec, "initContainers", [])[_]
}

deny[msg] {
  is_workload
  sc := object.get(podspec, "securityContext", {})
  sc.runAsNonRoot != true
  msg := sprintf("%s/%s must set pod securityContext.runAsNonRoot=true", [input.kind, input.metadata.name])
}

deny[msg] {
  is_workload
  c := containers[_]
  limits := object.get(object.get(c, "resources", {}), "limits", {})
  requests := object.get(object.get(c, "resources", {}), "requests", {})
  object.get(limits, "cpu", "") == ""
  msg := sprintf("%s/%s container %s must define resources.limits.cpu", [input.kind, input.metadata.name, c.name])
}

deny[msg] {
  is_workload
  c := containers[_]
  limits := object.get(object.get(c, "resources", {}), "limits", {})
  requests := object.get(object.get(c, "resources", {}), "requests", {})
  object.get(limits, "memory", "") == ""
  msg := sprintf("%s/%s container %s must define resources.limits.memory", [input.kind, input.metadata.name, c.name])
}

deny[msg] {
  is_workload
  c := containers[_]
  requests := object.get(object.get(c, "resources", {}), "requests", {})
  object.get(requests, "cpu", "") == ""
  msg := sprintf("%s/%s container %s must define resources.requests.cpu", [input.kind, input.metadata.name, c.name])
}

deny[msg] {
  is_workload
  c := containers[_]
  requests := object.get(object.get(c, "resources", {}), "requests", {})
  object.get(requests, "memory", "") == ""
  msg := sprintf("%s/%s container %s must define resources.requests.memory", [input.kind, input.metadata.name, c.name])
}

deny[msg] {
  is_workload
  c := containers[_]
  not c.readinessProbe
  msg := sprintf("%s/%s container %s must define readinessProbe", [input.kind, input.metadata.name, c.name])
}

deny[msg] {
  is_workload
  c := containers[_]
  not c.livenessProbe
  msg := sprintf("%s/%s container %s must define livenessProbe", [input.kind, input.metadata.name, c.name])
}

# Forbid raw Secret manifests in deployable paths; allow clearly example/template files only.
deny[msg] {
  input.kind == "Secret"
  not endswith(input.metadata.name, "-example")
  not contains(lower(input.metadata.name), "template")
  msg := sprintf("Secret/%s is not deployable; use ExternalSecret or secret templates only", [input.metadata.name])
}
