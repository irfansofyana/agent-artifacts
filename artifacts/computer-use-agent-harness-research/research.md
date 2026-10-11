# Computer use is a systems problem: building a vendor-neutral GUI-agent harness

Research snapshot: October 11 to 12, 2026, Western Indonesian Time (UTC+07:00).

## The short answer

Computer use means letting an agent operate software through its interface: inspect a page or desktop, identify controls, click, type, scroll, and check what changed. It is useful when the workflow lives in a GUI rather than a suitable application API. But a model that can point at a button is not yet a dependable automation system.

Three components need separate names. The model proposes actions. The harness manages observations, conversation state, authorization, execution, recovery, and verification. The driver delivers input and obtains interface state. A screenshot-to-action model, a browser automation library, and a desktop input driver are therefore not interchangeable purchases or dependencies.

The engineering recommendation in this article is deliberately narrow: start with a Python-first harness, Playwright for browser execution, and one versioned model adapter. Add Cua Driver behind a small native-desktop adapter only when desktop workflows justify it and the selected components’ licenses are acceptable. Use PyAutoGUI only as an explicitly authorized fallback on an agent-owned desktop. Evaluate browser workflows with BrowserGym and AgentLab; consider ShowUI or UI-TARS as optional open-weight baselines, not mandatory infrastructure.

This is a primary-source research synthesis, not a benchmark run or a working implementation. Documentation, papers, repository code, and license files were inspected. No authenticated model inference, cross-platform desktop acceptance test, or benchmark reproduction was performed. The interface sketch below is typed pseudocode, not runnable or verified code. Recommendations are engineering judgments; published capabilities and measurements receive numbered citations.

## 1. A loop, not a magic click function

Consider a user asking an agent to change a notification setting in a test application. The authorized goal is specific: disable promotional email while leaving security alerts enabled.

A useful execution loop has five stages:

1. Observe the current application, account context, controls, and visible state.
2. Decide which action would advance the goal.
3. Authorize that action against the task scope and current target.
4. Act through a driver with explicit delivery semantics.
5. Verify the resulting setting, then continue or stop.

The model might recognize two toggles and propose disabling the first. The harness should not interpret that proposal as authority to edit arbitrary account settings. It binds the proposal to the observed promotional-email control, checks that the application and account are still correct, and invokes the driver. Afterward it reads the setting again, ideally after navigating away and returning or through an authorized application-state check. A changed-looking toggle proves less than a persisted setting.

This distinction appears in provider contracts: the client-executed computer-use interfaces from OpenAI, Anthropic, and Google require the application to execute requests and return observations. A tool request is not an action already performed.[1][2][3]

A useful conceptual design model is a partially observable Markov decision process, or POMDP. Here that is an engineering analogy, not a claim that the proposed harness implements a formal POMDP solver. The real state includes hidden account settings, pending network requests, application focus, permission grants, and unsaved changes. A screenshot reveals only part of it. A semantic tree reveals another part. History supports a belief about what happened, but does not eliminate uncertainty.

Consequently, an agent sometimes needs to act to learn: open a menu, inspect a dialog, or revisit a setting. The harness should preserve uncertainty rather than compress every outcome into “success.” It should distinguish task verified complete, delivered but unverified, user help required, safety refusal, execution failure, and budget exhaustion. These are proposed lifecycle states, not upstream API names.

## 2. Grounding: from instructions to executable targets

Grounding connects “disable promotional email” to a concrete control. There are several observation channels, and their trade-offs should remain visible.

### Pixels, semantic structure, and OCR

Pixels show what a user sees, including canvases, icons, and visual grouping. They also leave the agent to infer meaning and location. DOM or accessibility observations can supply roles, labels, values, hierarchy, and control identity. BrowserGym exposes screenshots and accessibility-tree observations; native platforms offer their own accessibility interfaces rather than one universal desktop tree.[4][5][6]

OCR supplies text locations without necessarily identifying a button’s behavior. Set-of-marks, or SoM, annotates a screenshot with numbered regions and lets a reasoning model select a region. OmniParser combines detection, OCR, and icon captioning into structured elements and annotated screenshots; it is a perception component, not by itself the whole agent loop.[7]

Engineering recommendation: keep pixels and semantic metadata side by side. Prefer a validated semantic target for ordinary controls, and retain visual fallback for controls absent from the tree. Record which channel grounded the action. A DOM-assisted agent has more privileged information than a screenshot-only agent; report that difference in evaluation rather than treating both as the same model capability.

Do not assume semantic metadata is complete or trustworthy. Windows UIA control patterns can vary dynamically, and Linux AT-SPI depends on accessibility providers and the session bus. An application’s visible button may lack an actionable semantic representation.[6][8]

### End-to-end VLA versus modular perception

A vision-language-action model can learn perception, grounding, reasoning, and action generation together. UI-TARS presents this end-to-end screenshot-to-action approach, while ShowUI uses UI-guided visual-token selection and interleaved visual/action history. Their training methods do not establish that an arbitrary deployed harness will automatically improve from every failed task.[9][10]

A modular system instead combines a planner with a separate locator or parser. That makes it easier to measure whether failure came from target localization, action selection, or execution. It also adds another model or processing stage. The modular versus end-to-end choice should therefore be an ablation, not an ideology.

For an initial open-weight comparison, ShowUI is a lightweight candidate and UI-TARS is a native-agent candidate. Pin the checkpoint, processor, prompt template, and parser together. ShowUI’s published action positions are normalized from zero to one; that is not the same frame as provider screenshot pixels or Google’s normalized coordinates.[11]

Never execute a model’s Python-like action text with unrestricted `eval`. The recommended boundary is a closed, validated action grammar. Even when a provider supports general code execution, that should be a separate capability with a larger isolation and permission boundary.

## 3. Browser libraries: choose the layer you need

### Playwright as the execution baseline

Playwright is the recommended browser driver, not a model planner. Its click actionability checks cover a unique target, visibility, stability, event reception, and enablement; it also provides retrying assertions. Its source license is Apache-2.0.[12][13]

These checks solve an important execution problem: the agent can identify the right button while the page is still animating or an overlay intercepts input. They do not prove that clicking it achieved the business goal. Keep actionability checks and postcondition checks separate.

Playwright supports Chromium, Firefox, and WebKit, but attaching over Chrome DevTools Protocol is Chromium-specific and documented as lower fidelity than a Playwright-protocol connection. Choose the attachment route intentionally rather than assuming every remotely controlled browser offers identical behavior.[14]

Playwright MCP packages browser tools for an MCP client and emphasizes structured accessibility snapshots. It is a tool-access integration, not a replacement for an authorization policy or a complete security boundary.[15]

### browser-use when you want more of the agent stack

browser-use supplies a browser-agent framework rather than just deterministic execution primitives. The current project uses a CDP-based browser architecture; describing it as merely a thin Playwright wrapper is misleading. Its inspected license is MIT.[16][17]

Engineering recommendation: evaluate it when its observation management, agent loop, and browser integration save meaningful work. Avoid putting two independent planners in charge of the same session. Either adopt its orchestration deliberately or expose a narrow integration under your own harness; do not casually mix competing recovery and state-management loops.

### Stagehand v4 for controlled AI-assisted primitives

Stagehand v4 combines `act`, `observe`, and `extract` with deterministic locator methods. Its migration guide removes `agent()` and puts ownership of the agent loop with the caller. The inspected repository license is MIT.[18][19]

This is a useful middle layer when an application needs occasional natural-language grounding without delegating the entire workflow. Current model configuration allows direct provider credentials or a client-side LLM callback. Local browsers are possible; Browserbase hosting is not universally required. The automatic Model Gateway, however, requires a Browserbase session.[20]

Engineering recommendation: use deterministic locators for known, stable interactions and AI primitives for the ambiguous remainder. Keep provider routing explicit during evaluation; automatic per-call model selection is a different experimental condition from one pinned model.

### BrowserGym and AgentLab belong in evaluation

BrowserGym offers a browser environment framework integrating multiple benchmark suites, not one benchmark or a production planner.[21]
AgentLab provides associated experimental tooling.[22]
Both inspected license files declare Apache-2.0.[23][24]

AgentLab is experiment tooling rather than a production browser driver.[22]

BrowserGym is not a secure sandbox for arbitrary generated code. Treat evaluation environments, site fixtures, model execution, and host isolation as separate concerns. A repeatable reset/step interface helps measure behavior; it does not by itself grant permission to execute hostile programs on the host.

## 4. Native desktop control is platform-specific

Browser automation has a relatively coherent execution surface. Native desktops do not. Separate capture, semantic accessibility, targeted input, global input, and environmental isolation before comparing tools.

### Cua Driver: reuse the driver, audit the assembled stack

Cua Driver exposes CLI/MCP and native SDK interfaces independently of model inference. Its Python and TypeScript bindings load the native runtime; the older `cua-agent` package is explicitly deprecated.[25][26]

Its documented observation workflow can return a window screenshot and accessibility tree, with snapshot-bound element references and distinct screen versus screenshot frames. A subsequent observation can invalidate a pending handle, including observations initiated by another actor. This is a concrete reason to make staleness part of the harness contract.[27]

The action-support documentation distinguishes delivered behavior, explicit refusals, and unproven gaps. Pixel-addressed behavior may resolve through semantic hit-testing; that is not proof of unrestricted background pointer delivery into arbitrary canvases or games.[28]

Licensing is component-specific. Cua Driver, core SDK, Lume, and the Python sandbox wrapper are MIT, while Spaces and several associated components use FSL source-available terms. Optional perception components introduce additional licenses. An MIT wrapper does not make the resulting guest stack entirely MIT.[29][30]

Engineering recommendation: pin the driver binary and schema, discover capabilities at startup, and place it behind a small adapter. Do not inherit a whole ecosystem simply to obtain screenshot and click functions. Treat unsupported background input as refusal, not permission to steal focus.

### The operating-system constraints

On macOS, AXUIElement supplies application accessibility queries and actions. Cua’s documented background pixel path uses private SkyLight mechanisms, and its production setup requires appropriate Accessibility/Screen Recording grants with correct host attribution. Expect permission and OS-version regression work, not only Python packaging.[5][31]

On Windows, UIA exposes control patterns such as Invoke, Value, Selection, and Scroll. Input injection through SendInput is constrained by UIPI and existing keyboard state. The desktop driver must run in the interactive user session; Session 0 is not an equivalent automation environment.[6][32][33]

On Linux, AT-SPI provides semantic interfaces, while input and capture depend on the display stack. Cua documents different restrictions for X11, Sway, GNOME, KDE, and experimental nested compositor routes. “Wayland supported” is too broad without naming the compositor, permissions, delivery mode, and tested action.[8][34][28]

The RemoteDesktop portal uses session creation, device selection, and user-granted access, with an EIS connection path for input. A portal grant does not establish arbitrary occluded-window targeting or unconditional unattended permission.[35]

### Other native building blocks

PyAutoGUI provides mouse, keyboard, screenshot, and image-location primitives, not planning or accessibility. Its Linux input implementation uses Xlib/XTest; its license text is BSD-3-Clause. Restrict it to an owned desktop fallback unless user-input interference has been explicitly addressed.[36][37][38]

Enigo and XCap are separate Rust input and capture libraries, with MIT and Apache-2.0 declarations respectively. Their platform/backend features should be checked for the actual build rather than inferred from a broad platform list.[39][40]

Microsoft UFO is a useful Windows architectural reference: HostAgent/AppAgent coordination, state machines, a blackboard, and GUI/COM execution seams. Its repository is MIT. Galaxy’s cross-device orchestration does not imply native GUI parity everywhere: its LinuxAgent is a CLI executor.[41][42][43]

The inspected `suitedaces/computer-agent` is a Tauri application with an Anthropic-specific loop and internal Rust computer control, not an established model-neutral external driver. Its license contains additional derivative/work-for-hire and license-back terms despite an Apache heading. Do not classify it as unmodified Apache-2.0 based on a badge.[44][45][46]

## 5. Provider portability requires versioned contracts

A vendor-neutral harness should normalize intent and lifecycle without pretending the wire formats are identical. Version adapters by endpoint family and tool version. Preserve native call identifiers, result correlation, image rules, and safety metadata.

### OpenAI

The retrieved Responses computer-use guide describes both ordinary function-based code execution and a structured `computer` tool. The structured route returns `computer_call` items containing an ordered `actions` array, not necessarily one `action`. The client executes them and returns `computer_call_output` with the matching `call_id` and a `computer_screenshot` result, continuing the session through `previous_response_id`.[1]

The guide’s code-execution alternative requires an isolated persistent environment and client-managed limits. A separate Agents API hosted-browser contract uses hosted execution; it is not a spelling change for the Responses tool.[1][47]

Recommendation: implement the structured route first if a closed action vocabulary meets the task. Treat generated code as a later, separately authorized execution product. Do not perpetuate preview-only model names or safety fields as timeless requirements.

### Anthropic

The current guide defines `computer_toolset_20260801`, a client toolset with 17 member tools and no beta header. Member calls are distinguished by `toolset_name: "computer"`; correlated tool results must echo that toolset identity. Older beta computer tools remain a separate compatibility path.[2]

Ordered batches execute sequentially. After a failure, later dependent actions stop, but every requested block still needs a correlated error result. Coordinates remain in the full-display screenshot frame; zoom does not switch later actions to crop-relative coordinates. Screenshot/zoom images must meet the toolset’s image limits.[2]

Recommendation: do not silently prune image history or migrate tool versions without contract tests. Preserve requested, executed, skipped, and failed actions separately.

### Google

The retrieved Google guide uses the Interactions API and documents browser, desktop, and mobile environments. Calls are read from interaction steps and answered with matching `function_result` call IDs; continuation uses `previous_interaction_id`.[3]

Its coordinate tables specify a normalized 1000-by-1000 frame with integers from 0 through 999; examples denormalize using the screen dimensions. Calls can include a safety decision requiring user confirmation, followed by a safety acknowledgement in the result.[3]

Recommendation: keep current Interactions and legacy generateContent adapters separate. An example helper returning a continuation string is not a real approval mechanism. Provider safety flags are inputs to your policy, not the entire policy.

Across all three, documentation examples are not proof that every account or cloud has the same model availability. This research did not test authenticated requests, quotas, streaming behavior, retention, or multi-turn contract compatibility.

## 6. Coordinates, stale observations, and ambiguous actions

Engineering recommendation: every observation should identify its environment, session, target window or viewport, capture time, revision, original dimensions, presented dimensions, crop offset, and transform. Every target reference should identify the observation that produced it.

Coordinate errors often masquerade as model failures. A model may output screenshot pixels, normalized fractions, or provider-specific normalized integers. The driver may expect CSS pixels, display pixels, or desktop coordinates. Cropping, browser chrome, device scale, window movement, multiple monitors, and negative monitor origins all affect the conversion.

Represent the mapping as an explicit transform, not scattered arithmetic. A crop-relative point first maps into the captured image; image scaling then maps it to the target window or display; the window origin maps it into desktop space if that delivery route requires it. Preserve aspect ratio or describe separate axes explicitly. Reject out-of-range coordinates rather than quietly steering them onto an unrelated control.

Use synthetic fixtures to test transforms before asking a model to operate a desktop. Place controls at known positions, resize the window, change display scale, move it between monitors, and verify the delivered target. Those are proposed acceptance tests, not tests performed for this article.

Action ambiguity needs equally explicit treatment. “Click” may mean accessibility Invoke, a window-targeted pointer event, or global foreground input. “Type” may insert at the caret or replace a value. A pixel-targeted semantic action is not equivalent to raw pointer delivery. Cua’s documented distinctions make these materially different routes.[27][28]

Stale targets should fail closed or trigger re-observation. A delayed model response may refer to a page before navigation or a desktop before a dialog opened. A stale approval is worse: the user approved one recipient, but the interface now shows another.

Batch only while assumptions remain valid. Filling two harmless fields may be safe within one stable form; clicking a navigation control and then guessing the next page’s coordinates is not. Stop at failure, approval boundaries, unexpected dialogs, and target changes. Do not measure one batch as though it were necessarily comparable to one atomic action.

Cancellation also needs a delivery boundary. If a transport times out after a click, the result is unknown, not automatically “not executed.” Re-observe before retrying a non-idempotent operation. Bind input ownership to a lease and release held buttons/modifier keys after errors. In-flight side effects cannot be assumed reversible merely because the planner stopped.

## 7. Security: untrusted observations meet powerful sinks

A GUI agent reads attacker-influenced text while holding permission to act. Web pages, documents, filenames, accessibility labels, OCR output, and screenshots are task data, not new authority. Visual presentation does not sanitize an instruction.

WASP studies prompt injection against web agents with constrained attacker control and finds vulnerabilities in tested configurations. AgentDojo evaluates tool-using agents with utility and security checks over untrusted data; it is not primarily a visual desktop benchmark. BrowserART addresses a different issue: harmful browser requests can expose action-level failures even when a model refuses similar requests in chat.[48][49][50]

OpenAI’s prompt-injection defense discussion emphasizes source-sink analysis and constraining dangerous actions even when reasoning is deceived. Anthropic describes layered browser defenses and adaptive testing, while warning that low attack-success rates can still matter. These are evidence about documented product/configuration defenses, not protections automatically inherited by a custom executor.[51][52]

The recommended threat model identifies sources an attacker can influence and sinks the agent can reach. Sources include a comment or downloaded document. Sinks include a navigation URL, form field, upload, email recipient, filesystem write, purchase, or shell command. The important question is not only whether the model repeats malicious text, but whether data or authority crosses an unauthorized boundary.

For example, a document might tell the agent to “validate access” by visiting a URL containing confidential text. Reject that transmission even if the planner believes it advances the task. Origin restrictions, scoped credentials, and data-flow controls should remain effective after model deception.

Approval must precede exposure. Typing sensitive information into a web form can transmit it before final submission; OpenAI’s guide explicitly treats such typing as transmission. A submit-only approval gate is therefore insufficient.[1]

Recommended controls are concrete:

- Use disposable browser profiles or owned desktops, least privilege, restricted mounts, and explicit network policy.
- Keep credential material outside model context and bind autofill to the actual origin and authorized operation.
- Bind approval to the exact target, recipient, data, amount, action, and observation revision.
- Reject unknown tool versions, unsupported capabilities, and unauthorized delivery-mode widening.
- Separate code/shell execution from GUI actions; constrain downloads and executable opening.
- Maintain redacted audit records with access and retention limits; screenshots can contain secrets.
- Provide human takeover and deadline-driven cancellation without blind replay of uncertain actions.

Interaction isolation and compromise containment are different. QEMU provides VM management/input/capture seams, while gVisor supplies a Linux-like application kernel, not a Windows/macOS desktop. An Xvfb display or separate interaction session is not by itself a security sandbox.[53][54]

For Apple-host guests, Lume is an MIT virtualization option with macOS host requirements. Tart’s retrieved license is FSL-1.1-ALv2 with version-specific conversion terms. Evaluate the exact virtualization package, guest OS, firmware, and image licenses separately.[55][56][57]

## 8. A minimal Python-first architecture

The proposed design has six replaceable boundaries: environment lifecycle, observation, policy/model adapters, authorization, execution, and verification/recording. Begin with one planner and one environment. Multi-agent orchestration is not a prerequisite for moving a pointer, and it adds shared-state and ownership problems before basic execution is reliable.

The environment provider creates, attaches, resets, and destroys a leased workspace. The observer reports pixels, optional semantic structure, provenance, transforms, and degradation. The model adapter translates provider-native exchanges into typed proposals while retaining native correlation metadata. The authorization service evaluates authority independently. The executor selects only advertised delivery routes. The verifier checks task-specific postconditions.

The following is interface pseudocode in Python notation. It omits implementations, wire formats, full action schemas, persistence, image handling, and cleanup code. It was not executed and must not be presented as a tested library.

```python
from dataclasses import dataclass
from typing import Literal, Protocol

@dataclass(frozen=True)
class Observation:
    environment_id: str
    session_id: str
    target_id: str
    revision: str
    capture_id: str
    transform_id: str
    screenshot_ref: str
    semantic_ref: str | None
    capabilities: frozenset[str]

@dataclass(frozen=True)
class Proposal:
    action_id: str
    expected_revision: str
    target_id: str
    operation: str          # closed tagged union in real code
    delivery_mode: str      # semantic, targeted, owned_foreground
    validated_arguments: object
    provider_call_ref: str

@dataclass(frozen=True)
class Permit:
    action_id: str
    target_id: str
    observation_revision: str
    approval_ref: str | None
    expires_at: str

@dataclass(frozen=True)
class Execution:
    action_id: str
    status: Literal["delivered", "refused", "unknown", "failed"]
    audit_ref: str

class Observer(Protocol):
    async def observe(self, target_id: str) -> Observation: ...

class Policy(Protocol):
    async def propose(self, goal: str, obs: Observation) -> Proposal: ...

class Authorizer(Protocol):
    async def authorize(self, p: Proposal, obs: Observation) -> Permit: ...

class Executor(Protocol):
    async def execute(self, p: Proposal, permit: Permit) -> Execution: ...

class Verifier(Protocol):
    async def check(self, goal: str, obs: Observation) -> bool: ...
```

The critical implementation invariant is that `execute` validates the permit, target, lease, capability, expiry, and expected revision at dispatch, not only when the planner proposed the action. The concrete driver may offer stronger snapshot checks or weaker ones; the adapter must report that difference. Authorization and verification should not simply ask the same planner whether its own action was acceptable and successful.

A production action schema should distinguish invoke, insert-text, replace-value, pointer-click, key sequence, drag, scroll, navigate, wait, and finish. It should carry risk and idempotency information without letting model-supplied labels grant authority. Persist execution IDs so retries can be correlated; never imply exactly-once side effects when the driver and application cannot provide them.

## 9. Evaluation: measure the model-harness pair

Grounding, workflow completion, and safety require separate tracks. ScreenSpot-Pro targets professional/high-resolution localization; it is not an end-to-end workflow score. Original OSWorld evaluates real-computer tasks with initialization and execution-based checks. Original WebArena evaluates realistic multi-step web tasks with outcome-based scoring.[58][59][60]

Version names matter. OSWorld-Verified updates the original suite. OSWorld 2.0 is a long-horizon successor; at retrieval its repository recommended `osworld-v2.1`, with a release manifest pinning code, tasks, assets, and images. WebArena-Verified revises tasks and evaluators and supports deterministic JSON/network-event-based scoring. Do not mix these scores with their original suites without identifying the revision.[61][62][63]

The OSWorld 2.0 paper reports 108 long-horizon workflows and, for one specified model/budget condition, 20.6% strict completion versus 54.8% partial score. That gap illustrates why both measures matter; it is an author-reported result, not this article’s reproduction or a claim about today’s best model.[64]

The retrieved successor release manifest also records incomplete runtime verification, including no full 108-task agent evaluation and no VM boot in its stated setup. Treat those as upstream manifest limitations, not evidence that this research reran or certified the suite.[62]

Recommended reporting includes the exact model/checkpoint, endpoint/tool version, prompts, image handling, observation channels, code permissions, driver build, task/evaluator commits, environment images, and memory policy. Count actions, model turns, tool calls, and steps separately. Record wall time, tokens/cost, setup failures, intervention frequency, refusals, and unknown deliveries alongside completion.

Use clean resets, repeated trials, a private holdout, and explicit exclusions. Keep infrastructure failures in view rather than quietly removing them from the denominator. Compare screenshot-only and semantic-assisted agents as separate conditions. Useful ablations hold the planner fixed while changing grounding, observation channels, batching, or executor routes.

Safety evaluation should measure benign utility, utility under injection, attacker success, attempted unauthorized actions, executor-blocked effects, and approval burden. A harness that refuses everything is safe only in a trivial and useless sense. Use deterministic state/network checks where available; final model prose is not the acceptance oracle.

## 10. Decision matrix and implementation roadmap

The matrix combines inspected component properties with engineering choices. “Recommended” means fit for the proposed narrow architecture, not a benchmark ranking.

| Need | Starting point | Reason to consider it | Boundary to preserve |
|---|---|---|---|
| Browser execution | Playwright | Deterministic locators, actionability, assertions | No built-in task authority; verify outcomes separately |
| Full browser-agent framework | browser-use | Existing CDP-based agent/browser integration | Adopt or isolate its loop deliberately |
| AI-assisted browser primitives | Stagehand v4 | `act`/`observe`/`extract` plus deterministic methods | Caller owns loop; pin routing and inference configuration |
| Native desktop driver | Cua Driver adapter | Native control and snapshot-aware observations | Per-platform capabilities; component-specific licensing |
| Simple owned-desktop fallback | PyAutoGUI | Small Python input/capture surface | Global input, no accessibility, X11-specific Linux path |
| Windows architecture reference | UFO | GUI/COM seams and structured orchestration | Windows GUI scope is not universal desktop parity |
| Browser experiments | BrowserGym + AgentLab | Environment and experiment tooling | Not a secure generated-code sandbox |
| Open-weight comparison | ShowUI / UI-TARS | Alternative VLA/grounding baselines | Pin weights, preprocessing, parser, and coordinates |
| Optional modular perception | OmniParser | OCR/icon/SoM grounding | Resolve artifact-specific license and revision issues |

The component facts in this summary are documented in the browser, driver, and model sections above. The selection itself is an engineering recommendation.

Phase one is a deterministic browser slice. Implement environment leasing, Playwright execution, one provider adapter, authorization, and postcondition verification for a small local application. Acceptance requires persisted settings, stale-target rejection, failure propagation, no unapproved origin changes, and clean cancellation.

Phase two adds adversarial and operational tests before more capability. Inject hostile page instructions, change targets after approval, create overlays, interrupt transport after delivery, and simulate denied credentials. Verify blocked transmissions independently and report benign utility alongside safety. Acceptance requires evidence that executor controls survive a deceived planner.

Phase three introduces one native OS and one owned desktop. Add Cua Driver only after checking the precise selected components. Test permissions, accessibility degradation, display transforms, focus preservation, text insertion versus replacement, unsupported background delivery, and concurrency. Acceptance is action-specific; “driver started” is not sufficient.

Phase four introduces measured comparisons: BrowserGym/AgentLab for browser tasks, pinned desktop suites after infrastructure smoke tests, and optional ShowUI/UI-TARS baselines. Compare equivalent observation and budget conditions. Add modular perception only if localization failures justify its cost and licensing work.

Phase five expands scope selectively: additional OS adapters, durable recovery, richer approvals, and possibly constrained code execution. Do not add multi-agent orchestration until single-session ownership and cancellation are reliable. Each expansion changes the authority boundary and deserves its own acceptance suite.

## 11. Licensing and unresolved research gaps

Code and weights need separate inventory entries. UI-TARS code is Apache-2.0; the inspected UI-TARS-1.5-7B weight card declares Apache-2.0, but a separate top-level weight-license retrieval failed. ShowUI code is Apache-2.0 while the ShowUI-2B weight card declares MIT. Those declarations do not license every derivative checkpoint or dependency.[65][66][67]

ShowUI’s weight declaration is a distinct artifact, not evidence that its code license changed.[68]

OmniParser needs particular care. The inspected repository license is CC-BY-4.0 despite an MIT README badge. Original detector weights carry AGPL-3.0; `icon_detect_v3` and icon-caption folder licenses declare MIT. The hub’s broad pipeline description does not erase the code-license discrepancy or revision-selection questions.[69][70][71]

The icon-caption license is independently inspectable; resolve the entire assembled artifact set before redistribution rather than certifying the project name as “MIT.”[72]

No complete transitive SBOM, training-data audit, benchmark-asset clearance, or cloud-terms analysis was performed. License findings describe inspected declarations, not legal advice. Pin release artifacts and retain notices before shipping.

Runtime gaps remain substantial: no paid model calls, compositor acceptance tests, multi-monitor experiments, accessibility coverage measurements, or independent benchmark runs. Provider contracts and live branch licenses can change. The right next deliverable is a narrow tested harness with auditable failure states, not another unqualified leaderboard claim.

The first implementation should expose its observation revisions, action delivery routes, authorization decisions, and postcondition evidence in a single trace. That trace is what lets a failed task become a reproducible test case.

## Sources

[1] https://developers.openai.com/api/docs/guides/tools-computer-use — OpenAI Responses computer-use guide
[2] https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool — Anthropic computer-use tool guide
[3] https://ai.google.dev/gemini-api/docs/computer-use — Google Gemini computer-use guide
[4] https://raw.githubusercontent.com/ServiceNow/BrowserGym/main/browsergym/core/src/browsergym/core/env.py — BrowserGym environment implementation
[5] https://developer.apple.com/documentation/applicationservices/axuielement — Apple AXUIElement
[6] https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-controlpatternsoverview — Windows UIA control patterns
[7] https://arxiv.org/html/2408.00203v1 — OmniParser paper
[8] https://gnome.pages.gitlab.gnome.org/at-spi2-core/libatspi — GNOME AT-SPI2 API and LGPL
[9] https://arxiv.org/html/2501.12326v1 — UI-TARS paper
[10] https://arxiv.org/html/2411.17465v1 — ShowUI paper
[11] https://huggingface.co/showlab/ShowUI-2B — ShowUI-2B model card
[12] https://playwright.dev/docs/actionability — Playwright actionability and auto-waiting
[13] https://raw.githubusercontent.com/microsoft/playwright/main/LICENSE — Playwright license
[14] https://playwright.dev/docs/api/class-browsertype — Playwright browser connections and CDP
[15] https://github.com/microsoft/playwright-mcp — Playwright MCP repository
[16] https://github.com/browser-use/browser-use — browser-use repository
[17] https://raw.githubusercontent.com/browser-use/browser-use/main/LICENSE — browser-use license
[18] https://docs.stagehand.dev/v4/migrations/v3 — Stagehand v3-to-v4 migration
[19] https://raw.githubusercontent.com/browserbase/stagehand/main/LICENSE — Stagehand license
[20] https://docs.stagehand.dev/v4/configuration/models — Stagehand v4 model configuration
[21] https://github.com/ServiceNow/BrowserGym — BrowserGym repository
[22] https://github.com/ServiceNow/AgentLab — AgentLab repository
[23] https://raw.githubusercontent.com/ServiceNow/BrowserGym/main/LICENSE — BrowserGym license
[24] https://raw.githubusercontent.com/ServiceNow/AgentLab/main/LICENSE — AgentLab license
[25] https://raw.githubusercontent.com/trycua/cua/9579e561613bbe7f7253fb561ae3ae4041c2cab3/libs/cua-driver/README.md — Cua Driver README
[26] https://raw.githubusercontent.com/trycua/cua/9579e561613bbe7f7253fb561ae3ae4041c2cab3/libs/python/agent/README.md — Cua deprecated agent
[27] https://raw.githubusercontent.com/trycua/cua/9579e561613bbe7f7253fb561ae3ae4041c2cab3/libs/cua-driver/rust/Skills/cua-driver/WORKFLOW.md — Cua Driver workflow
[28] https://raw.githubusercontent.com/trycua/cua/9579e561613bbe7f7253fb561ae3ae4041c2cab3/libs/cua-driver/docs/action-support.md — Cua Driver empirical action support
[29] https://raw.githubusercontent.com/trycua/cua/main/LICENSING.md — Cua licensing
[30] https://raw.githubusercontent.com/trycua/cua/9579e561613bbe7f7253fb561ae3ae4041c2cab3/libs/cua-driver/rust/crates/cua-perception/models/THIRD_PARTY_NOTICES.md — Cua perception model notices
[31] https://raw.githubusercontent.com/trycua/cua/9579e561613bbe7f7253fb561ae3ae4041c2cab3/libs/cua-driver/rust/Skills/cua-driver/MACOS.md — Cua Driver macOS
[32] https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput — Windows SendInput constraints
[33] https://raw.githubusercontent.com/trycua/cua/9579e561613bbe7f7253fb561ae3ae4041c2cab3/libs/cua-driver/rust/Skills/cua-driver/WINDOWS.md — Cua Driver Windows
[34] https://raw.githubusercontent.com/trycua/cua/9579e561613bbe7f7253fb561ae3ae4041c2cab3/libs/cua-driver/rust/Skills/cua-driver/LINUX.md — Cua Driver Linux
[35] https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.RemoteDesktop.html — Wayland portal control
[36] https://pyautogui.readthedocs.io/en/latest — PyAutoGUI documentation
[37] https://raw.githubusercontent.com/asweigart/pyautogui/master/pyautogui/_pyautogui_x11.py — PyAutoGUI X11 implementation
[38] https://raw.githubusercontent.com/asweigart/pyautogui/master/LICENSE.txt — PyAutoGUI BSD-3 license
[39] https://raw.githubusercontent.com/enigo-rs/enigo/main/Cargo.toml — Enigo package and features
[40] https://raw.githubusercontent.com/nashaofu/xcap/master/Cargo.toml — XCap package and license
[41] https://raw.githubusercontent.com/microsoft/UFO/a795552d976c4c019d7c2f778a0effb5cef7de6b/documents/docs/ufo2/overview.md — UFO2 architecture
[42] https://raw.githubusercontent.com/microsoft/UFO/a795552d976c4c019d7c2f778a0effb5cef7de6b/LICENSE — UFO MIT license
[43] https://microsoft.github.io/UFO/linux/overview — UFO Linux CLI distinction
[44] https://raw.githubusercontent.com/suitedaces/computer-agent/92795e717b5bd254d1894d46d180eb29b690525b/src-tauri/src/agent.rs — computer-agent agent loop
[45] https://raw.githubusercontent.com/suitedaces/computer-agent/92795e717b5bd254d1894d46d180eb29b690525b/src-tauri/src/computer.rs — computer-agent input implementation
[46] https://raw.githubusercontent.com/suitedaces/computer-agent/92795e717b5bd254d1894d46d180eb29b690525b/LICENSE — computer-agent custom license
[47] https://developers.openai.com/api/docs/guides/agents-api/tools/computer-use — OpenAI Agents API hosted computer use
[48] https://arxiv.org/html/2504.18575v1 — WASP web-agent prompt-injection paper
[49] https://arxiv.org/html/2406.13352v3 — AgentDojo paper
[50] https://arxiv.org/html/2410.13886v1 — BrowserART harmful-browser-task paper
[51] https://openai.com/index/designing-agents-to-resist-prompt-injection — OpenAI agent prompt-injection defense design
[52] https://www.anthropic.com/news/prompt-injection-defenses — Anthropic browser prompt-injection defenses
[53] https://qemu.readthedocs.io/en/master/interop/qemu-qmp-ref.html — QEMU QMP interface
[54] https://raw.githubusercontent.com/google/gvisor/master/README.md — gVisor architecture
[55] https://raw.githubusercontent.com/trycua/cua/main/libs/lume/README.md — Lume README
[56] https://raw.githubusercontent.com/trycua/cua/9579e561613bbe7f7253fb561ae3ae4041c2cab3/libs/lume/Package.swift — Lume macOS package
[57] https://raw.githubusercontent.com/cirruslabs/tart/main/LICENSE — Tart FSL license
[58] https://github.com/likaixin2000/ScreenSpot-Pro-GUI-Grounding — ScreenSpot-Pro project
[59] https://arxiv.org/html/2404.07972v2 — OSWorld original paper
[60] https://arxiv.org/html/2307.13854v4 — WebArena original paper
[61] https://github.com/xlang-ai/OSWorld — OSWorld repository and revision guidance
[62] https://raw.githubusercontent.com/xlang-ai/OSWorld-V2/main/benchmark_releases/osworld-v2.1.json — OSWorld-v2.1 release manifest
[63] https://servicenow.github.io/webarena-verified/dev — WebArena-Verified documentation
[64] https://arxiv.org/html/2606.29537v2 — OSWorld 2.0 paper
[65] https://raw.githubusercontent.com/bytedance/UI-TARS/main/LICENSE — UI-TARS code license
[66] https://huggingface.co/ByteDance-Seed/UI-TARS-1.5-7B/raw/main/README.md — UI-TARS-1.5-7B model-card license declaration
[67] https://raw.githubusercontent.com/showlab/ShowUI/main/LICENSE — ShowUI code license
[68] https://huggingface.co/showlab/ShowUI-2B/raw/main/README.md — ShowUI-2B model-card license declaration
[69] https://raw.githubusercontent.com/microsoft/OmniParser/master/LICENSE — OmniParser repository license
[70] https://huggingface.co/microsoft/OmniParser-v2.0/raw/main/icon_detect/LICENSE — OmniParser original icon_detect license
[71] https://huggingface.co/microsoft/OmniParser-v2.0/raw/main/icon_detect_v3/LICENSE — OmniParser icon_detect_v3 license
[72] https://huggingface.co/microsoft/OmniParser-v2.0/raw/main/icon_caption/LICENSE — OmniParser icon_caption license
