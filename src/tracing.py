# tracing.py
from functools import wraps
from typing import Any

import logfire
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from pydantic_ai import Agent, InstrumentationSettings

from config import settings


def traced_node(name: str):
    def decorator(fn):
        @wraps(fn)
        async def wrapper(self, state: dict[str, Any], *args, **kwargs):
            with logfire.span(
                "graph.node." + name,
                node=name,
            ):
                return await fn(self, state)

        return wrapper

    return decorator


logfire.configure(
    send_to_logfire="if-token-present",
    service_name="rag",
    additional_span_processors=[
        BatchSpanProcessor(
            OTLPSpanExporter(
                endpoint=settings.otlp_endpoint,
                timeout=2,
            )
        )
    ],
)

logfire.instrument_pydantic_ai()

Agent.instrument_all(
    InstrumentationSettings(
        include_content=False,
        use_aggregated_usage_attribute_names=True,
    )
)
