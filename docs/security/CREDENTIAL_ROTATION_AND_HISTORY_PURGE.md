# Credential Rotation and Git History Purge

## Background

Historical audit (`reports/security/tracked_secret_files.md`, 2026-05-02) identified **6 tracked `.env` files** that may have contained live credentials:

| File | Status |
|------|--------|
| `frontend/.env.development` | Removed from working tree |
| `frontend/.env.production` | Removed from working tree |
| `frontend/.env.staging` | Removed from working tree |
| `frontend/.env.test` | Removed from working tree |
| `.env.staging` | Removed from working tree |
| `.env.test` | Removed from working tree |

These files have been removed from the current working tree but **may still exist in Git history**.

## Action Required

### Step 1: Credential Rotation (HUMAN ACTION REQUIRED)

**BEFORE purging Git history, rotate ALL credentials that may have been exposed in the above files.**

1. **JWT secrets**: Generate new secrets for all environments
   ```bash
   openssl rand -hex 32
   ```
   Update in: Vault, Infisical, GitHub Environment secrets, `.env.dev` (local)

2. **API keys**: Rotate any OpenAI, Anthropic, Thesys, or third-party API keys

3. **Database passwords**: Rotate PostgreSQL, Neo4j, and Redis passwords

4. **OAuth client secrets**: Rotate Salesforce, Keycloak, and any OIDC client secrets

5. **Cloud credentials**: Rotate any AWS/GCP/Azure service account keys

### Step 2: Git History Purge

After credential rotation is complete:

```bash
# Install git-filter-repo (preferred over BFG)
pip install git-filter-repo

# Create a fresh clone for the operation
git clone --mirror https://github.com/bmsull560/Fabric_4L.git fabric_4l_mirror.git
cd fabric_4l_mirror.git

# Purge .env files from history
git filter-repo \
  --path-glob '*.env' \
  --path-glob '*/.env.*' \
  --invert-paths \
  --force

# Push the rewritten history (DESTRUCTIVE)
git push --mirror --force
```

**Alternative with BFG Repo-Cleaner:**

```bash
# Download BFG
wget https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar

# Run BFG on .env files
java -jar bfg-1.14.0.jar --delete-files '.env*' Fabric_4L.git
cd Fabric_4L.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

### Step 3: Team Coordination

1. **Notify all collaborators** immediately after the history rewrite
2. **Everyone must reclone** the repository:
   ```bash
   rm -rf Fabric_4L
   git clone https://github.com/bmsull560/Fabric_4L.git
   ```
3. **Close all open PRs** that were based on the old history and recreate them from the new clone
4. **Update CI caches** if they reference old commit SHAs

### Step 4: Verification

```bash
# Verify no .env files remain in history
git log --all --full-history --name-only --pretty=format: | grep -E '\.env($|\.)' | sort -u
# Should return empty

# Verify gitleaks passes
gitleaks detect --source . --verbose
```

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| History rewrite breaks open PRs | Close and recreate all PRs after purge |
| Forks retain old history | Notify fork owners to delete and refork |
| CI caches invalid | Clear GitHub Actions caches |
| Tags/releases reference old SHAs | Recreate tags after purge |
| Backup copies exist | Ensure no team members have old clones with secrets |

## Compliance Note

This purge is required for SOC 2 Type II and ISO 27001 compliance. The presence of credentials in Git history is a **critical finding** that will block certification audits.

## Sign-off

| Role | Name | Date | Status |
|------|------|------|--------|
| Security Lead | | | ☐ Credential rotation complete |
| DevOps Lead | | | ☐ History purge complete |
| Engineering Lead | | | ☐ Team notified and recloned |
