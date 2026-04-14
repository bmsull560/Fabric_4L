package main

deny[msg] {
  input.kind == "Deployment"
  sc := object.get(input.spec.template.spec, "securityContext", {})
  sc.runAsNonRoot != true
  msg := sprintf("Deployment %s must set pod securityContext.runAsNonRoot=true", [input.metadata.name])
}

deny[msg] {
  input.kind == "Deployment"
  sc := object.get(input.spec.template.spec, "securityContext", {})
  seccomp := object.get(sc, "seccompProfile", {})
  seccomp.type != "RuntimeDefault"
  msg := sprintf("Deployment %s must set pod securityContext.seccompProfile.type=RuntimeDefault", [input.metadata.name])
}

deny[msg] {
  input.kind == "Deployment"
  container := object.get(input.spec.template.spec, "containers", [])[_]
  not has_required_container_security_context(container)
  msg := sprintf("Deployment %s container %s is missing required securityContext hardening", [input.metadata.name, container.name])
}

deny[msg] {
  input.kind == "Deployment"
  initContainer := object.get(input.spec.template.spec, "initContainers", [])[_]
  not has_required_container_security_context(initContainer)
  msg := sprintf("Deployment %s initContainer %s is missing required securityContext hardening", [input.metadata.name, initContainer.name])
}

has_required_container_security_context(container) {
  sc := object.get(container, "securityContext", {})
  sc.allowPrivilegeEscalation == false
  sc.readOnlyRootFilesystem == true
  caps := object.get(sc, "capabilities", {})
  drops := object.get(caps, "drop", [])
  drops[_] == "ALL"
}
