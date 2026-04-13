# RedisDown Runbook

## Severity: warning

## Alert Condition
`layer1_health_status{component="redis"} == 0` or `layer4_health_status{component="redis"} == 0` for 1 minute.

## Impact
Caching and rate limiting are degraded. Some background tasks may stall.

## Triage Steps
1. Check Redis pod status and resource usage.
2. Verify memory limits and eviction policies.
3. Check if Sentinel or Cluster mode needs promotion.

## Resolution
### Quick Fix
- Restart the Redis pod.
- Adjust memory limits if OOMKilled.
- Promote a Sentinel replica if master is down.

### Root Cause Analysis
- Review memory growth and key expiration rates.
- Check for large keys or pub/sub overload.

## Escalation
- Escalate to platform on-call if data loss is suspected.
- Contact `#vf-platform-oncall`.

## Prevention
- Run Redis Sentinel or Cluster in production.
- Set appropriate maxmemory policies.
- Monitor memory usage with proactive alerts.
