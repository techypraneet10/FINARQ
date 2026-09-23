"""Unit tests for distributed tracer, spans, and context propagation."""

import pytest

from financial_rag.infrastructure.observability.tracer import Tracer


def test_tracer_sync_span_lifecycle() -> None:
    tracer = Tracer()
    with tracer.span("test.parent_span", attributes={"layer": "retrieval"}) as parent:
        parent.set_attribute("key1", "val1")
        with tracer.span("test.child_span") as child:
            assert child.parent_span_id == parent.span_id
            assert child.trace_id == parent.trace_id

    spans = tracer.get_recorded_spans()
    assert len(spans) == 2
    child_rec, parent_rec = spans[0], spans[1]

    assert child_rec.name == "test.child_span"
    assert parent_rec.name == "test.parent_span"
    assert parent_rec.attributes["key1"] == "val1"
    assert parent_rec.duration_ms >= 0.0
    assert parent_rec.status == "OK"


@pytest.mark.asyncio
async def test_tracer_async_span_and_error_recording() -> None:
    tracer = Tracer()
    with pytest.raises(ValueError):
        async with tracer.async_span("test.failing_operation") as span:
            span.set_attribute("attempt", 1)
            raise ValueError("Something went wrong")

    spans = tracer.get_recorded_spans()
    assert len(spans) == 1
    rec = spans[0]
    assert rec.status == "ERROR"
    assert "Something went wrong" in (rec.error_message or "")
    assert rec.attributes["error"] is True
