# tracing.py
import inspect
from functools import wraps
from typing import Any

import opentelemetry.trace as trace
from langfuse import Langfuse
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from pydantic_ai import Agent, InstrumentationSettings

from src.config import settings

# Shared global provider: Langfuse adds its own span processor (auth via
# LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY env vars, disabled when absent),
# so spans flow to both Langfuse and the local OTLP collector.
provider = TracerProvider(resource=Resource.create({"service.name": "rag"}))
provider.add_span_processor(
    BatchSpanProcessor(
        OTLPSpanExporter(
            endpoint=settings.otlp_endpoint,
            timeout=2,
        )
    )
)
trace.set_tracer_provider(provider)

langfuse = Langfuse(tracer_provider=provider)

tracer = trace.get_tracer("rag")


def traced_node(name: str):
    def decorator(fn):
        # keep sync nodes sync: awaiting a plain dict fails ('dict' object
        # can't be awaited), so wrap each kind natively
        if inspect.iscoroutinefunction(fn):

            @wraps(fn)
            async def wrapper(self, state: dict[str, Any], *args, **kwargs):
                with tracer.start_as_current_span(
                    "graph.node." + name,
                    attributes={"node": name},
                ):
                    return await fn(self, state)

            return wrapper

        @wraps(fn)
        def sync_wrapper(self, state: dict[str, Any], *args, **kwargs):
            with tracer.start_as_current_span(
                "graph.node." + name,
                attributes={"node": name},
            ):
                return fn(self, state)

        return sync_wrapper

    return decorator


Agent.instrument_all(
    InstrumentationSettings(
        include_content=False,
        use_aggregated_usage_attribute_names=True,
    )
)
