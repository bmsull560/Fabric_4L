import sys
import types

class _AutoModule(types.ModuleType):
    """Module that auto-creates submodules on attribute access."""
    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        if name not in self.__dict__:
            mod = _AutoModule(f"{self.__name__}.{name}")
            self.__dict__[name] = mod
            sys.modules[mod.__name__] = mod
        return self.__dict__[name]

def install_otel_stubs():
    try:
        import opentelemetry  # noqa: F401
    except ImportError:
        otel = _AutoModule("opentelemetry")
        otel.trace = _AutoModule("opentelemetry.trace")
        otel.sdk = _AutoModule("opentelemetry.sdk")
        otel.exporter = _AutoModule("opentelemetry.exporter")
        sys.modules["opentelemetry"] = otel
        sys.modules["opentelemetry.trace"] = otel.trace
        sys.modules["opentelemetry.sdk"] = otel.sdk
        sys.modules["opentelemetry.exporter"] = otel.exporter
        # Pre-populate leaf modules with commonly imported symbols
        otel.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter = type("OTLPSpanExporter", (), {})
        otel.sdk.resources.Resource = type("Resource", (), {})
        otel.trace.SpanContext = type("SpanContext", (), {})
