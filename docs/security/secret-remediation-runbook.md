# Secret Remediation Runbook

**Status:** P0 Blocker - Must Complete Before Production Deployment  
**Created:** 2026-05-02  
**Updated:** 2026-05-02  
**Applies To:** All `.env*`, `k8s/secrets.yml`, and secret-bearing files in git history

---

## ⚠️ CRITICAL SECURITY NOTICE

**This repository contains committed secrets.** Do not deploy to production until this runbook is executed.

**Files at risk:** `frontend/.env.development`, `frontend/.env.production`, `frontend/.env.staging`, `frontend/.env.test`, `value-fabric/.env.staging`, `value-fabric/.env.test` (and any other non-example `.env` variants)

---

## Mandatory Sequence

These steps **must** be performed in order. Do not skip or reorder.

1. **Rotate all credentials first.** Every secret referenced by a committed `.env` file must be rotated at its source before any Git cleanup begins.
2. **Replace committed `.env` usage with `.env.example` templates and external secret management.** Remove non-example `.env` files from the working tree and provide `.env.*.example` templates with placeholder values. Use ExternalSecrets, Vault, or equivalent for runtime injection.
3. **Only after rotation, remove files from Git tracking.** Run `git rm --cached` on all non-example `.env` files. Update `.gitignore` to prevent recurrence.
4. **Then use `git-filter-repo` or BFG to purge history.** Purge `.env` files and any other secret-bearing files from the entire Git history.
5. **All collaborators must reclone or hard-reset after history rewrite.** Notify the team. A force-pushed rewrite invalidates all existing clones.

**Failure to follow this sequence risks:**
- Rotating secrets that are still visible in Git history (pointless)
- Breaking applications because secrets are removed before replacements are operational
- Data breaches from credentials that remain valid in historical commits

---

## Phase 1: Immediate Response (Do First)

### 1.1 Inventory Exposed Secret Types

**Check what was exposed (metadata only, never print values):**

```bash
# List tracked files matching secret patterns (safe - no content)
git ls-files | grep -E "\.(env|secrets?\.(ya?ml|json)|\.pem|\.key)$"

# Check git history for secret-risk files (safe - paths only)
git log --all --source --remotes --name-only -- "*.env*" "*secrets*" | sort -u
```

**Typical exposed secrets in this repo:**
- Database passwords (PostgreSQL, Neo4j)
- JWT signing secrets
- API key HMAC secrets
- Service-to-service auth secrets
- OpenAI/Anthropic API keys
- Stripe API keys and webhook secrets
- Container registry tokens

### 1.2 Rotate All Exposed Credentials

**Before any git history cleanup, rotate these in production:**

| Secret Type | Where to Rotate | Priority |
|-------------|-----------------|----------|
| Database passwords | PostgreSQL: `ALTER USER postgres PASSWORD 'NEW_SECRET';` | P0 |
| JWT secrets | Auth service or secret backend | P0 |
| API key HMAC secrets | Key management system | P0 |
| Service auth secrets | Shared secret store | P0 |
| OpenAI API keys | OpenAI dashboard | P1 |
| Stripe keys | Stripe dashboard | P1 |
| Neo4j passwords | Neo4j console | P1 |

**Commands (example for PostgreSQL):**
```bash
# Generate new password (32+ chars)
NEW_DB_PASS=$(openssl rand -base64 32)

# Rotate in database
psql -c "ALTER USER fabric_app PASSWORD '$NEW_DB_PASS';"

# Update ExternalSecret or vault (do NOT commit to git)
# Example for Vault:
vault kv put secret/fabric/prod/layer1 DATABASE_URL="postgresql://fabric_app:${NEW_DB_PASS}@db:5432/fabric"
```

### 1.3 Revoke Old Credentials

After rotation, immediately revoke old credentials at their source:
- OpenAI: Deactivate old API keys in dashboard
- Stripe: Revoke old API keys
- JWT: Set short expiration on tokens signed with old secret
- Database: Verify old password no longer works

---

## Phase 2: Replace Secret Architecture

### 2.1 Use ExternalSecrets (Kubernetes)

**Replace `k8s/secrets.yml` with ExternalSecret manifests:**

Created templates in:
- `k8s/base/externalsecrets/clustersecretstore.yaml`
- `k8s/base/externalsecrets/externalsecret-layer1.yaml`

**Enable External Secrets Operator:**
```bash
# Install ESO
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets \
  --namespace external-secrets \
  --create-namespace

# Create ClusterSecretStore (Vault example)
kubectl apply -f k8s/base/externalsecrets/clustersecretstore.yaml

# Create ExternalSecret for each layer
kubectl apply -f k8s/base/externalsecrets/externalsecret-layer1.yaml
```

### 2.2 Development Environment

**Use `.env` files (gitignored) with `.env.example` template:**

```bash
# Copy template
cp .env.example .env
# Edit with real values (never commit)
nano .env
```

**Template created:** `.env.example` (safe, placeholders only)

---

## Phase 3: Git History Cleanup

### 3.1 Prerequisites (MUST complete first)

- [ ] All credentials rotated
- [ ] Old credentials revoked
- [ ] ExternalSecret manifests applied and verified
- [ ] Applications using new secrets confirmed working

**⚠️ DANGER:** Do not run git-filter-repo until Phase 1 and 2 are complete.

### 3.2 Clean Git History

**Option A: git-filter-repo (recommended)**

```bash
# Install git-filter-repo
pip install git-filter-repo

# Create filter file (paths only, no values)
cat > secrets-filter.txt << 'EOF'
# Secret file patterns to remove from history
regex:\.env$
regex:\.env\.
regex:.*secrets?\.ya?ml$
regex:.*\.pem$
regex:.*\.key$
EOF

# Run filter (removes files entirely from history)
git filter-repo --paths-from-file secrets-filter.txt --invert-paths

# Verify cleanup
git log --all --name-only | grep -E "\.env|secrets" | head -20
# Should return nothing
```

**Option B: BFG Repo-Cleaner**

```bash
# Download BFG
wget https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar -O bfg.jar

# Remove secret files
java -jar bfg.jar --delete-files "*.env" --delete-files "*secrets.yml"

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

### 3.3 Force Push and Notify

```bash
# Force push to all remotes
git push origin --force --all
git push origin --force --tags

# Notify all collaborators
echo "Repository history rewritten. All collaborators must reclone or hard-reset."
```

**Critical:** All collaborators must:
```bash
# Backup their work
cd ..
mv Fabric_4L Fabric_4L_backup

# Fresh clone
git clone <repo-url> Fabric_4L
cd Fabric_4L

# Restore their work carefully (do NOT restore old .env files)
```

---

## Phase 4: Prevent Reintroduction

### 4.1 Update .gitignore

Ensure `.gitignore` contains:

```gitignore
# Environment files
.env
.env.*
!.env.example
!.env.template
!.env.dev.example

# Secrets
*.pem
*.key
*secrets.yml
*secrets.yaml
*secret.yml
*secret.yaml

# Kubernetes secrets (raw, not ExternalSecret)
k8s/**/secrets.yml
k8s/**/secrets.yaml
!k8s/**/externalsecrets/
```

### 4.2 Enable CI Secret Scanning

**Add to `.github/workflows/security-gates.yml`:**

```yaml
- name: Detect committed secrets
  run: |
    # Scan with gitleaks or trufflehog
    gitleaks detect --source . --verbose --redact
    
- name: Verify no raw k8s secrets
  run: |
    if git ls-files | grep -E "k8s/.*/secrets\.(yml|yaml)$"; then
      echo "❌ Raw Kubernetes Secret files found. Use ExternalSecret instead."
      exit 1
    fi
```

### 4.3 Pre-commit Hooks

**Install pre-commit with secret detection:**

```bash
pip install pre-commit
pre-commit install

# Add to .pre-commit-config.yaml:
# - repo: https://github.com/gitleaks/gitleaks
#   hooks:
#   - id: gitleaks
```

---

## Phase 5: Verification

### 5.1 Post-Cleanup Checks

```bash
# 1. Verify no tracked secret files
git ls-files | grep -E "\.(env|secrets?\.(ya?ml|json)|\.pem|\.key)$" && echo "FAIL" || echo "PASS"

# 2. Verify ExternalSecrets work
kubectl get externalsecrets -A

# 3. Verify apps start with new secrets
docker compose up -d  # or deploy to staging

# 4. Run structural preflight
python scripts/ci/structural_preflight.py --strict
```

### 5.2 Evidence for Launch Readiness

**Required evidence in `docs/readiness/current.md`:**

| Criterion | Evidence | Status |
|-----------|----------|--------|
| Secrets rotated | Rotation timestamps from secret backends | [ ] |
| Old credentials revoked | Deactivation confirmations | [ ] |
| Git history clean | `git log` shows no secret files | [ ] |
| ExternalSecrets operational | `kubectl get externalsecret` shows READY | [ ] |
| CI secret scanning enabled | Workflow file showing gitleaks/trufflehog | [ ] |

---

## Quick Reference: Safe vs Unsafe Commands

### ✅ Safe (metadata only)
```bash
git ls-files | grep "\.env"  # Lists filenames only
git log --name-only          # Lists paths only
python scripts/ci/structural_preflight.py --json  # Redacts values
```

### ❌ Unsafe (exposes values)
```bash
cat .env                     # Prints secret values
git show HEAD:.env           # Shows historical values
grep -r "SECRET" .           # May print secret lines
echo $DATABASE_URL           # Exposes env var value
```

---

## Emergency Contacts

- **Security issues:** security@example.com
- **Infrastructure:** devops@example.com
- **Secret backend admin:** vault-admin@example.com

---

*This runbook was generated as part of structural hardening (Phase 8). Execute Phases 1-3 in order. Do not skip credential rotation before git history cleanup.*
