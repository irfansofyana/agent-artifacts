"""Verify the UAEF quickstart end-to-end on deterministic metrics (no AWS needed)."""
from datetime import datetime
from uuid import uuid4

from uaef.api import evaluate
from uaef.models import AgentTrace, Message, MessageRole, ToolCall, GroundTruth

print("uaef version:", __import__("uaef").__version__ if hasattr(__import__("uaef"), "__version__") else "n/a")

def trace(messages, tool_calls, latency, in_tok, out_tok, framework="langgraph"):
    return AgentTrace(
        trace_id=uuid4(),
        framework=framework,
        messages=messages,
        tool_calls=tool_calls,
        input_tokens=in_tok,
        output_tokens=out_tok,
        latency=latency,
    )

now = datetime.now()

# --- Case A: the documented quickstart trace ---------------------------------
ok = trace(
    [
        Message(role=MessageRole.USER, content="What's the weather in Paris?", timestamp=now),
        Message(role=MessageRole.ASSISTANT, content="I'll check the weather for you.", timestamp=now),
        Message(role=MessageRole.ASSISTANT, content="The weather in Paris is sunny with 22C.", timestamp=now),
    ],
    [ToolCall(name="get_weather", arguments={"city": "Paris", "units": "celsius"},
              result={"temperature": 22, "condition": "sunny"}, timestamp=now)],
    latency=1.5, in_tok=150, out_tok=75,
)
gt = GroundTruth(
    expected_output="The weather in Paris is sunny with 22C.",
    expected_tool_calls=[ToolCall(name="get_weather",
                                  arguments={"city": "Paris", "units": "celsius"},
                                  timestamp=now)],
)

METRICS = ["tool_selection_accuracy", "mcp_compliance", "latency_score"]
res = evaluate(trace=ok, ground_truth=gt, metrics=METRICS,
               context=["Paris is the capital of France."])
print("\n=== CASE A (exact tool, 1.5s latency) ===")
print(f"Overall Score: {res.overall_score:.2f}")
print(f"Passed: {res.passed}")
for d in res.dimension_results:
    print(f"{d.dimension_name}: {d.aggregate_score:.2f}")
    for m in d.metric_scores:
        v = "n/a" if m.score is None else f"{m.score:.2f}"
        warn = (m.metadata or {}).get("warning")
        print(f"  - {m.metric_name}: {v}{' (' + str(warn) + ')' if warn else ''}")

# --- Case B: wrong tool + slow -> partial scores ------------------------------
bad = trace(
    [
        Message(role=MessageRole.USER, content="What's the weather in Paris?", timestamp=now),
        Message(role=MessageRole.ASSISTANT, content="Here is a recipe for crepes.", timestamp=now),
    ],
    [ToolCall(name="search_recipes", arguments={"q": "crepes"}, timestamp=now)],
    latency=10.0, in_tok=900, out_tok=800, framework="strands",
)
res_b = evaluate(trace=bad, ground_truth=gt, metrics=["tool_selection_accuracy",
                                                      "tool_sequence_correctness",
                                                      "parameter_quality", "latency_score"])
print("\n=== CASE B (wrong tool, 10s latency) ===")
print(f"Overall Score: {res_b.overall_score:.2f}")
print(f"Passed: {res_b.passed}")
for d in res_b.dimension_results:
    print(f"{d.dimension_name}: {d.aggregate_score:.2f}")
    for m in d.metric_scores:
        v = "n/a" if m.score is None else f"{m.score:.2f}"
        warn = (m.metadata or {}).get("warning")
        print(f"  - {m.metric_name}: {v}{' (' + str(warn) + ')' if warn else ''}")

# --- Threshold gating ---------------------------------------------------------
res_t = evaluate(trace=bad, ground_truth=gt, metrics=["tool_selection_accuracy", "latency_score"],
                 thresholds={"Tool Calling": 0.85, "Performance": 0.70})
print("\n=== THRESHOLD GATE (Tool Calling >= 0.85, Performance >= 0.70) ===")
print("passed:", res_t.passed)
print("failures:", res_t.failures)

print("\nregistry size:", len(__import__("uaef.metrics.registry", fromlist=["x"]).metric_registry.list_metrics()))
