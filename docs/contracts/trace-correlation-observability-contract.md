# Trace Correlation Observability Contract

## Canonical key

- Canonical request trace key: `trace_id`.
- Canonical inbound/outbound header: `X-Request-ID`.

## Accepted inbound aliases

The normalization pass accepts these inbound aliases and maps them to canonical `trace_id`:

- `X-Correlation-ID`
- `X-Trace-ID`
- `X-Trace-Id`

## Outbound header set

All normalized responses emit a consistent header set with the same normalized value:

- `X-Request-ID`
- `X-Correlation-ID`
- `X-Trace-ID`
- `X-Trace-Id`

## Layer coverage

Adapters are active in:

- Layer 1 ingestion API middleware
- Layer 3 knowledge API middleware
- Layer 4 agents API middleware

## Logging enrichment

Middleware writes normalized IDs to request state as:

- `request.state.trace_id`
- `request.state.correlation_id`

Log enrichment and error handlers must consume `request.state.trace_id` as the canonical key.
