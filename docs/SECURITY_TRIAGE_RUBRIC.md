# Security Triage Rubric

Standardized classification system for security scan findings in the Value Fabric repository.

---

## Classification Categories

### True Positive
**Definition**: Exploitable vulnerability requiring code change or mitigation.

**Action Required**: Fix, patch, or implement compensating controls.

**Examples**:
- SQL injection with unsanitized user input concatenated into queries
- SSRF with user-controlled URLs hitting internal services
- Hardcoded secrets in source code
- Missing authentication on sensitive endpoints

**Documentation**: File issue with severity, assign to owner, track to resolution.

---

### False Positive
**Definition**: Tool misidentification of safe patterns or non-exploitable code paths.

**Action Required**: Add inline comment explaining safety, suppress in scanner config.

**Examples**:
- `agent.execute()` flagged as SQL injection - actually orchestration method
- `jwt.decode(verify_signature=False)` followed immediately by verified decode
- ORM queries with parameter binding flagged as SQL injection
- SSRF on base URLs from trusted configuration

**Documentation Pattern**:
```python
# SECURITY: [explanation of why this is safe]
# [scanner-name]: ignore [rule-id]
```

---

### Acceptable Risk
**Definition**: Known limitation with documented compensating controls.

**Action Required**: Document risk acceptance, monitoring, and mitigation controls.

**Examples**:
- Debug endpoints enabled in non-production with IP restrictions
- Legacy API without rate limiting but behind API gateway
- Alertmanager templates in Slack markup (not HTML context)

**Documentation**: Record in `docs/security/risk-acceptance/` with:
- Risk description
- Compensating controls
- Review date
- Approver

---

### Needs Review
**Definition**: Uncertain classification requiring manual code inspection.

**Action Required**: Assign to security reviewer for deeper analysis.

**Examples**:
- Truncated code snippets hiding context
- Complex multi-step data flows
- Novel patterns not matching known safe/unsafe categories

**Documentation**: Create ticket, schedule review within 48 hours.

---

## Triage Decision Tree

```
Finding Received
       |
       v
+------------------+
| Is it a known    |
| safe pattern?    |
+--------+---------+
         |
    Yes  |  No
         v
+------------------+
| Is there a       |
| compensating     |
| control?         |
+--------+---------+
         |
    Yes  |  No
         v
+------------------+
| Can it be        |
| exploited with   |
| current code?    |
+--------+---------+
         |
    Yes  |  No
         v
    TRUE POSITIVE   FALSE POSITIVE
    (Fix it)        (Document it)
```

---

## Known Safe Patterns in This Repo

### Pattern 1: Agent/Tool Registry `execute()`
**Rule**: `python.sqlalchemy.security.sqlalchemy-execute-raw-query`  
**Classification**: False Positive  
**Reason**: `execute()` dispatches to tool implementations, not SQL. Tool names are validated against registry; inputs validated via Pydantic schemas.

**Files**: `layer4-agents/src/tools/registry.py`, `layer4-agents/src/api/routes/tools.py`

---

### Pattern 2: OIDC Two-Step JWT Verification
**Rule**: `python.jwt.security.unverified-jwt-decode`  
**Classification**: False Positive  
**Reason**: Per RFC 7517/7519, first decode extracts `kid` for key lookup; second decode verifies signature and claims with fetched key.

**Files**: `shared/identity/oidc.py`

---

### Pattern 3: ORM Parameter Binding
**Rule**: `python.sqlalchemy.security.sqlalchemy-execute-raw-query`  
**Classification**: False Positive  
**Reason**: SQLAlchemy `select().where()` uses bound parameters automatically. UUID validation, enum constraints, and allowlists prevent injection.

**Files**: `layer3-knowledge/src/api/routes/*.py`

---

### Pattern 4: SSRF with Trusted Base URL
**Rule**: `python.requests.security.ssrf`  
**Classification**: False Positive (when validated)  
**Reason**: Base URL from trusted configuration; user input only affects validated path segments or JSON payloads.

**Required**: Inline comment documenting safe pattern.

---

### Pattern 5: Alertmanager Slack Templates
**Rule**: Various template injection rules  
**Classification**: False Positive (or Acceptable Risk)  
**Reason**: Slack templates render in mrkdwn format, not HTML. Variables rendered as plain text in Slack's proprietary markup.

**Documentation**: Header comment in `monitoring/alertmanager/templates/slack.tmpl`

---

## Review Cadence

| Category | Review Frequency |
|----------|------------------|
| True Positive | Track to closure |
| False Positive | Re-verify on major refactors |
| Acceptable Risk | Quarterly review |
| Needs Review | 48 hours |

---

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE/SANS Top 25](https://cwe.mitre.org/top25/)
- [Semgrep Rule Registry](https://semgrep.dev/r)
- [Bandit Documentation](https://bandit.readthedocs.io/)
