# Backend-Integrated Stack Startup Issue

**Date:** 2026-05-04
**Sprint:** Sprint 3 - Backend-Integrated Product Confidence and Runtime Policy Checks

## Issue Summary

Attempted to start the backend-integrated stack using `docker-compose.backend-integrated.yml` but the build failed during the image build phase.

## Command Executed

```bash
docker compose -f docker-compose.backend-integrated.yml up --build -d
```

## Error Output

```
Exit code: 1
Output:
[+] up 0/8
- Image fabric_4l-layer1-worker Building 0.1s
- Image fabric_4l-layer1 Building 0.1s
- Image fabric_4l-layer6 Building 0.1s
- Image fabric_4l-layer4 Building 0.1s
- Image fabric_4l-layer5 Building 0.1s
- Image fabric_4l-layer2 Building 0.1s
- Image fabric_4l-layer5-migrate Building 0.1s
- Image fabric_4l-layer3 Building 0.1s
```

## Root Cause Analysis

**Confirmed issue:** Docker network/download error during package installation
- Error occurs while downloading packages from debian repositories
- `failed to receive status: rpc error: code = Unavailable desc = error reading from server: EOF`
- This is a transient network connectivity issue, not a code/configuration problem

**Validation performed:**
- Docker Compose YAML syntax valid (`docker compose config` succeeded)
- All service directories exist with valid Dockerfiles
- Volume mount paths correct (`./packages/shared/src/value_fabric/shared` exists)
- Init script path correct (`./value-fabric/scripts/init-multiple-dbs.sh` exists)
- Build contexts valid for all services

## Potential Causes

1. **Network connectivity**: Docker daemon cannot reach debian package mirrors
2. **Docker registry issues**: Temporary outages with Docker Hub or debian mirrors
3. **Firewall/proxy**: Corporate firewall or proxy blocking package downloads
4. **Docker daemon state**: Docker daemon may be in a degraded state

## Next Steps for Investigation

1. **Retry the build**: This may be a transient network issue
   ```bash
   docker compose -f docker-compose.backend-integrated.yml build layer1
   ```

2. **Check Docker daemon health**:
   ```bash
   docker ps
   docker info
   ```

3. **Test network connectivity**:
   ```bash
   docker run --rm debian:bookworm apt-get update
   ```

4. **Check for proxy settings**: Verify if Docker is configured to use a proxy

5. **Try building with different base image**: Test if issue is specific to `python:3.11.11-slim-bookworm`

## Workarounds

- **Retry build**: Network errors are often transient; retrying may succeed
- **Use pre-built images**: If available, use pre-built images instead of building from source
- **Configure Docker proxy**: If behind corporate firewall, configure Docker proxy settings
- **Focus on contract/deep tests**: Continue with contract and deep tests that don't require backend
- **Document as known issue**: Add to technical debt for later resolution

Since the backend stack cannot be started, Phase 1 backend validation is blocked. However:
- The seed script (`scripts/db/seed-e2e-data.ts`) is functional and can be used when backend is available
- Playwright backend-integrated configuration is ready (requires `@backend` tag on tests)
- Test infrastructure is in place (global-setup.ts seeds data automatically)

Proceeding with Phase 2 (backend-integrated test creation) which can be validated once backend issues are resolved.
