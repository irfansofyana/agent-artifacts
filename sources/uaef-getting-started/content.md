# Universal Agent Evaluation Framework (UAEF)

## A hands-on guide to scoring any AI agent the same way, whatever framework it was built in

UAEF is AWS Labs' open-source, framework-agnostic evaluation system for AI agents. It takes the agent you already have, normalizes one run into a single canonical trace, and scores that trace with 36 built-in metrics spread across 7 quality dimensions.[1][14] Every metric returns a number between 0 and 1, so a tool-calling regression and a safety regression can be read on the same scale.[14]

Results can be persisted, so a new agent version is compared against a stored baseline instead of against your memory of last week's numbers.[14][9] Reports and regression detection close the loop: evaluate, learn what moved, change the prompt or the tools, evaluate again.[14]

**At a glance**

- License: Apache 2.0, source at `awslabs/uaef`.[1][14]
- Version: 0.2.0 (verified from a local install of the repository).
- Requirements: Python 3.10+ and the `uv` package manager; Python 3.11+ for the deployable service.[3][15]
- Metrics registry: 54 entries out of the box, 56 after you opt into the contact-center metrics (verified by listing the registry in a local 0.2.0 install).[6]
- LLM judge: an Amazon Bedrock model, `us.anthropic.claude-sonnet-4-6` by default.[9]
- AWS credentials are only needed for the LLM-judged metrics and for persistence. Deterministic metrics run with no cloud account at all.[4]

## Why this exists

Teams use different agent frameworks, and each one records execution its own way, so the shape of messages, tool calls, and handoffs differs from one to the next.[14] Evaluation tooling tends to follow the same boundaries: metrics, scoring logic, and result storage get written against a single framework's trace format, and then have to be rebuilt when the team switches frameworks or runs agents on more than one.[14]

That coupling makes a basic question hard to answer: did the change I just made to the prompt, model, or tools actually improve the agent?[14] Answering it needs consistent metrics across versions and a shared record of past results.[14] UAEF's answer is to separate the two halves: normalize the trace first, score second, and never let a metric know which framework produced its input.[14]

## The mental model

One evaluation follows one path:

1. An adapter reads the framework's native record (messages, tool calls, agent-to-agent handoffs) and normalizes it into an `AgentTrace`.[14]
2. PII screening runs on the trace before anything is stored.[14]
3. The evaluation engine scores it on a selection from the 36 built-in metrics.[14]
4. The result comes back to the caller, and with `persist=True` it is written to Amazon DynamoDB and Amazon S3.[14]
5. Stored runs are compared against a baseline, and reports and insights explain what changed.[14]

Under the hood the architecture is layered: an adapter layer, core data models, a metrics layer, an evaluation engine, experiment management, analysis and insights, and a reporting layer.[5] You only ever touch the first and last of those directly.

There are also two ways to drive the same engine. The Python library runs in notebooks, scripts, and CI pipelines; the deployable AWS service exposes a low-code web interface over the identical engine and the same stores, so a score never depends on which path produced it.[14]

## Install

The repository is the recommended install path, and `pyproject.toml` plus `uv.lock` are the source of truth for dependencies.[3]

```bash
git clone https://github.com/awslabs/uaef.git
cd uaef
uv sync                 # everything needed to run every metric and every capability
```

`uv sync` installs all metric backends, every adapter, analysis and reporting, the Bedrock LLM judge, and the remote client SDK.[3] The capability extras (`integrations`, `langgraph`, `analysis`, `judge`, `client`, `server`) are retained as no-op aliases so older install commands keep resolving; they add nothing.[3] A Jupyter kernel is the only genuinely optional add-on.[3]

> **Expect a large environment.** Because the core pulls the RAGAS, DeepEval, LangGraph, and Strands backends, the installed environment is heavy: a local `uv sync` on this machine produced a virtualenv of roughly 660 MB. Budget disk and CI image size accordingly.

**What actually needs an AWS account.** Bedrock access is required for the LLM-judged metrics, and DynamoDB plus S3 are required only when you persist results.[3][9] A first evaluation on deterministic metrics needs nothing but the library.[4]

## Your first evaluation

This is the official quickstart trace, using three metrics that are all deterministic, so the run needs no AWS credentials.[4]

```python
from datetime import datetime
from uuid import uuid4

from uaef.api import evaluate
from uaef.models import AgentTrace, Message, MessageRole, ToolCall, GroundTruth

now = datetime.now()

trace = AgentTrace(
    trace_id=uuid4(),
    framework="langgraph",          # or "bedrock", "langchain", "strands", ...
    messages=[
        Message(role=MessageRole.USER, content="What's the weather in Paris?", timestamp=now),
        Message(role=MessageRole.ASSISTANT, content="I'll check the weather for you.", timestamp=now),
        Message(role=MessageRole.ASSISTANT, content="The weather in Paris is sunny with 22C.", timestamp=now),
    ],
    tool_calls=[
        ToolCall(
            name="get_weather",
            arguments={"city": "Paris", "units": "celsius"},
            result={"temperature": 22, "condition": "sunny"},
            timestamp=now,
        )
    ],
    input_tokens=150,
    output_tokens=75,
    latency=1.5,
)

ground_truth = GroundTruth(
    expected_output="The weather in Paris is sunny with 22C.",
    expected_tool_calls=[
        ToolCall(name="get_weather", arguments={"city": "Paris", "units": "celsius"}, timestamp=now)
    ],
)

result = evaluate(
    trace=trace,
    ground_truth=ground_truth,
    metrics=["tool_selection_accuracy", "mcp_compliance", "latency_score"],
    context=["Paris is the capital of France."],
)

print(f"Overall Score: {result.overall_score:.2f}")
print(f"Passed: {result.passed}")
for dimension in result.dimension_results:
    print(f"\n{dimension.dimension_name}: {dimension.aggregate_score:.2f}")
    for metric in dimension.metric_scores:
        value = "n/a" if metric.score is None else f"{metric.score:.2f}"
        print(f"  - {metric.metric_name}: {value}")
```

Running that on version 0.2.0 prints this, verbatim:

```text
Overall Score: 1.00
Passed: True

Tool Calling: 1.00
  - mcp_compliance: n/a
  - tool_selection_accuracy: 1.00

Performance: 1.00
  - latency_score: 1.00
```

Three things to notice. `tool_selection_accuracy` is 1.00 because the agent called exactly the tool the ground truth expected. `latency_score` is 1.00 because 1.5 seconds is under the 2000 ms default threshold.[4] And `mcp_compliance` is `n/a` rather than a number, because that input had nothing for it to judge: every metric returns `None` plus a warning instead of guessing when its input does not apply.[4]

**Now break it.** Give the same ground truth a run that picked the wrong tool and took ten seconds:

```python
result = evaluate(
    trace=bad_trace,               # called search_recipes instead of get_weather, 10s latency
    ground_truth=ground_truth,
    metrics=["tool_selection_accuracy", "tool_sequence_correctness",
             "parameter_quality", "latency_score"],
)
```

The real output on 0.2.0:

```text
Overall Score: 0.06
Passed: False

Tool Calling: 0.00
  - tool_selection_accuracy: 0.00
  - parameter_quality: 0.00
  - tool_sequence_correctness: 0.00

Performance: 0.20
  - latency_score: 0.20
```

`latency_score` is `2000/10000` = 0.20, exactly the documented threshold formula.[6] The overall score is the weighted aggregate over the dimensions that were actually evaluated (0.25 for Tool Calling, 0.10 for Performance against a full weight of 0.35), which is why it lands at 0.06 rather than at an average of the two dimension scores.[13]

**Gate on it.** Thresholds are passed per call and keyed by the exact dimension name, Title Case with spaces.[4][13]

```python
result = evaluate(
    trace=bad_trace,
    ground_truth=ground_truth,
    metrics=["tool_selection_accuracy", "latency_score"],
    thresholds={"Tool Calling": 0.85, "Performance": 0.70},
)
print(result.passed)     # False
print(result.failures)
```

```text
['Tool Calling: score 0.000 below threshold 0.850',
 'Performance: score 0.200 below threshold 0.700']
```

That list is what you assert on in CI.

## The canonical trace is the contract

Adapters are what make UAEF framework-agnostic: they read a run and produce one canonical `AgentTrace`, which is the only thing the rest of UAEF scores.[14] Three models carry almost everything you will care about.[5]

| Model | Fields |
| --- | --- |
| `AgentTrace` | `trace_id`, `messages`, `tool_calls`, `metadata` (latency, tokens, cost), optional `session_id` |
| `Message` | `role` (`user`, `assistant`, `system`, `tool`), `content`, associated `tool_calls` |
| `ToolCall` | `name`, `arguments`, `result`, `timestamp` |

Build the trace yourself if you have already captured a run, or let an adapter do it. Either way the metrics downstream see the same shape, which is what lets an agent built on one framework be compared against an agent built on another on a single scale.[14]

## Wiring your own agent

Six adapters ship in the box, plus a generic one for anything else.[7]

| Framework | How to get the adapter |
| --- | --- |
| LangGraph | `get_adapter("langgraph")` |
| Amazon Bedrock Agents | `get_adapter("bedrock")` |
| LangChain | `get_adapter("langchain")` |
| Langfuse (traces already collected) | `get_adapter("langfuse")` |
| Strands Agents | `get_adapter("strands")` |
| Amazon Bedrock AgentCore | `get_adapter("agentcore")` |
| Anything else | `GenericJSONAdapter(schema_mapping)` |

The generic adapter maps your own JSON onto the canonical trace with a schema mapping, which is the fastest route for an in-house runtime.[7] This mapping was verified against 0.2.0 and produces a well-formed `AgentTrace` with messages, tool calls, tokens, latency, and session id all populated:

```python
from uaef.adapters.generic import GenericJSONAdapter

schema_mapping = {
    "messages": {
        "path": "$.conversation.messages[*]",
        "role_field": "sender",
        "content_field": "text",
        "timestamp_field": "created_at",
    },
    "tool_calls": {
        "path": "$.execution.tools[*]",
        "name_field": "tool_name",
        "arguments_field": "params",
        "result_field": "output",
    },
    "metadata": {
        "input_tokens": "$.usage.input",
        "output_tokens": "$.usage.output",
        "latency": "$.performance.duration",
    },
    "session_id": "$.session.id",
}

adapter = GenericJSONAdapter(schema_mapping)
trace = adapter.transform_to_canonical(custom_data)
```

Two other shapes worth knowing. First, UAEF can run the agent for you: given a runtime ARN or an HTTP endpoint it calls the agent on each dataset input, collects the response, and adapts it in one step, which is the "active" mode against the "passive" mode of feeding it a trace you already have.[14] Second, for a framework with no adapter at all, subclass `BaseAdapter`, implement `transform_to_canonical`, and register it with `register_adapter("my_framework", MyCustomAdapter)`.[7]

## Choosing metrics

The 7 dimensions, and what each one actually covers:[5]

| Dimension | What it measures |
| --- | --- |
| Tool Calling | Tool selection, sequencing, parameter quality, MCP compliance |
| Response Quality | Relevance, completeness, hallucination, accuracy |
| Responsible AI | Safety, bias, prompt injection, toxicity |
| Performance | Latency, token efficiency, cost efficiency, throughput |
| Multi-Turn | Context retention, coherence, conversation completeness, turn efficiency |
| Multi-Agent | Agent utilization, delegation quality, workflow completion, coordination |
| Reasoning | Chain-of-thought coherence, logical consistency, step correctness, fallacies |

Metrics come in three families, and the family decides what you must supply in return.[6]

- **Deterministic**: rule-based and reproducible, no ground truth needed. Latency, token efficiency, cost efficiency, throughput, MCP compliance, prompt injection detection.[5][6]
- **Ground-truth-based**: compares the output against expected results, so it needs labeled test cases with expected outputs and expected tool calls. Tool selection accuracy, tool sequence correctness, parameter quality, accuracy, completeness.[5][6]
- **LLM-judged**: an Amazon Bedrock judge scores the subjective qualities and returns its reasoning with the score. Relevance, hallucination, safety, bias, toxicity, coherence, reasoning quality.[5][6]

Start from your scenario, not from the metric list, because scoring a travel-booking agent and a policy Q&A agent on all 36 metrics wastes time and Bedrock invocations.[14] The starting sets below are the ones AWS recommends per scenario.[14]

| Your agent | Start with |
| --- | --- |
| RAG / knowledge Q&A | `answer_relevance`, `accuracy`, `completeness`, plus the RAGAS context metrics |
| General Q&A | `answer_relevance`, `hallucination_score`, `safety_score`, `latency_score` |
| Tool-using agent | `tool_selection_accuracy`, `tool_sequence_correctness`, `parameter_quality`, `mcp_compliance` |
| Multi-turn conversation | `context_retention`, `coherence`, `conversation_completeness`, `user_satisfaction` |
| Reasoning-heavy | `chain_of_thought_coherence`, `logical_consistency`, `reasoning_step_correctness`, `fallacy_detection` |
| Safety and compliance | `prompt_injection_detection`, `toxicity_score`, `bias_score`, `safety_score` |
| Multi-agent | `agent_utilization`, `delegation_quality`, `workflow_completion`, `coordination_efficiency` |
| Production monitoring | `latency_score`, `token_efficiency`, `cost_efficiency`, `throughput` |

Beyond the built-ins, 21 more metrics come through integrations: 7 prefixed `ragas_`, 8 prefixed `deepeval_`, and 6 Stickler metrics that the catalog still marks work in progress.[6] Two contact-center metrics, `containment` and `resolution`, exist but are deliberately not registered by default, because they are only meaningful for customer-service agents; opt in with one call.[6] Verified on 0.2.0: the registry lists 54 entries before that call and 56 after, the two additions being `containment` and `resolution`.

```python
from uaef.metrics.registry import register_use_case_specific_metrics

register_use_case_specific_metrics()
result = evaluate(trace, metrics=["containment", "resolution"])
```

Selecting metrics happens per call, not on the evaluator.[4] Pass a flat list with `metrics=[...]`, or group by dimension with `metric_set={"tool_calling": [...], "response_quality": [...]}` when you want dimension-level control.[4] Add a custom metric by subclassing `BaseMetric` and calling `register_metric`.[6]

## Ground truth datasets

For the service and the notebook paths, a dataset is one row per test case in CSV or XLSX, and only `Question` is mandatory.[10]

| Column | Required | Purpose |
| --- | --- | --- |
| `Question` | yes | Input sent to the agent |
| `Answer` | no | Expected response |
| `context` | no | Reference documents for retrieval-style evaluation |
| `expected_tool_calls` | no | Expected tool calls as a JSON array |
| `session_id` | multi-turn only | Groups rows into one conversation |
| `turn_id` | multi-turn only | Orders turns within a conversation, starting at 1 |

Without `Answer` you still get safety, performance, and reasoning scores; with it you also get the comparison metrics such as `accuracy`.[10] `Question` and `Answer` accept common aliases and any capitalisation, so existing test files usually work without renaming.[10]

Multi-turn is where the sharp edges are. Rows that share a `session_id` are driven in order against a single agent session, so a later turn can depend on an earlier one, and that is also what unlocks the Multi-Turn dimension.[10] The agent endpoint has to maintain its own conversation state, because UAEF sends each turn with the session id rather than replaying history.[10] And unlike `Question` and `Answer`, the two multi-turn columns are read literally in lowercase: a column called `Session_ID` is not recognised, the file is quietly evaluated as single-turn, and you get a complete set of plausible scores with nothing to indicate the conversations were never assembled.[10]

## Experiments and regression detection

Persisting is what makes version comparison possible: only persisted runs can be compared.[14]

```python
result = evaluate(
    trace=trace,
    ground_truth=ground_truth,
    persist=True,
    experiment_name="Customer Support Agent v2",
    experiment_objective="Measure quality after prompt changes",
)
print(result.experiment_id)
```

With `persist=True` and no name, UAEF resolves the target experiment in a fixed order: a supplied `experiment_id` is used directly, else a supplied `experiment_name` is found or created, else an experiment named `default` is used or created.[9] Each experiment is a self-contained evaluation, so a run with different settings belongs in a new experiment rather than appended to an old one.[9]

Storage splits by job: DynamoDB holds one row per experiment with the metadata used for listing and comparison (evaluation count, per-metric averages, overall average), and S3 holds the full results JSON including per-metric scores and the judge's reasoning.[9][14] Averages in DynamoDB are recomputed on every write, so the row always reflects the current state.[9]

Comparison works on those stored per-metric averages. For each metric two runs share, the engine calculates the absolute and percentage change and classifies it as a regression, an improvement, or unchanged, using a configurable threshold that defaults to 5 percent.[14] Regressions also get a severity: minor (5 to 10 percent), moderate (10 to 20), or severe (over 20), grouped by dimension so you can see whether a prompt change hurt tool calling but left response quality alone.[14] Several runs can be compared against one baseline in a single call.[14]

```python
from uaef.experiments import ComparisonEngine

engine = ComparisonEngine(regression_threshold=5.0, improvement_threshold=5.0)
report = engine.compare_runs(baseline_run, improved_run)
print(report.regressions, report.improvements, report.unchanged)
```

Keep the test set constant across runs and record which set a run used; run names like `baseline-v1.0` and `improved-added-database-tool-v1.1` cost nothing and save an afternoon.[8]

## Human in the loop

An LLM judge is a model, so its scores are worth calibrating. UAEF ships a calibration workflow that queues low-confidence items for human review, samples a slice of high-confidence ones, computes agreement between humans and the judge, and turns the disagreements into prompt suggestions.[11]

```python
from uaef.hitl import AgreementCalculator, JudgeCalibrationWorkflow
from uaef.llm_judge import LLMJudge

workflow = JudgeCalibrationWorkflow(
    llm_judge=LLMJudge(),
    confidence_threshold=0.7,   # queue items the judge scored below this
    sample_rate=0.1,            # also sample 10% of high-confidence items
)
```

`AgreementCalculator` then reports Pearson and Spearman correlation, mean absolute error, and an agreement rate, and `identify_disputes` pulls out the items where the human and the judge diverge by more than a threshold you set.[11] Reviewed items can be frozen into a versioned benchmark and re-run as a regression test on the judge itself.[11]

## Running it in production

The library path covers notebooks, scripts, and CI.[14] A gate looks like this:

```python
results = batch_evaluate(
    traces=test_traces,
    ground_truths=test_gts,
    persist=True,
    experiment_name=f"ci-build-{build_number}",
)

avg = sum(r.overall_score for r in results) / len(results)
assert avg >= 0.8, f"Quality regression: {avg:.2f}"
```

`batch_evaluate` runs traces in parallel through `OfflineEvaluator`, and you control the pool with `max_workers`.[4] For live traffic, evaluate each response and persist every request into a single named experiment: that keeps a running average of production quality you can alert on.[12]

The service path deploys the same engine behind a web interface.[14] You upload a dataset, pick a framework and metrics, run the evaluation, and read the scores; both paths write to the same stores, so a score never depends on which one produced it.[14]

Two operational notes for that path:

- It is a CDK deployment, so it needs `cdk bootstrap` run once per account and region, plus Bedrock model access.[15]
- A React and FastAPI demo app in the repository runs the same flow locally against your ambient AWS credentials, and the demo backend fails closed with a 503 unless you configure an API key or explicitly opt out for local development.[15]

Deploy one stack per tenant: a single deployment has one Cognito pool, one experiment table, and one results bucket shared by every authenticated caller.[15]

## Pitfalls that actually bite

**A green run does not mean the judge ran.** Metrics whose input is unusable return `None` with a warning instead of a score, and `None` scores are excluded from the dimension average rather than counted as zero.[6] Verified on 0.2.0 with no AWS credentials configured: requesting `answer_relevance` and `safety_score` alongside `latency_score` produced `answer_relevance: None (api_error)`, `safety_score: None (api_error)`, and still printed `overall: 1.00, passed: True`. Read the per-metric scores, or assert that the judge metrics are non-null, before you trust a passing build.

**Metrics that need ground truth disappear when you forget it.** Verified on 0.2.0: with no `ground_truth` passed, `tool_selection_accuracy` is skipped rather than returned as `None`, so it is simply absent from `dimension_results`, and the result carries the warning `Ground truth not provided, some metrics may be skipped`. A dashboard that counts metrics will not tell you it lost one.

**Threshold keys are dimension names, not metric names.** They are matched against the dimension name, Title Case with spaces: `"Tool Calling"`, `"Response Quality"`, `"Responsible AI"`, `"Performance"`, `"Multi-Turn"`, `"Multi-Agent"`, `"Reasoning"`.[4][13]

**Treat agent output as untrusted in the judge.** Judge metrics feed the agent's own output back into a prompt, so an agent that can influence its judge can influence its own scores. UAEF sends the rubric separately from the content, escapes the content so it cannot break out of its delimiter, parses judge responses strictly, and requires each score to cite a verbatim span of the content it scored, rejecting a score whose evidence cannot be found.[14] Even so, judge scores are evaluation signal and not a safety decision, and should not gate a security control; for runtime enforcement the guidance is to apply Amazon Bedrock Guardrails in the agent's own invocation path.[14]

**Redact PII before you store or share a dataset.** UAEF screens traces for personally identifiable information such as email addresses, phone numbers, and credit card numbers before data is stored, and `uaef.security.PIIDetector` does the same job on a dataset drawn from real traffic before you share or persist it.[14][10]

**Persisting creates billable cloud resources, and service teardown retains them.** The default stores are a DynamoDB table and an S3 bucket, overridable with environment variables.[14] When you delete the service stack, the DynamoDB tables, S3 buckets, and Cognito user pool are deliberately created with a retain policy, so they and their contents stay behind; the storage keeps costing you until you remove it yourself.[14][15]

**The default judge model pins you to US regions.** `us.anthropic.claude-sonnet-4-6` is a `us.` cross-region inference profile, so it works in `us-east-1`, `us-east-2`, and `us-west-2`.[9] Outside those regions, change the model id rather than discovering the failure at scoring time.

**The extras are no-ops, so dependency pinning is all-or-nothing.** `integrations`, `langgraph`, `analysis`, `judge`, and `client` add nothing because everything ships in the core, which is also why the service Worker had to be packaged as a container image instead of a zip.[3]

**A single run is not a trend.** One trace tells you what happened once; the aggregate over a dataset is what you compare and gate on. Use `evaluate()` to debug one case and `batch_evaluate()` to measure a release.[14]

## A 30-minute path from zero

1. `uv sync`, then run the quickstart trace above with three deterministic metrics. No AWS account required, and you will have a number in about five minutes.[4]
2. Capture ten real runs from your own agent and adapt them with `GenericJSONAdapter`. This is the step that makes the rest of the exercise about your system rather than about the tutorial.[7]
3. Pick three metrics that match your scenario from the table above, and add ground truth for critical journeys and known edge cases only.[14]
4. Create an experiment, run `batch_evaluate(..., persist=True)`, and mark that run as the baseline.[8][9]
5. Turn on Bedrock access, add one or two judge metrics to the same call, and re-run. Compare against the baseline and read which dimensions moved.[14]
6. Put step 4 in CI with an aggregate assertion, so the next regression is caught by the build instead of by a customer.[12]

For the reference material behind all of this, the documentation site carries the full API reference, a metrics catalog with worked good, partial, and bad examples for every metric, and runnable notebooks for each supported framework.[2][6]

## Sources

[1] https://github.com/awslabs/uaef
[2] https://awslabs.github.io/uaef
[3] https://awslabs.github.io/uaef/Getting-Started/installation
[4] https://awslabs.github.io/uaef/Getting-Started/quickstart
[5] https://awslabs.github.io/uaef/Getting-Started/core-concepts
[6] https://awslabs.github.io/uaef/Guides/metrics-catalog
[7] https://awslabs.github.io/uaef/Guides/adapters
[8] https://awslabs.github.io/uaef/Guides/experiments
[9] https://awslabs.github.io/uaef/Guides/persistence-and-configuration
[10] https://awslabs.github.io/uaef/Guides/ground-truth-datasets
[11] https://awslabs.github.io/uaef/Guides/hitl
[12] https://awslabs.github.io/uaef/Guides/use-cases
[13] https://awslabs.github.io/uaef/Advanced/multi-turn-evaluation-workflow
[14] https://aws.amazon.com/blogs/machine-learning/uaef-a-framework-agnostic-system-for-closed-loop-evaluation-of-ai-agents
[15] https://github.com/awslabs/uaef/blob/main/uaef-service/README.md
