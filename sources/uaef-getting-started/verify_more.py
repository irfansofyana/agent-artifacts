"""Verify GenericJSONAdapter, edge-case warnings, registry size, and the AWS-less judge path."""
import os
from datetime import datetime
from uuid import uuid4

from uaef.adapters.generic import GenericJSONAdapter
from uaef.api import evaluate
from uaef.metrics.registry import register_use_case_specific_metrics
from uaef.models import AgentTrace, Message, MessageRole, ToolCall

# 1. Registry inventory -------------------------------------------------------
from uaef.metrics import registry as regmod
print("registry module exports:", [n for n in dir(regmod) if "regist" in n.lower()])
r = regmod.MetricRegistry()
names = None
for attr in ("list_metrics", "get_all_metric_names", "list_metric_names"):
    if hasattr(r, attr):
        try:
            names = getattr(r, attr)()
            print(f"registry size via {attr}:", len(names))
        except Exception as e:
            print(attr, "err", e)
if names:
    flat = sorted(names if isinstance(names, list) else list(names))
    print("sample:", flat[:6], "...", flat[-6:])

print("\nAWS env present:",
      {k: bool(os.environ.get(k)) for k in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_PROFILE", "AWS_REGION")})

# 2. Generic JSON adapter ------------------------------------------------------
schema_mapping = {
    "messages": {"path": "$.conversation.messages[*]", "role_field": "sender",
                 "content_field": "text", "timestamp_field": "created_at"},
    "tool_calls": {"path": "$.execution.tools[*]", "name_field": "tool_name",
                   "arguments_field": "params", "result_field": "output"},
    "metadata": {"input_tokens": "$.usage.input", "output_tokens": "$.usage.output",
                 "latency": "$.performance.duration"},
    "session_id": "$.session.id",
}
adapter = GenericJSONAdapter(schema_mapping)
custom = {
    "conversation": {"messages": [
        {"sender": "user", "text": "Find customer data", "created_at": "2026-11-15T10:30:00Z"},
        {"sender": "assistant", "text": "I found 5 customers.", "created_at": "2026-11-15T10:30:05Z"},
    ]},
    "execution": {"tools": [{"tool_name": "search_customers",
                             "params": {"query": "customer data"}, "output": {"count": 5}}]},
    "usage": {"input": 120, "output": 80},
    "performance": {"duration": 1.5},
    "session": {"id": "session_789"},
}
tr = adapter.transform_to_canonical(custom)
print("\n=== GENERIC JSON ADAPTER ===")
print("type:", type(tr).__name__, "| framework:", getattr(tr, "framework", None))
print("messages:", [(m.role.value if hasattr(m.role, "value") else m.role,
                     m.content[:28]) for m in tr.messages])
print("tool_calls:", [(t.name, t.arguments) for t in tr.tool_calls])
print("tokens:", tr.input_tokens, tr.output_tokens, "| latency:", tr.latency,
      "| session:", tr.session_id)

# 3. Edge cases: no ground truth, empty response -------------------------------
now = datetime.now()
no_gt = AgentTrace(
    trace_id=uuid4(), framework="custom",
    messages=[Message(role=MessageRole.USER, content="Hi", timestamp=now),
              Message(role=MessageRole.ASSISTANT, content="Hello there.", timestamp=now)],
    tool_calls=[], input_tokens=10, output_tokens=5, latency=0.5,
)
res = evaluate(trace=no_gt, metrics=["tool_selection_accuracy", "latency_score",
                                     "answer_relevance", "safety_score"])
print("\n=== NO GROUND TRUTH, NO AWS (judge metrics requested) ===")
print("overall:", f"{res.overall_score:.2f}", "| passed:", res.passed)
for d in res.dimension_results:
    for m in d.metric_scores:
        v = "None" if m.score is None else f"{m.score:.2f}"
        print(f"  {d.dimension_name} / {m.metric_name}: {v} warning={(m.metadata or {}).get('warning')}")

# 4. Use-case-specific opt-in --------------------------------------------------
register_use_case_specific_metrics()
r2 = regmod.MetricRegistry()
for attr in ("list_metrics", "get_all_metric_names", "list_metric_names"):
    if hasattr(r2, attr):
        try:
            print("\nregistry size after use-case opt-in via", attr, ":", len(getattr(r2, attr)()))
        except Exception as e:
            print(attr, "err", e)
