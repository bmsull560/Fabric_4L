# Distributed Tracing Configuration

This directory contains shared OpenTelemetry/Jaeger tracing configuration for all Value Fabric layers.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Value Fabric Layers                       │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │   L1    │ │   L2    │ │   L3    │ │   L4    │  ...      │
│  │Ingestion│ │Extract │ │Knowledge│ │ Agents  │           │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘           │
│       │           │           │           │                 │
│       └───────────┴───────────┴───────────┘                 │
│                   OpenTelemetry SDK                          │
└────────────────────────┬────────────────────────────────────┘
                         │ OTLP (gRPC/HTTP)
┌────────────────────────▼────────────────────────────────────┐
│           OpenTelemetry Collector                              │
│  - Batch processing                                            │
│  - Tail-based sampling                                         │
│  - Resource enrichment                                         │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              Jaeger (All-in-One)                             │
│  - Trace storage                                               │
│  - UI visualization                                            │
│  - Search and analysis                                         │
└───────────────────────────────────────────────────────────────┘
```

## Configuration

### 1. Jaeger Deployment

```bash
# Deploy Jaeger
kubectl apply -f k8s/monitoring/jaeger-deployment.yaml
kubectl apply -f k8s/monitoring/jaeger-service.yaml

# Verify
kubectl get pods -n monitoring -l app=jaeger
```

Access Jaeger UI:
- Cluster internal: `http://jaeger-query.monitoring.svc.cluster.local:16686`
- External (if ingress configured): `https://jaeger.value-fabric.local`

### 2. OpenTelemetry Collector

```bash
# Deploy OTel Collector
kubectl apply -f k8s/monitoring/opentelemetry-collector.yaml

# Verify
kubectl get pods -n monitoring -l app=opentelemetry
```

### 3. Network Policies

```bash
# Apply network policies for secure communication
kubectl apply -f k8s/monitoring/tracing-network-policy.yaml
```

## Instrumenting a Layer

Add the following to each layer's `main.py`:

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

# Initialize tracing
def init_tracing(service_name: str):
    provider = TracerProvider(
        resource=Resource.create({
            "service.name": service_name,
            "service.namespace": "value-fabric",
            "deployment.environment": "production"
        })
    )
    
    # OTLP exporter to collector
    otlp_exporter = OTLPSpanExporter(
        endpoint="http://otel-collector.monitoring.svc.cluster.local:4317",
        insecure=True
    )
    
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    trace.set_tracer_provider(provider)
    
    return provider

# In your FastAPI app creation:
app = FastAPI()
FastAPIInstrumentor.instrument_app(app)

# Instrument Redis
RedisInstrumentor().instrument()

# Instrument SQLAlchemy
SQLAlchemyInstrumentor().instrument()
```

## Trace Context Propagation

### HTTP Headers

All requests must propagate these headers:

| Header | Description | Example |
|--------|-------------|---------|
| `x-trace-id` | W3C Trace ID | `4bf92f3577b34da6a3ce929d0e0e4736` |
| `x-span-id` | Current span ID | `00f067aa0ba902b7` |
| `x-sampled` | Sampling flag | `1` |
| `x-tenant-id` | Tenant context | `tenant-abc123` |
| `x-workflow-id` | Workflow ID | `wf-xyz789` |

### Example: Cross-Layer Request Flow

```
Client → L1 (Ingestion) → L2 (Extraction) → L3 (Knowledge)
   │        │                  │                  │
   │   Trace ID: abc          │                  │
   │        │            Trace ID: abc          │
   │        │                  │            Trace ID: abc
   │        │                  │                  │
   │        └──────────────────┴──────────────────┘
   │                  Same Trace Context
```

## Sampling Configuration

### Head-Based Sampling (Default)

- 10% of traces sampled at entry point
- Entire trace included or excluded
- Configured in tracing-config.yaml

### Tail-Based Sampling (OTel Collector)

- Collects all spans temporarily
- Makes sampling decision when trace completes
- Keeps:
  - All error traces
  - Traces with latency > 1s
  - 10% of remaining traces

## Common Operations

### Finding Slow Traces

```
Jaeger UI → Search → Min Duration: 1000ms → Find Traces
```

### Finding Error Traces

```
Jaeger UI → Search → Tags: error=true → Find Traces
```

### Cross-Layer Dependency Graph

```
Jaeger UI → System Architecture → Show Dependencies
```

## Troubleshooting

### No Traces Appearing

1. Check OTel Collector is running:
   ```bash
   kubectl logs -n monitoring -l app=opentelemetry
   ```

2. Verify sampling ratio is not 0

3. Check network policies allow communication

### Missing Cross-Layer Spans

1. Verify trace context headers are propagated
2. Check all layers use same propagation format (W3C)
3. Verify no proxies strip headers

### High Memory Usage

1. Reduce max_traces in Jaeger config
2. Increase batch processor timeout
3. Reduce sampling ratio temporarily

## References

- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [W3C Trace Context](https://www.w3.org/TR/trace-context/)
