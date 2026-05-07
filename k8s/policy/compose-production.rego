package main

is_compose {
  input.services
}

services[name] := svc {
  svc := input.services[name]
}

deny[msg] {
  is_compose
  svc := services[name]
  object.get(svc, "user", "") == ""
  msg := sprintf("compose service %s must set non-root user", [name])
}

deny[msg] {
  is_compose
  svc := services[name]
  not svc.healthcheck
  msg := sprintf("compose service %s must define healthcheck (probe equivalent)", [name])
}

deny[msg] {
  is_compose
  svc := services[name]
  limits := object.get(object.get(object.get(svc, "deploy", {}), "resources", {}), "limits", {})
  object.get(limits, "cpus", "") == ""
  msg := sprintf("compose service %s must define deploy.resources.limits.cpus", [name])
}

deny[msg] {
  is_compose
  svc := services[name]
  limits := object.get(object.get(object.get(svc, "deploy", {}), "resources", {}), "limits", {})
  object.get(limits, "memory", "") == ""
  msg := sprintf("compose service %s must define deploy.resources.limits.memory", [name])
}
