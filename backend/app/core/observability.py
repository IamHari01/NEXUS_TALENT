import os
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

# Configuration: Point to SigNoz OTLP Collector
SIGNOZ_ENDPOINT = os.getenv("SIGNOZ_ENDPOINT", "http://localhost:4317")
ENV = os.getenv("ENV", "production")

# 1. Identity: The 'Resource' defines who is sending the data
resource = Resource.create(
    {
        "service.name": "nexus-talent-api",
        "deployment.environment": ENV,
        "version": "1.0.0",
    }
)

# --- PILLAR 1: TRACING (The Timeline of Events) ---
tracer_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(tracer_provider)

# Use OTLP (gRPC) for SigNoz - much faster than HTTP or Console logging
span_exporter = OTLPSpanExporter(endpoint=SIGNOZ_ENDPOINT, insecure=True)
tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))

# Shared Tracer instance
tracer = trace.get_tracer("nexus-talent-tracer")


# --- PILLAR 2: METRICS (The Quantitative Data) ---
# Exporting metrics via OTLP to SigNoz (Replaces local Prometheus reader)
metric_exporter = OTLPMetricExporter(endpoint=SIGNOZ_ENDPOINT, insecure=True)
metric_reader = PeriodicExportingMetricReader(
    metric_exporter, export_interval_millis=15000
)

meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(meter_provider)

# Shared Meter instance
meter = metrics.get_meter("nexus-talent-metrics")

# --- GLOBAL COUNTERS ---
# Business Metric: Shortlisting Success
shortlist_counter = meter.create_counter(
    "ats_shortlisted_total", description="Total candidates who scored > 80%"
)

# Infrastructure Metrics: Cache Performance
cache_hit_counter = meter.create_counter(
    name="cache_hits_total",
    description="Total number of Redis cache hits",
)
cache_miss_counter = meter.create_counter(
    name="cache_misses_total",
    description="Total number of Redis cache misses",
)
