# AWS AgentCore Code Interpreter: practical POC runbook

Revision 2 · October 14, 2026 · us-west-2 · Python

**Follow this order: organization approval and SCPs → IAM and dependencies → create one tool in the console or CLI → call it from a local Python script → add Deep Agents/LangChain → adopt the working resource into Terraform.**

The baseline is a custom **SANDBOX** Code Interpreter. It requires no customer VPC, NAT gateway, container image, AgentCore Runtime, or S3 bucket for API-based file transfer.[3][6][9]

"Local" means the Python client runs on your workstation. **Code execution still happens remotely in AWS and incurs AWS charges.** This is not an offline AgentCore emulator.

All identities, account IDs and organization-policy examples below are illustrative. They are not a diagnosis of any specific company's SCPs. Only the organization's authorized policy owners should approve or apply changes.

[TOC]

## 1. The path and checkpoints

You can finish the basic service test before installing Deep Agents or touching Terraform:

1. **Organization/security owner:** approve the POC account, us-west-2, SANDBOX mode and the API network path; identify any SCP deny.
2. **IAM/platform owner:** supply the execution role and a deployer role; ensure the caller permission set can be granted after creation.
3. **Operator:** create a custom interpreter in the console or CLI, wait for READY and record its returned ID and ARN.
4. **IAM/platform owner:** attach a caller policy scoped to that exact ARN.
5. **Developer:** run a small local boto3 script, inspect remote execution output and verify session termination.
6. **Developer:** run file/isolation/failure smoke tests, then Deep Agents and optionally plain LangChain.
7. **Infrastructure owner:** import the same working resource into Terraform, or create a separately named resource deliberately. Review every replacement plan.

Do not use model output as the only success criterion. Observe the tool call, verify the result or downloaded artifact, exercise failure cases, and read back session state after cleanup.

### What is and is not validated

The reference includes locally exercised Python framework/mock-SDK tests, policy-generator tests, AWS request-schema checks, Terraform validation and four mock-provider tests. The PDF and site have separate layout checks. **These checks do not establish effective company permissions.**

No AWS resources, SCPs, IAM roles, model invocations or company policies were created or modified to produce this guide. Cloud acceptance steps require an authorized operator. Policy JSON validity, known action names and successful mock tests are not the same as AWS IAM Access Analyzer validation or a live Organizations/IAM evaluation.

## 2. Prerequisites: owner, deliverable and stop condition

### Organization/security owner

Deliverable:

- Approved member account and `us-west-2`.
- Required AgentCore actions permitted by applicable SCPs at the root, every parent OU and the account; no matching explicit Deny remains.
- Approval for either regional public HTTPS endpoints or an existing PrivateLink path.
- Approval to process synthetic data in SANDBOX mode, plus a cost owner and cleanup date.

Stop if the SCP or network decision is unresolved. An IAM administrator cannot override an SCP deny by attaching AdministratorAccess.[50][51]

### IAM/platform owner

Deliverable:

- An execution role trusted by `bedrock-agentcore.amazonaws.com`, initially without production-data access.
- A deployer identity allowed to Create/Get/List/DeleteCodeInterpreter, manage POC tags and PassRole on that execution role only.
- A caller identity allowed Start/Invoke/Stop/Get/List sessions on the created custom interpreter ARN.
- Any required permission boundaries and federated session policies permit those actions too.[25][26][52]

Role creation is a platform/bootstrap operation. It is not necessary to grant IAM administration to the local script or sandbox.

### Developer workstation or existing runner

Deliverable:

- Approved Python (the complete framework track needs Python 3.11+; validated here on 3.14.7).
- Current AWS CLI v2 with `bedrock-agentcore-control` commands, normal company credential login and trusted corporate CA/proxy configuration.
- HTTPS access to AgentCore and credential endpoints; later, a separately approved model path.
- Access to an approved Python package repository. Terraform is **not** required yet.

### Required versus optional AWS services

- **Required for the baseline:** AgentCore Code Interpreter and applicable AWS authentication/IAM permissions.
- **Not required for the first direct script:** Bedrock model inference. You send code directly; no LLM is involved.[9]
- **Optional S3:** only for an explicit S3 storage exercise. The API can upload/download files without your own bucket.[8][9]
- **Optional Bedrock model access:** needed by the supplied agent examples, not by Code Interpreter itself. `bedrock:*` and `bedrock-agentcore:*` are different IAM namespaces.[25]
- **Optional VPC/EC2 permissions and PrivateLink:** only for selected private connectivity or private-resource access. Keep caller-to-service and sandbox egress decisions separate.[1][2]
- **Optional Secrets Manager/KMS, logs/telemetry, EFS or S3 Files:** only when those features are explicitly used.[49]
- **Optional ECR/Runtime host dependencies:** only if you later deploy your agent host that way. Do not add them to a Code Interpreter-only POC.[6]
- **Optional Cloud Control and Terraform-backend services:** depend on your IaC provider and company state backend; native AWS provider support avoids an AWSCC-only management dependency.[27][29]

For conditional services, review both their IAM permissions and their SCP ceilings. Allowing AgentCore does not automatically permit S3 reads, KMS decrypt, model inference, EC2 endpoint creation or IAM PassRole.

## 3. Unblock SCPs before debugging application code

### 3.1 Identify the actual denial

Keep the following evidence in an internal security ticket, not in a public artifact:

- Exact failing IAM action, region, caller role ARN and resource ARN.
- Error text and request ID; timestamp and management event details when available.
- Whether it is an explicit SCP deny or a missing SCP allow.
- The account's root-to-OU-to-account policy path.

AccessDenied messages can identify a policy type or ARN, but not every service emits full enhanced context. Multiple policy types can block the same request while the message mentions only one. Resolving the first deny does not prove all permissions are now correct.[52]

The relevant IAM namespace is **`bedrock-agentcore:`**. The SDK/CLI management client is called **`bedrock-agentcore-control`**, but **`bedrock-agentcore-control:*` is not the IAM service prefix**. Model inference permissions normally use `bedrock:` separately.[25]

An approved read-only diagnostic command is:

```bash
aws bedrock-agentcore-control list-code-interpreters \
  --region us-west-2 --max-results 10
```

List success proves only that list action works for that identity. It does not prove creation, PassRole, session invocation or model inference is permitted. There is no universal AgentCore authorization dry run that replaces controlled action-by-action tests.

### 3.2 Ask the organization administrator to inspect the full policy path

An authorized organization operator can use:

```bash
aws organizations list-parents --child-id "$POC_ACCOUNT_ID"
aws organizations list-policies-for-target \
  --target-id "$POC_ACCOUNT_ID" --filter SERVICE_CONTROL_POLICY
aws organizations describe-policy --policy-id "$POLICY_ID"
```

Repeat `list-parents` for each returned OU until reaching the root. Run `list-policies-for-target` for **each** OU and the root, then inspect every applicable policy's content and conditions. The account-only list returns directly attached policies, not the inherited policy set. Preserve pagination; do not use `--no-paginate` to draw a completeness conclusion.[53][58]

These read operations require authorized Organizations access, generally from the management account or an appropriate delegated administrator. A developer failing to enumerate the organization's policies is not evidence that no SCP exists. Ask the organization/security owner for the evaluation instead.

### 3.3 Case A: allow-list SCPs omit AgentCore

For an action to pass the SCP layer, the applicable policy set must permit it at **every level** from root through all OUs to the account. Policies at the same level can contribute allows, but an allow at the account cannot compensate for an implicit deny at a parent.[51]

`policy-examples/scp-allowlist-addition.json` is a **reviewable additive statement**, not a replacement for the company's full service allow-list. It permits the Code Interpreter POC actions in us-west-2:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PermitCodeInterpreterPocCeiling",
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:CreateCodeInterpreter",
        "bedrock-agentcore:GetCodeInterpreter",
        "bedrock-agentcore:ListCodeInterpreters",
        "bedrock-agentcore:DeleteCodeInterpreter",
        "bedrock-agentcore:TagResource",
        "bedrock-agentcore:UntagResource",
        "bedrock-agentcore:ListTagsForResource",
        "bedrock-agentcore:StartCodeInterpreterSession",
        "bedrock-agentcore:InvokeCodeInterpreter",
        "bedrock-agentcore:StopCodeInterpreterSession",
        "bedrock-agentcore:GetCodeInterpreterSession",
        "bedrock-agentcore:ListCodeInterpreterSessions"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "us-west-2"
        }
      }
    }
  ]
}
```

The action set includes setup/read/tagging, execution lifecycle and teardown. Do not omit Stop/Delete just because the initial goal is to start a session. The exact action names were checked against AWS's published authorization catalog.[25][56]

This statement does not allow IAM PassRole or role creation. If the SCP strategy allow-lists those services/actions too, platform owners must ensure their existing IAM/bootstrap ceiling permits the narrowly scoped prerequisites. Apply region conditions to the regional AgentCore actions; do not blindly apply the same us-west-2 condition to global IAM/Organizations operations.

**Do not replace the organization's SCP with this snippet or detach FullAWSAccess as a POC shortcut.** It does not include the company's other needed services or guardrails. SCPs define maximum permissions and grant no IAM permissions themselves.[50]

### 3.4 Case B: an explicit Deny blocks AgentCore

An extra Allow cannot override the Deny. The authorized owner must change the blocking statement, its scope, or its approved exception in **every matching policy**. Keep unrelated restrictions intact.[50][51]

For example, this hypothetical existing statement blocks all AgentCore actions:

```json
{
  "Effect": "Deny",
  "Action": "bedrock-agentcore:*",
  "Resource": "*"
}
```

An organization owner might replace that **particular service-specific deny** with a reviewed principal exception:

```json
{
  "Sid": "DenyAgentCoreExceptApprovedPocRoles",
  "Effect": "Deny",
  "Action": "bedrock-agentcore:*",
  "Resource": "*",
  "Condition": {
    "ArnNotEquals": {
      "aws:PrincipalArn": [
        "arn:aws:iam::111122223333:role/ApprovedAgentCorePocDeployer",
        "arn:aws:iam::111122223333:role/ApprovedAgentCorePocCaller"
      ]
    }
  }
}
```

This is an **illustrative policy-edit pattern**, not a ready-to-attach exception to an existing deny. Attaching it alongside the original unconditional deny changes nothing. In a real change, preserve the company's original conditions and every unrelated service restriction; use actual approved role ARNs, including paths. AWS SSO/Identity Center roles need their real generated IAM role ARN, not a guessed display name or an STS session ARN.[57]

The example exception covers the whole AgentCore namespace for those identities at that deny statement. Therefore security must review the role permissions/boundaries and the remaining SCP hierarchy; this is not an action-scoped exemption. Prefer the smallest POC account/role scope and an expiry/review date. A region deny, a second service deny, or a missing allow can still block the roles.

Other common explicit-deny shapes:

- **Deny everything except an approved `NotAction` list:** add only reviewed AgentCore action patterns to the existing exception list. A separate Allow does not bypass that deny.
- **Region guardrail:** ensure us-west-2 is approved for the specific regional path. Do not weaken the entire region policy or remove global-service exceptions.
- **Network-origin guardrail:** if policy requires a VPC endpoint, satisfy the approved private API path; changing the tool's network mode does not fix the caller's origin.
- **Mandatory tags or VPC conditions:** supply the approved values where supported, or request a narrowly scoped exception for this SANDBOX baseline. Do not invent a network-mode condition key absent from the action's authorization reference.[25][52]

### 3.5 What if security wants to enable broader AgentCore products?

`policy-examples/scp-broader-agentcore-optional.json` contains an optional service-level ceiling:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "OptionalWholeAgentCoreNamespaceCeiling",
      "Effect": "Allow",
      "Action": "bedrock-agentcore:*",
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "us-west-2"
        }
      }
    }
  ]
}
```

Use this only if security intentionally approves the whole namespace in us-west-2. It permits more products and future actions; it is **not the default recommendation** for a Code Interpreter POC. It still cannot override Deny, grant IAM privileges, approve other AWS services or guarantee product availability. Regional exceptions for other products must be reviewed separately.[25][50][51]

Use this expansion inventory instead of turning every role into an administrator:

- **Code Interpreter:** the minimal POC policy above; optional S3/private data permissions only when used.
- **Browser:** Create/Get/List/DeleteBrowser and Start/Get/List/StopBrowserSession families; streaming/profile permissions only when used. Public browsing and profiles require separate network/storage review.
- **Runtime:** Create/Get/Update/DeleteAgentRuntime, endpoints and InvokeAgentRuntime/StopRuntimeSession as applicable. PassRole and the selected deployment artifact path are separate prerequisites.
- **Memory:** Create/Get/List/Update/DeleteMemory plus the event/record actions the application actually invokes; extraction roles/models are conditional.
- **Gateway:** gateway/target management and invocation permissions according to its ingress authentication and target types; add only required Lambda, OpenAPI, MCP, identity or network dependencies.
- **Identity:** specific workload identity, token-vault and credential-provider operations; provider credentials and secret/encryption policies are separate boundaries.
- **Policy/evaluations/observability:** policy/evaluator/configuration actions as used, associated execution roles and telemetry/model permissions. Code Interpreter does not require these products.

The AWS authorization catalog is the action-level source of truth; the list above is an expansion checklist, not a complete deployment policy for each product. Both CLI planes use the same `bedrock-agentcore` IAM namespace.[25][56]

### 3.6 Change request you can send to security

```text
Request: time-bounded AgentCore Code Interpreter POC
Account/OU: [internal approved account and hierarchy]
Region: us-west-2
Data: synthetic files only
Network: SANDBOX; approved API path [regional HTTPS or existing PrivateLink]
Identities: approved deployer, approved local application caller
SCP change: remove/except the matching explicit deny OR add the minimal
  AgentCore action ceiling at each missing level; keep unrelated guardrails
IAM prerequisites: scoped PassRole for the existing execution role;
  platform-owned role/policy provisioning where needed
Not requested: Runtime, ECR, NAT, production data, org-wide FullAccess
Verification: create/get -> start/invoke/stop -> delete; independent negative tests
Rollback: stop sessions, delete POC tool, remove dedicated permissions and
  restore/expire the approved policy change through normal change control
```

**Gate:** the organization owner confirms the actual policy path is unblocked. Do not attempt alternate accounts/roles, disable guardrails, or look for a way around an intentional denial.

## 4. Prepare IAM roles and generate request files

Set the non-secret inputs explicitly before running the generator. For example, replace the documentation account ID below with your approved account; do not use it literally:

```bash
export POC_ACCOUNT_ID='111122223333'
export EXECUTION_ROLE_NAME='ApprovedAgentCorePocExecution'
```

Run the generator only after setting these values. `APPROVED_BOUNDARY_ARN`, `DEPLOYER_ROLE_NAME` and `CALLER_ROLE_NAME` in the platform-only commands below are values your IAM owner supplies; they are not inferred by the script.

From the downloaded reference bundle's `reference/` directory, run the standard-library-only generator with your approved account ID and execution-role name:

```bash
python prepare_poc.py \
  --account-id "$POC_ACCOUNT_ID" \
  --execution-role-name "$EXECUTION_ROLE_NAME" \
  --output-dir generated
```

This writes local JSON only. It does not call AWS or attach SCP/IAM policies. It refuses to overwrite existing files so you cannot silently replace a reviewed request. If your organization uses IAM role paths, have the platform team adapt the templates to the actual ARN; this small generator intentionally accepts a pathless role name.

Files for review:

- `generated/execution-role-trust.json`: same-account service trust.
- `generated/create-interpreter.json`: SANDBOX, underscore-only tool name and POC purpose tag.
- `generated/iam-deployer.json`: regional tool management plus exact-role PassRole; no caller execution or IAM administration.
- `generated/scp-allowlist-addition.json`: minimal AgentCore ceiling.
- `generated/scp-broader-agentcore-optional.json`: broader alternative, not needed by default.

### 4.1 Platform creates or supplies the execution role

Prefer an existing dedicated POC role with the approved trust and no production-data access. If the platform owner is authorized to create it through CLI, an example is:

```bash
aws iam create-role \
  --role-name "$EXECUTION_ROLE_NAME" \
  --assume-role-policy-document file://generated/execution-role-trust.json \
  --permissions-boundary "$APPROVED_BOUNDARY_ARN"

aws iam get-role --role-name "$EXECUTION_ROLE_NAME"
```

The boundary argument is company-specific; use the company's approved boundary, and omit it only if policy explicitly permits role creation without one. Role creation/tagging/permission management belongs to the platform identity's own IAM/SCP approvals. The POC deployer policy deliberately does not grant it.

For the first synthetic computation and API-file exercise, attach no downstream production-data permissions to the execution role. The execution role is what sandbox code can use for AWS data access; the local caller's data permissions are not the sandbox's data permissions.[8][26]

### 4.2 Platform grants the deployer identity

Apply the generated `iam-deployer.json` to the approved deployer role/permission set through your company's workflow. For an ordinary IAM role, an authorized IAM operator can use the inline-policy operation:[59]

```bash
aws iam put-role-policy \
  --role-name "$DEPLOYER_ROLE_NAME" \
  --policy-name AgentCorePocDeployment \
  --policy-document file://generated/iam-deployer.json
aws iam get-role-policy \
  --role-name "$DEPLOYER_ROLE_NAME" \
  --policy-name AgentCorePocDeployment
```

For Identity Center-managed roles, update the owning permission set/provisioning workflow rather than editing the generated role arbitrarily. Caller permissions are attached **after** the interpreter ARN is known.

### 4.3 Keep four identity boundaries separate

- **Organization owner:** SCP inspection/change approval. Neither the local script nor Terraform should modify SCPs as a side effect of this POC.
- **Deployer:** custom tool management and scoped PassRole.
- **Caller:** session execution on the exact returned custom ARN, plus separately approved model inference later.
- **Execution role:** only the downstream access executed code needs.

The VPC extension also has a distinct AWS network service-linked role. SCPs do not restrict service-linked roles, but your normal deployer/execution/caller roles and first-time role-creation calls remain subject to their own controls. Do not infer that all service-assumed roles are exempt.[30][50]

**Gate:** the execution role exists with the right trust/boundary; the deployer has its scoped identity policy and applicable SCP clearance. No need to provision a VPC for the baseline.

## 5. Prepare the local workstation

Commands use Bash-compatible quoting. Use the company's standard SSO/credential process:

```bash
export AWS_PROFILE=company-poc
export AWS_REGION=us-west-2
export AWS_DEFAULT_REGION=us-west-2
export AWS_STS_REGIONAL_ENDPOINTS=regional
export AWS_PAGER=''
aws sts get-caller-identity
aws --version
python --version
```

Check the account ID and effective role. A successful STS identity lookup does not prove AgentCore permissions. Login under the **deployer** profile for creation; later switch to the **caller** profile for local execution.

From `reference/`, create a small initial environment:

```bash
python -m venv .venv-direct
source .venv-direct/bin/activate
python -m pip install 'boto3==1.43.113'
python -m pip check
```

Use the approved internal package mirror/CA/proxy configuration where required. Do not disable TLS verification or install the full agent stack just to prove a direct code call. For PowerShell or another shell, use its equivalent environment and venv activation syntax.

The Code Interpreter service API is remote. Your workstation must reach its normal regional endpoint or the approved PrivateLink/private-DNS path. An SCP approval does not establish that network route.[1]

## 6. Create the interpreter manually first

Choose **one** creation path. Do not run both against the same tool name. Keep the console/CLI-created tool unmanaged by Terraform until the adoption stage.

### 6.1 Console path

1. Sign in using the approved deployer identity and select **us-west-2**.
2. Open Amazon Bedrock AgentCore, then **Built-in tools → Code Interpreter**.
3. Create a custom tool named `agentcore_poc`.
4. Set the description to `Deep Agents Code Interpreter POC` and the purpose tag to `Purpose=agentcore-code-interpreter-poc`.
5. Choose **SANDBOX**, not PUBLIC and not VPC.
6. Select the existing dedicated execution role. Do not use automatic role creation unless the platform owner approved that extra IAM workflow.
7. Create the tool; wait for READY.
8. Copy the actual **code interpreter ID**, **custom resource ARN**, execution role and network mode from the resource details.[55]

The console may require list/read permissions to display roles and other UI elements beyond the minimal API policy. A UI dropdown failure does not prove the underlying create API is unsupported. Use the CLI with an approved explicit role ARN rather than broadly increasing permissions to satisfy every console panel.

### 6.2 CLI path

Use the request generated earlier:

```bash
aws bedrock-agentcore-control create-code-interpreter \
  --region us-west-2 \
  --cli-input-json file://generated/create-interpreter.json \
  --output json > created-interpreter.json
```

If the CLI exits nonzero, inspect the error before using that file. Do not blindly repeat a creation request after a network failure: check whether the tool was created first. A consistent `--client-token` can be supplied for controlled creation retries.[54]

Extract the ID and ARN, then read the resource back:

```bash
export AGENTCORE_CODE_INTERPRETER_ID="$(python -c \
  'import json; print(json.load(open("created-interpreter.json"))["codeInterpreterId"])')"
export AGENTCORE_CODE_INTERPRETER_ARN="$(python -c \
  'import json; print(json.load(open("created-interpreter.json"))["codeInterpreterArn"])')"

aws bedrock-agentcore-control get-code-interpreter \
  --region us-west-2 \
  --code-interpreter-id "$AGENTCORE_CODE_INTERPRETER_ID"
```

Wait for `READY`; investigate `CREATE_FAILED`. Confirm SANDBOX and the intended execution role. For console creation, export the two returned values manually instead of fabricating `created-interpreter.json`.

Use **`bedrock-agentcore-control create-code-interpreter`**, not the data-plane group used in some older introductory examples. The current CLI/API reference is the authority for request shape.[54]

### 6.3 Grant the local caller the exact tool ARN

Generate the caller policy in a fresh output directory:

```bash
python prepare_poc.py \
  --account-id "$POC_ACCOUNT_ID" \
  --execution-role-name "$EXECUTION_ROLE_NAME" \
  --interpreter-arn "$AGENTCORE_CODE_INTERPRETER_ARN" \
  --output-dir generated-after-create
```

Have the platform owner apply `generated-after-create/iam-caller.json` to the approved caller permission set or ordinary IAM role. An authorized IAM operator can use:

```bash
aws iam put-role-policy \
  --role-name "$CALLER_ROLE_NAME" \
  --policy-name AgentCorePocSessionAccess \
  --policy-document file://generated-after-create/iam-caller.json
aws iam get-role-policy \
  --role-name "$CALLER_ROLE_NAME" \
  --policy-name AgentCorePocSessionAccess
```

Then select the caller credential profile and confirm identity again. The caller policy contains Start/Invoke/Stop/Get/ListSession but no create/delete tool, PassRole or model inference permission.[25]

**ARN trap:** custom tools use `code-interpreter-custom/ID`. Do not substitute an account-owned `code-interpreter/*` wildcard copied from a built-in-tool example. Use the returned ARN exactly.[25]

**Gate:** one custom tool is READY; the caller policy references it; caller/deployer identities are distinguishable. You still have not needed Terraform or a model.

## 7. First local script: send code to the existing tool

Save the following as `local_execute.py`, or use the identical file in the reference bundle:

```python
"""First local Python -> remote AgentCore exercise. Explicitly billable when enabled."""
import argparse
import json
import uuid

import boto3
from botocore.config import Config


def consume(response):
    results = []
    for event in response["stream"]:
        if "result" not in event:
            raise RuntimeError(f"Service stream failure: {event}")
        result = event["result"]
        exit_code = result.get("structuredContent", {}).get("exitCode")
        if result.get("isError") or exit_code not in (None, 0):
            raise RuntimeError(f"Sandbox execution failed: {result}")
        results.append(result)
    if not results:
        raise RuntimeError("Service returned no results")
    return results


def run(client, interpreter_id):
    started = client.start_code_interpreter_session(
        codeInterpreterIdentifier=interpreter_id, name="local-poc",
        sessionTimeoutSeconds=600, clientToken=str(uuid.uuid4()),
    )
    sid = started["sessionId"]
    print(json.dumps({"session_id": sid, "interpreter_id": interpreter_id}))
    try:
        results = consume(client.invoke_code_interpreter(
            codeInterpreterIdentifier=interpreter_id, sessionId=sid,
            name="executeCode", arguments={
                "language": "python", "code":
                "import json; values=[10,20,30]; assert sum(values)==60; "
                "print(json.dumps({'total':sum(values)}))",
            },
        ))
        print(json.dumps(results, indent=2, default=str))
        return results
    finally:
        client.stop_code_interpreter_session(codeInterpreterIdentifier=interpreter_id, sessionId=sid)
        try:
            status = client.get_code_interpreter_session(
                codeInterpreterIdentifier=interpreter_id, sessionId=sid)["status"]
        except client.exceptions.ResourceNotFoundException:
            status = "TERMINATED"
        if status != "TERMINATED":
            raise RuntimeError(f"Cleanup not yet verified: session={sid} status={status}")
        print(json.dumps({"session_id": sid, "cleanup": status}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--interpreter-id", required=True)
    parser.add_argument("--allow-live", action="store_true")
    args = parser.parse_args()
    if not args.allow_live or args.interpreter_id.startswith("aws."):
        parser.error("Provide --allow-live and the custom interpreter ID created earlier")
    client = boto3.client("bedrock-agentcore", region_name="us-west-2", config=Config(
        connect_timeout=10, read_timeout=120, retries={"mode": "standard", "total_max_attempts": 1},
    ))
    run(client, args.interpreter_id)


if __name__ == "__main__":
    main()
```

Run it with the caller profile:

```bash
export AWS_PROFILE=company-poc-caller
aws sts get-caller-identity
python local_execute.py \
  --interpreter-id "$AGENTCORE_CODE_INTERPRETER_ID" \
  --allow-live
```

The script starts a remote session, executes a small standard-library computation, consumes the full result stream, stops the session and reads back termination. It disables automatic SDK request retries for this tiny example to avoid retrying unknown execution side effects.

**Pass condition:** inspect the real returned total (60), no streamed/tool error, and verified session termination. If cleanup returns a non-terminated state, record the session ID and follow up; do not call that a clean success. No pre-generated AWS output is included here.

Do not create a new interpreter inside an application request. Interpreter configuration is a provisioned resource; a session is its temporary execution context.[26]


## 8. Stronger service smoke tests before a model
Do this before calling a model. It separates IAM/API/service problems from model and Deep Agents behavior.

```bash
python direct_smoke.py \
  --interpreter-id "$AGENTCORE_CODE_INTERPRETER_ID" \
  --allow-live
```

This **billable live command** starts two 600-second sessions, transfers a non-UTF-8 file and compares returned bytes, runs a computation, checks that a marker from the first session is absent from the second, checks an explicit exit code 7, and stops both sessions in `finally`. It reads each session back to confirm termination or that it is no longer addressable. Evidence goes to `artifacts/direct-smoke.json`.

Expected acceptance conditions, not pre-generated output:

- Two distinct session IDs.
- Identical bytes after write/read.
- Computation and isolation assertions succeed inside their intended sessions.
- The failing shell command exposes exit code 7.
- Every session stop is verified; `cleanup_errors` is empty.

The code consumes the entire lazy response stream and rejects streamed exceptions, `isError` results and nonzero structured exit status. `HTTP 200` alone is not execution success.[9]

If the smoke test fails, stop here. Save the request ID/error and session IDs in the restricted POC ticket, then use the troubleshooting section. Do not add a model to obscure the failure.

The full script is in the reference bundle. Its core API sequence is:

```python
response = client.start_code_interpreter_session(
    codeInterpreterIdentifier=approved_custom_id,
    sessionTimeoutSeconds=600,
)
session_id = response["sessionId"]
try:
    response = client.invoke_code_interpreter(
        codeInterpreterIdentifier=approved_custom_id,
        sessionId=session_id,
        name="executeCode",
        arguments={"language": "python", "code": "print(1 + 1)"},
    )
    results = collect(response)  # strict parser in direct_smoke.py
finally:
    client.stop_code_interpreter_session(
        codeInterpreterIdentifier=approved_custom_id,
        sessionId=session_id,
    )
```

Never automatically retry an execution request with side effects just because the response stream broke. The command may already have run. Session-start idempotency and execution idempotency are different concerns.[7][9]

## 9. Add the framework dependencies
Use the official LangChain-maintained integrations. A custom sandbox adapter is unnecessary for the demonstrated Deep Agents or LangChain paths.[36][44][47]

### Important release/source mismatch

The retrieved published `langchain-agentcore-codeinterpreter` **0.0.5** does not behave like current upstream source. Local fixtures reproduced these differences:

- An AWS result with `structuredContent.exitCode = 7` was returned as exit code **0** by the release; the candidate returned **7**.
- `execute(..., timeout=1)` ignored the timeout in the release; the candidate wrapped execution with an in-sandbox GNU `timeout` command.
- `writeFiles` with `isError=True` could be reported as a successful upload by the release; the candidate reported an error.
- Upstream has additional `.create()` and context-manager lifecycle APIs that are absent from the release.[38][44]

These are **offline contract observations**, not proof of every behavior on AWS. Do not rely on the release's exit code as your only success check. Timeout wrapping also requires the GNU utility in the actual sandbox and is not a server-side cancellation guarantee.

### Track A: reviewed source-pinned candidate (recommended for evaluating fixes)

The supplied `requirements-candidate.txt` replaces only the sandbox package with this immutable upstream source:

```text
langchain-agentcore-codeinterpreter @ git+https://github.com/langchain-ai/langchain-aws.git@a0e80b9febaf21cf1cead8f0dc16b3ffd8633976#subdirectory=libs/agentcore-codeinterpreter
```

That VCS build/install was executed successfully in an isolated environment, and the installed candidate passed the offline tests. It still identifies its package version as 0.0.5, so **version number alone cannot distinguish it from the released wheel**. Record the source commit or internal wheel digest.

Company gate: review the source, run your dependency/security process, and preferably promote a built wheel into your private package repository. An immutable commit is reproducible provenance, not a security approval or a promise of production readiness.

### Track B: published release, limited exploratory use

`requirements-release.lock` captures the published wheel and resolved dependencies. Use this only to reproduce the baseline integration and the known defects, or when company policy forbids a VCS candidate. Keep synthetic inputs, verify results independently, and do not mark timeout/error-handling acceptance complete until the chosen release passes those tests.

The primary direct API smoke test remains useful regardless of which framework track is approved.

### Install and run offline checks

From `reference/`, using the company's approved Python/package mirror:

```bash
python -m venv .venv
# Activate with your shell's normal venv activation command.
python -m pip install -r requirements-candidate.txt
python -m pip check
python offline_verify.py
```

For the published release, use a separate environment:

```bash
python -m pip install -r requirements-release.lock
EXPECT_FIXED=0 python offline_verify.py
```

The release fixture passing means it reproduced the documented defects; it does **not** mean those defects are acceptable. The candidate test intentionally logs a caught upload-error traceback while testing failure handling.

The installed snapshot includes `bedrock-agentcore==1.24.1` and `deepagents==0.7.25`.[39][40]

It also includes `langchain==1.4.5`, `langchain-aws==1.8.2`, and resolved `boto3/botocore==1.43.113`.[41][42] Do not update one dependency casually during the POC; refresh the lock and rerun the tests together.

## 10. Deep Agents: use the existing tool as the sandbox
The integration boundary is **`create_deep_agent(..., backend=AgentCoreSandbox(...))`**. This gives the agent sandbox-backed filesystem and shell execution rather than access to your workstation filesystem.[36][44]

The exact portable lifecycle used by the reference is:

```python
from bedrock_agentcore.tools.code_interpreter_client import CodeInterpreter
from langchain_agentcore_codeinterpreter import AgentCoreSandbox
from deepagents import create_deep_agent

interpreter = CodeInterpreter(region="us-west-2")
interpreter.start(
    identifier=approved_custom_id,
    session_timeout_seconds=1800,
)
try:
    backend = AgentCoreSandbox(interpreter=interpreter)
    agent = create_deep_agent(model=model, backend=backend)
    result = agent.invoke({"messages": [
        {"role": "user", "content": "Use execute to run pwd and report it."}
    ]})
finally:
    interpreter.stop()
```

**Do not copy imaginary constructor arguments:** `AgentCoreSandbox` takes `interpreter=`, not `region=`, `client=`, or `session_id=`. `CodeInterpreter` takes `region=` and optional `session=`. Select the custom interpreter in `.start(identifier=...)`.[44][45]

### Run the supplied integration

Set `BEDROCK_MODEL_ID` to the exact **company-approved, tool-capable model ID** available through the intended route in us-west-2. The guide intentionally does not choose a cross-region inference profile or assume model entitlement.

```bash
export BEDROCK_MODEL_ID='REPLACE_WITH_APPROVED_MODEL_ID'
python run_agent.py deep --allow-live
```

The supplied `run_deep` function uploads `input.txt`, downloads it to verify the bytes, asks the agent to read it through the shell, and stops its session. Inspect the printed tool message, not only the final assistant answer.

The model object uses:

```python
from langchain_aws import ChatBedrockConverse
model = ChatBedrockConverse(
    model_id=approved_model_id,
    region_name="us-west-2",
    temperature=0,
    max_tokens=1024,
)
```

This model choice adds its own IAM/inference costs and network route. Restrict it to the approved model resource(s); do not grant all-model permissions just to unblock a test. Validate the precise InvokeModel/streaming permissions needed by your chosen model/inference path with the platform owner. LangChain tracing and any outbound telemetry must follow company policy.

### File transfer and paths

Backend methods use these shapes:[44]

```python
uploaded = backend.upload_files([("input.csv", b"amount\n10\n20\n30\n")])
if uploaded[0].error:
    raise RuntimeError(uploaded[0].error)
readback = backend.download_files(["input.csv"])[0]
if readback.error or readback.content != b"amount\n10\n20\n30\n":
    raise RuntimeError("Upload verification failed")
```

Prepare nested directories before bulk upload. Prefer relative paths and discover the real working directory with `execute("pwd")`. Do not copy `/root/...` paths from another sandbox provider. Download responses contain bytes or an error; inspect each response rather than assuming a list of results implies success.[44]

### Lifecycle and isolation rules

- One backend/session per user task in the initial POC; do not share it across unrelated users.
- Pass the provisioned ID explicitly. A bare SDK `.start()` selects the built-in interpreter.
- Never reuse a backend after stopping its interpreter. SDK `invoke` may implicitly call bare `start()` when identifiers are missing, creating a different default session.
- Export required artifacts before stopping or TTL expiry. Do not treat ephemeral files as durable storage.
- Monitor failed stop calls; `finally` attempts cleanup but cannot guarantee it when the network fails.[45]

## 11. Plain LangChain: native toolkit alternative
Use this path to compare an explicit tool-based agent with Deep Agents' richer backend integration. The supported factory is asynchronous:[47]

```python
from langchain.agents import create_agent
from langchain_aws.tools import create_code_interpreter_toolkit

toolkit, tools = await create_code_interpreter_toolkit(
    region="us-west-2",
    code_interpreter_identifier=approved_custom_id,
)
config = {"configurable": {"thread_id": unique_task_id}}
try:
    agent = create_agent(model=model, tools=tools)
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "Use execute_code to calculate 10+20+30."}]},
        config=config,
    )
finally:
    await toolkit.cleanup()
```

Run the supplied example with:

```bash
python run_agent.py langchain --allow-live
```

It uploads a text file and reads it through `execute_command`. Reuse the same thread configuration for upload and agent calls; different keys can select different sessions. A per-task toolkit makes ownership simple for the POC.[47]

**Limitations in the inspected toolkit:** it creates sessions lazily, uses the standard AWS credential chain and default 900-second TTL, has no injected boto3-session/TTL factory parameter, and reduces tool responses to text. Binary output and structured failures need independent verification. Cleanup logs errors rather than reliably propagating them, so read session state back during acceptance. The toolkit is a useful integration, not the authority for a pass/fail security result.[47]

Choose Deep Agents when you need its filesystem/shell backend contract. Choose the plain toolkit when you want selected code/file tools inside an existing LangChain agent. Neither requires a custom adapter for this POC.

## 12. Verify a useful output: synthetic CSV analysis
After the hello-file examples pass, extend `run_deep` inside its existing session lifetime:

1. Upload `sales.csv` containing only synthetic values.
2. Ask the agent to create and execute a Python script that reads it, computes total sales, and writes `report.json`.
3. Download `report.json` through the backend **before** `finally` stops the interpreter.
4. Parse the file on the host and assert the expected value. Do not use the model's final prose as the assertion.

Input:

```csv
team,amount
A,10
B,20
A,30
```

Prompt:

```text
Read sales.csv from the sandbox filesystem. Write and execute a Python
script using the standard library. Produce report.json containing
{"total": 60, "by_team": {"A": 40, "B": 20}}. Do not install packages.
```

Host-side check, inside the same `try` block:

```python
import json
from pathlib import Path
response = backend.download_files(["report.json"])[0]
if response.error or response.content is None:
    raise RuntimeError(f"Missing report: {response.error}")
report = json.loads(response.content)
assert report == {"total": 60, "by_team": {"A": 40, "B": 20}}
Path("artifacts").mkdir(exist_ok=True)
Path("artifacts/report.json").write_bytes(response.content)
```

This is a live extension exercise, not an already executed cloud example. Add a second input and change one amount to prove the script reads input instead of reproducing the prompt's expected JSON. For production evaluation, use hidden expected outputs and verify the execution trace.

## 13. Terraform comes after the working local path

Your manual tool is already enough to run every application exercise. Terraform now makes the infrastructure repeatable; it should not force you to debug SCPs and agent code at the same time.

### 13.1 Support, provider choices and coverage

**Yes: Terraform supports the Code Interpreter resource directly.** This runbook pins `hashicorp/aws` to **6.68.0**, whose resource schema includes `SANDBOX`, `PUBLIC`, and `VPC` plus nested subnet/SG configuration.[13][14]

The native resource is:

```hcl
resource "aws_bedrockagentcore_code_interpreter" "poc" {
  name               = "agentcore_poc"
  execution_role_arn = var.execution_role_arn
  network_configuration {
    network_mode = "SANDBOX"
  }
}
```

`name` must start with a letter and contain only letters, digits and underscores, up to 48 characters. Some provider examples use hyphens despite the service pattern. Use `agentcore_poc`; preserve the generated interpreter ID exactly, including any suffix/hyphen.[18]

The verified native provider replaces the interpreter when its name, description, execution role, or network configuration changes. Treat changing SANDBOX to VPC as a replacement: drain sessions, apply the replacement, refresh the application ID and caller policy, and repeat acceptance tests.[14]

### Alternative: AWSCC

`hashicorp/awscc` **1.105.0** exposes `awscc_bedrockagentcore_code_interpreter_custom`, mapping to CloudFormation's custom interpreter resource. It also supports VPC in the retrieved schema. Its nested `network_configuration` is an **object attribute**, whereas the native provider uses a **block**.[15][16][17]

Use AWSCC only if it fits the company's provider policy or a needed feature is better supported there. It adds Cloud Control API permissions/connectivity and does not eliminate downstream AgentCore permissions. Do not manage one interpreter with both providers.[27][28][29]

### Coverage limits

The native and AWSCC schemas verified for this snapshot do not expose every current service option. In particular, API-level `filesystemConfigurations` must not be assumed available as a Terraform argument. Optional certificate shapes/count limits also differ. Keep mounts/certificates out of the initial POC; reassess provider coverage when you need them.[14][16][18]

Avoid `null_resource` plus shell provisioning for a resource Terraform already supports. If your company's provider pin is older, check its actual schema, request a provider upgrade, or use an approved AWSCC version. Do not silently bypass infrastructure governance through application startup code.

### 13.2 Choose adoption or a separate resource

**Recommended: adopt the manually created interpreter.** Use one owning state and match its current configuration before importing:

1. Have the infrastructure owner approve state/backend, account, execution role and ownership.
2. Copy `terraform.tfvars.example` to a private `terraform.tfvars`. Supply the same account/execution role, an approved owner, and SANDBOX mode.
3. Ensure resource name and description in `main.tf` exactly match the console/CLI-created tool. The CLI payload supplied here uses matching values.
4. Initialize the company backend/provider and run the local validation/mock tests.
5. Import by interpreter ID. Import changes Terraform state; it does not itself recreate the interpreter.
6. Review the first plan. Resolve unexpected replacements before applying. An Owner tag added by provider default tags is expected only if the platform approves it.

```bash
terraform -chdir=terraform/interpreter init
terraform -chdir=terraform/interpreter validate
terraform -chdir=terraform/interpreter test
terraform -chdir=terraform/interpreter import \
  aws_bedrockagentcore_code_interpreter.poc \
  "$AGENTCORE_CODE_INTERPRETER_ID"
terraform -chdir=terraform/interpreter plan -out=adopt.tfplan
terraform -chdir=terraform/interpreter show -no-color adopt.tfplan
```

Do not apply a replacement just to make the plan green. Mutable/default tags and immutable name/description/network/role fields are different concerns. If a separate Terraform-owned interpreter is desired, deliberately use a distinct valid name such as `agentcore_poc_iac`, record the second ID, update caller policy/configuration, rerun acceptance and delete the old manual tool through its original ownership path.[13][14]

### 13.3 Terraform provisioning procedure

The following is the full reference-root procedure for an intentionally Terraform-owned resource. For adoption, import before applying it; do not run a second creation against an existing same-name tool.

Use `reference/terraform/interpreter/`. The root:

- Restricts the provider to the explicitly supplied company account and `us-west-2`.
- Defaults to `SANDBOX` with no subnets or security groups.
- Requires an explicit execution-role ARN and owner.
- Excludes PUBLIC mode.
- Emits the interpreter ID/ARN and caller policy.
- Supports an optional VPC extension with input validation.

### Prepare state and inputs

Use the company's existing backend convention. The reference intentionally omits a backend block because bucket/workspace/locking settings are company-specific. Local state is acceptable only if your company permits it; protect state and never commit it.

Copy `terraform.tfvars.example` to a private `terraform.tfvars`, replace the example account/role/owner, and keep `network_mode = "SANDBOX"`. Do not supply VPC inputs for this baseline.

### Validate, review, apply

From the reference directory:

```bash
terraform -chdir=terraform/interpreter init
terraform -chdir=terraform/interpreter fmt -check -recursive
terraform -chdir=terraform/interpreter validate
# Mock-provider tests; Terraform >=1.7. No live AWS resources.
terraform -chdir=terraform/interpreter test

# The commands below require company approval and AWS access.
terraform -chdir=terraform/interpreter plan -out=poc.tfplan
terraform -chdir=terraform/interpreter show -no-color poc.tfplan
terraform -chdir=terraform/interpreter apply poc.tfplan
```

Use your CI approval process, not an unattended `-auto-approve`. Review that only the intended interpreter is created and that no VPC, NAT gateway, Runtime or ECR resources appear.

```bash
export AGENTCORE_CODE_INTERPRETER_ID="$(terraform \
  -chdir=terraform/interpreter output -raw code_interpreter_id)"
terraform -chdir=terraform/interpreter output -raw code_interpreter_arn
terraform -chdir=terraform/interpreter output -raw caller_policy_json
aws bedrock-agentcore-control get-code-interpreter \
  --region us-west-2 \
  --code-interpreter-id "$AGENTCORE_CODE_INTERPRETER_ID"
```

**Gate:** management read-back reports `READY` and `SANDBOX`, with the intended execution role. Have the emitted caller policy attached through the approved IAM workflow. The operator performing this management read needs GetCodeInterpreter; do not add that administrative permission to every application caller merely for a one-time check.

### Existing resources

If an approved custom interpreter already exists, either consume it without claiming Terraform ownership or import it into the chosen state through a reviewed change. Native import uses its interpreter ID, not the full ARN:[13]

```bash
terraform -chdir=terraform/interpreter import \
  aws_bedrockagentcore_code_interpreter.poc \
  "$AGENTCORE_CODE_INTERPRETER_ID"
```

Inspect the subsequent plan before applying. Never import platform-owned resources into a throwaway state without agreeing ownership and teardown.
## 14. Negative tests and isolation checks
Run these in a dedicated synthetic session. Record the command, observed result, session ID and package/source identity.

### Command failures

`sh -c 'exit 7'` must not be treated as success. Compare direct API `structuredContent.exitCode` with `backend.execute(...).exit_code`. The released adapter issue is a reason to fail this gate, not to remove the test.[9][38][44]

### Execution timeout

For the candidate, try `backend.execute("sleep 10", timeout=1)`. Measure elapsed time with a host monotonic clock and verify a non-success timeout result. First verify GNU `timeout` exists in the sandbox. A client read timeout is not a command deadline, and a session TTL is not a per-command timeout.[44][45]

### Missing/binary files

Read a nonexistent path and verify an explicit failure. Round-trip arbitrary non-UTF-8 bytes and compare them on the host. Add a nested-directory test; do not infer directory creation from a flat-file success.

### TTL expiry

Start a dedicated short-TTL session (AWS recommends at least 60 seconds). After expiry, the old session must no longer run code. Download needed artifacts first. Expiry is **absolute**, regardless of activity, not an idle timeout.[7]

### Cross-session isolation

Write a unique marker in session A. Confirm session B cannot read that marker from its scratch filesystem. The direct smoke includes this test. Shared S3/EFS storage, if later added, has a different isolation boundary.[4][49]

### Least privilege

With security approval, demonstrate that a separate test identity without permission cannot invoke the tool and that the execution role cannot access an unrelated synthetic bucket/object. Never test denial by probing production data. A caller having no S3 policy does not prove sandbox code has no S3 access; the execution identity is separate.

### Egress

If no public internet egress is required, test a security-approved destination with a short timeout from inside the sandbox and review the observed behavior with security. Do not claim SANDBOX is an air gap; limited supported AWS access exists. For VPC mode, inspect routing/firewall controls as well as testing reachability.[2][3]

## 15. Optional: private API access without tool VPC mode
Use this when company policy requires the application's API traffic to stay on a private path. **You can keep the interpreter in SANDBOX mode.**[1][3]

For us-west-2:

```text
Session/invoke API:
com.amazonaws.us-west-2.bedrock-agentcore

Provision/get/delete API:
com.amazonaws.us-west-2.bedrock-agentcore-control
```

Use `reference/terraform/endpoints/` only if platform/network owners approve dedicated endpoint creation. If endpoints already exist, reuse their approved path instead of creating duplicate private-DNS endpoints. This optional root intentionally creates both planes; if only application access must be private, the platform can retain control-plane access through its existing approved management route.

### Required network decisions

- Endpoint VPC and subnets, one endpoint subnet per AZ.
- Private DNS enabled; VPC DNS support and hostnames enabled.
- Endpoint SG inbound TCP 443 from approved caller/admin sources, and matching caller egress.
- Routes/NACLs and DNS forwarding for a corporate workstation outside the VPC.
- Explicit endpoint policies allowing the relevant principal, actions, and resources.
- Ownership/cost/teardown responsibility, especially for shared VPCs.[1][23]

The endpoint root takes `data_endpoint_policy_json` and `control_endpoint_policy_json` as required strings. Read policy files into these values through your company module/wrapper. Do not leave the default full-access endpoint policy as an accidental security choice.

A data-plane policy should allow the approved caller's Start/Invoke/Stop/Get/ListSession actions on the exact custom ARN. The control-plane policy should allow the deployer management actions, with Create/List on `*` and supported resource-level actions scoped separately. IAM permissions, endpoint policy and SCPs must all permit the request.[1][25]

### Bootstrap and verification

An isolated infrastructure runner cannot create its first private endpoints through those nonexistent endpoints. Have platform owners bootstrap the approved management path. Provider/module downloads, Python packages, credentials, Terraform state and Bedrock inference each need their own allowed route or mirror. AgentCore PrivateLink does not make the public package registry private.

Read-only discovery:

```bash
aws ec2 describe-vpc-endpoint-services --region us-west-2 \
  --service-names \
  com.amazonaws.us-west-2.bedrock-agentcore \
  com.amazonaws.us-west-2.bedrock-agentcore-control
```

From the actual caller environment, verify that the normal regional AgentCore names resolve to the intended endpoint ENI private IPs, test API reachability, and inspect private flow evidence through the company's network controls. Merely creating an endpoint does not disable the service's public endpoint or enforce private-only use. If enforcement is required, review applicable IAM/SCP network-origin conditions and egress controls with security.[1]

A Bedrock-hosted model additionally needs its separate approved `bedrock-runtime` access path; do not confuse that with the AgentCore endpoint.

## 16. Optional: sandbox access to private resources
Use this only for a real requirement such as a private synthetic database or an internal test API. Change the interpreter inputs:

```hcl
network_mode            = "VPC"
tool_subnet_ids         = ["subnet-REPLACE_ONE", "subnet-REPLACE_TWO"]
tool_security_group_ids = ["sg-REPLACE"]
```

Supply real approved identifiers, then review the replacement plan. Do not use those illustrative strings literally.

AWS currently lists **`usw2-az1`, `usw2-az2`, `usw2-az3`** for tool VPC connectivity. Verify subnet **AZ IDs**, not hard-coded `us-west-2a/b` letters. The reference requires at least two subnets as a POC design choice; the service supports 1-16.[2][20]

```bash
aws ec2 describe-subnets --region us-west-2 \
  --subnet-ids subnet-REPLACE_ONE subnet-REPLACE_TWO \
  --query 'Subnets[].{Id:SubnetId,Vpc:VpcId,AZID:AvailabilityZoneId,FreeIPs:AvailableIpAddressCount}'
```

### Network controls

- Tool SG egress only to the intended private test resource/port.
- Target SG ingress from the tool SG on that port.
- No broad production-network allow rules for a code-execution tool.
- Approved DNS and subnet IP capacity.
- If no internet is allowed, inspect existing default routes/NAT/firewall paths. A VPC attachment alone does not block internet.
- A public subnet does not give the service-managed ENI a public IP. Add NAT only if deliberately approved; it is not required for this POC.[2]

### Schema traps

Current Code Interpreter API uses:

```json
{
  "networkConfiguration": {
    "networkMode": "VPC",
    "vpcConfig": {
      "subnets": ["APPROVED_SUBNET_ID"],
      "securityGroups": ["APPROVED_SECURITY_GROUP_ID"]
    }
  }
}
```

Use `vpcConfig`, not the conflicting `networkModeConfig` shown in some generic VPC examples. Creation belongs to `bedrock-agentcore-control`. Terraform uses `vpc_config`. The shared API's `requireServiceS3Endpoint` setting is Runtime-only and must not be copied into this tool configuration.[20]

ECR/S3 image-layer endpoint instructions in the generic Runtime guide are not evidence that a Code Interpreter-only setup needs an ECR repository. Inventory only the AWS services your actual host/code path invokes.

## 17. Packages, files and persistence
### Package installation

The dependencies installed on your Python host are separate from packages available inside the sandbox. Begin with standard-library computations. Inventory interpreter packages at runtime before relying on pandas or plotting libraries. No-NAT/private mode will not automatically permit PyPI downloads.[2]

For extra packages, use approved preinstalled dependencies or upload vetted compatible wheels through the API/use an approved private artifact path. Check Python/platform compatibility, transitive dependencies, licenses and malware policy. Do not open internet egress simply to make `pip install` work.

### Artifact persistence

Session-local scratch is temporary. Download approved artifacts before stop/expiry or use scoped, approved S3 operations if persistence becomes a requirement. The execution role, bucket policy and any KMS permissions must allow only the intended data path.[4][8]

AWS's session guide also mentions a 30-day session-data retention policy. Do not promise that stopping a session proves immediate deletion of every service-retained record; confirm retention/data-handling requirements with AWS and your company before introducing sensitive data.[4]

### Advanced mounts

Current APIs document S3 Files and EFS mounts for Code Interpreter. These bring VPC, mount targets, IAM and NFS connectivity requirements. The inspected SDK convenience `start` method and Terraform schemas do not expose all current mount options; generic backend path translation also needs care. Treat mounts as a separate follow-up, not a hidden dependency of sandbox execution.[14][45][49]

## 18. Limits and application controls
Published Code Interpreter defaults include **1,000 concurrent sessions**, **1,000 tool configurations**, **2 vCPU / 8 GB memory per session**, **10 GB disk**, **100 MB request/response payload**, **15-minute synchronous requests**, and **8-hour asynchronous commands**. These are service defaults, not a guarantee of account capacity or measured throughput.[5]

Session TTL defaults to 900 seconds and can be configured up to 28,800 seconds. It is absolute. The reference direct test uses 600 seconds; the Deep Agents example uses 1,800 seconds.[7]

For the company POC, use stricter application controls:

- One active task initially; small synthetic files.
- Explicit task/session deadlines and a bounded agent recursion/tool-call budget before unattended use.
- Small model output caps and an approved model.
- No unbounded retry loop or automatic session recreation after expiry.
- Record interpreter ID, session ID, task owner, start/stop result and elapsed time without logging sensitive inputs or credentials.
- Reconcile outstanding sessions after crashes rather than relying only on local in-memory cleanup.

The reference hello examples are intentionally small. Before exposing the agent to users, add your actual request timeout, model-call retry policy, concurrency limiter and authentication boundary. Do not mistake a POC script for a production multi-tenant service.

## 19. Cost controls
Current published table rates for Code Interpreter are **$0.0895 per vCPU-hour** and **$0.00945 per GB-hour**. Billing uses actual CPU and running peak-memory consumption with a one-second minimum, system overhead and a minimum memory charge. Session lifetime includes boot through termination; idle CPU may be free while memory still incurs charges.[6]

Budget with measured consumption, not just your script's execution duration:

```text
Interpreter cost = metered vCPU-hours * CPU rate
                 + metered GB-hours * memory rate

Total POC cost = interpreter + model inference + host
               + optional endpoints/network + storage/telemetry
```

Do not infer a fixed 2-vCPU/8-GB charge from the maximum hardware limits. Do not quote a monthly total without the actual session/resource measurements and your company's prices.

PrivateLink adds per-endpoint per-AZ-hour charges even with no active interpreter session, plus data processing. Check the regional quote before adding several endpoints. NAT, if later approved, adds separate costs. S3, KMS, Secrets Manager, CloudWatch and cross-AZ traffic may also contribute when used.[35]

Set an owner, expiry date, small spend alert and daily review for the POC. Spend alerts are notifications, not a hard execution cap. Explicit session stop, concurrency limits and teardown are the main controls.

## 20. Troubleshooting by layer
### Terraform does not recognize the resource or VPC block

Check the selected provider in `.terraform.lock.hcl` and the initialized provider schema. The reference was validated with AWS 6.68.0. Do not use native block syntax in an AWSCC object attribute or assume an old corporate pin supports the same fields.[13][16]

### Invalid name or invalid VPC parameter

Use `agentcore_poc`, not a hyphenated tool name. Use `vpcConfig` in API payloads and `vpc_config` in native HCL. For VPC mode, verify real subnet/SG IDs, one VPC, supported AZ IDs and available IPs.[18][19][2]

### AccessDenied with an SCP indication

Return to section 3. An explicit deny requires an approved edit to the blocking policy; a missing allow requires permission at every hierarchy level. Do not retry with increasingly broad IAM policies. After an approved SCP change, test the exact failing action again with the same intended identity, then inspect boundary/session/endpoint policies if another denial appears.[50][51][52]

### AccessDenied during provisioning

Check the deployer identity/account/region, SCP and boundary, Create/Get/tag permissions, and PassRole for the exact execution role. VPC first use additionally needs the network service-linked role path. IAM propagation may delay recognition; do not solve it with FullAccess or a wildcard PassRole.[14][25][30]

### AccessDenied starting or invoking a session

Check caller IAM against the **returned custom ARN**, not a built-in ARN pattern. For PrivateLink, check its endpoint policy as well. A successful GetCodeInterpreter under the deployer does not prove the application caller is authorized.[25][1]

### Connection timeout before the API responds

Check workstation/runner proxy and CA trust first. On a private path, verify DNS resolves to the intended ENIs, routing and TCP 443 SG/NACL rules. Do not add NAT reflexively. Verify whether the failure is AgentCore, STS credential refresh or the separate model endpoint.

### SDK works but the agent fails

Inspect the actual tool messages, model tool-calling support and inference permissions. Check the sandbox-package source identity, factory argument names and explicit custom ID. Re-run the direct smoke to separate service behavior from the adapter.

### Command fails but agent reports success

Inspect the raw stream's `isError`, exception events and `structuredContent.exitCode`. Reproduce the known released-adapter fixture. Do not equate a fluent final answer, empty stderr, or HTTP 200 with success.[9][38][44]

### Upload reports success but file is missing

Download and compare the bytes. Prepare nested directories. Check path mapping and sandbox cwd. The released adapter's upload failure reporting is a known caveat.[44][38]

### Session unexpectedly expires or switches interpreter

TTL is absolute. Never reuse a disposed backend. The SDK can implicitly start the default built-in interpreter after local IDs are cleared; create a new explicitly configured session instead.[7][45]

### `pip install` fails inside the sandbox

Check network mode and approved artifact path, not host dependencies. SANDBOX is not general internet mode. Keep the baseline standard-library-only.[3]

### Cleanup or SG/subnet deletion fails

First list/stop sessions and verify the custom interpreter is deleted. In the VPC extension, shared managed ENIs may remain for up to eight hours. Do not forcibly delete AWS-managed ENIs or shared platform networking.[2]

## 21. Teardown: follow the resource owner
1. Download approved results before stopping.
2. Stop all POC sessions, including ones left by a crashed process. Use the exact custom interpreter ID.
3. Read session state back; if cleanup failed, record the IDs and escalate rather than claiming completion.
4. Review and apply a destroy plan in the owning Terraform state.
5. Confirm the custom interpreter is no longer addressable by its ID.
6. Remove only POC-owned policies/artifacts/endpoints. Review retained logs and storage separately.

Useful session-management commands:

```bash
aws bedrock-agentcore list-code-interpreter-sessions \
  --region us-west-2 \
  --code-interpreter-identifier "$AGENTCORE_CODE_INTERPRETER_ID"

aws bedrock-agentcore stop-code-interpreter-session \
  --region us-west-2 \
  --code-interpreter-identifier "$AGENTCORE_CODE_INTERPRETER_ID" \
  --session-id 'REPLACE_WITH_EXACT_SESSION_ID'

aws bedrock-agentcore get-code-interpreter-session \
  --region us-west-2 \
  --code-interpreter-identifier "$AGENTCORE_CODE_INTERPRETER_ID" \
  --session-id 'REPLACE_WITH_EXACT_SESSION_ID'
```

Handle all pages when listing sessions; a first page is not a complete cleanup inventory.

```bash
terraform -chdir=terraform/interpreter plan -destroy -out=destroy.tfplan
terraform -chdir=terraform/interpreter show -no-color destroy.tfplan
terraform -chdir=terraform/interpreter apply destroy.tfplan

aws bedrock-agentcore-control get-code-interpreter \
  --region us-west-2 \
  --code-interpreter-id "$AGENTCORE_CODE_INTERPRETER_ID"
```

The final management lookup should report that the exact resource is not found. Save the ID before destroying outputs. The native provider waits for deletion; its create/delete timeouts default to 30 minutes.[13][14]

If you created dedicated PrivateLink endpoints, destroy them through their own reviewed state only after verifying no other workload uses them. Endpoint billing continues otherwise. Leave shared VPCs, subnets, platform SGs and the shared network service-linked role intact.[2][30][35]

### Manual resource cleanup (if it was never imported)

After stopping and verifying all sessions, the approved deployer can delete the manually created tool:

```bash
aws bedrock-agentcore-control delete-code-interpreter \
  --region us-west-2 \
  --code-interpreter-id "$AGENTCORE_CODE_INTERPRETER_ID"
aws bedrock-agentcore-control get-code-interpreter \
  --region us-west-2 \
  --code-interpreter-id "$AGENTCORE_CODE_INTERPRETER_ID"
```

Deletion may be asynchronous. Read back until the exact ID is not found, or escalate a deletion failure. Do not use Terraform destroy to clean up an unimported manual resource, and do not manually delete a Terraform-owned resource behind its state. After teardown, have policy owners remove dedicated IAM access and expire/restore the approved SCP exception through change control. Do not detach shared organization guardrails yourself.


## 22. POC sign-off checklist
- [ ] Security approved account, region, SANDBOX mode and public/private API route.
- [ ] Applicable SCP allow/deny path reviewed by the organization owner; no guardrails bypassed.
- [ ] Console/CLI creation read back as READY; caller uses the exact custom ARN.
- [ ] If Terraform adoption was chosen, import/plan reviewed with no unintended replacement.
- [ ] Caller policy uses the returned ARN; execution role has no production-data access.
- [ ] Direct smoke passed binary transfer, computation, failure classification and session isolation.
- [ ] Deep Agents emitted a real sandbox tool call and its output was checked.
- [ ] Optional LangChain toolkit demonstrated the same intended custom interpreter.
- [ ] Chosen adapter release/source passed negative exit/timeout/upload tests; known published defects are not waived silently.
- [ ] Synthetic CSV exercise produced a downloaded artifact verified on the host.
- [ ] No prohibited egress, cross-region inference or external telemetry path was introduced.
- [ ] Stop failures/crash cleanup were tested and sessions read back as terminated.
- [ ] Cost owner and expiry are recorded; final resources/storage/endpoints reconciled.

**Recommendation:** keep the first POC at SANDBOX plus API file transfer. Make the decision about private connectivity with security. Add interpreter VPC mode only after proving a private-resource requirement. Treat adapter failure handling as an acceptance criterion before moving to production.

## Appendix A. Reference bundle contents
- `prepare_poc.py`: local JSON generator; no AWS calls or policy attachment.
- `policy-examples/`: illustrative SCP/IAM/request files for review, not applied policies.
- `local_execute.py`: standalone first local-to-AWS script, requiring only boto3.
- `prerequisites_verify.py`: generator, action-catalog, request-schema and local-client tests.
- `terraform/interpreter/main.tf`: account-guarded SANDBOX baseline and conditional VPC mode.
- `terraform/interpreter/tests/offline.tftest.hcl`: four mock-provider tests; Terraform >=1.7.
- `terraform/interpreter/terraform.tfvars.example`: illustrative inputs, not real company identifiers.
- `terraform/endpoints/main.tf`: optional platform-owned data/control PrivateLink endpoints.
- `execution-role-trust.json.example`: trust template for platform review.
- `requirements-candidate.txt`: full dependency snapshot with immutable sandbox source pin.
- `requirements-release.lock`: published-package comparison environment.
- `direct_smoke.py`: explicit opt-in live service tests and cleanup read-back.
- `agentcore_examples.py`: Deep Agents and plain LangChain functions exercised offline.
- `run_agent.py`: explicit opt-in live CLI using the approved Bedrock model.
- `offline_verify.py`: local fake-model/mock-SDK checks; blocks socket connections during tests.
- `verification.txt`: captured local verification output.

All commands in application sections assume the working directory is `reference/`. Markdown/PDF and reference files contain no company credentials or account-specific findings. Replace illustrative identifiers only after company approval.

## Appendix B. Complete Deep Agents and LangChain functions
The following is the actual tested reference module. Calling these functions without mocked transport makes AWS/model calls.

```python
"""AWS examples: importing is safe; calling requires AWS and a tool-capable model."""
from bedrock_agentcore.tools.code_interpreter_client import CodeInterpreter
from langchain_agentcore_codeinterpreter import AgentCoreSandbox
from deepagents import create_deep_agent
from langchain.agents import create_agent
from langchain_aws.tools import create_code_interpreter_toolkit

REGION = "us-west-2"


def run_deep(model, interpreter_id: str, boto3_session=None):
    # interpreter_id must be the pre-provisioned READY custom interpreter ID.
    interpreter = CodeInterpreter(region=REGION, session=boto3_session)
    interpreter.start(identifier=interpreter_id, session_timeout_seconds=1800)
    try:
        backend = AgentCoreSandbox(interpreter=interpreter)
        # Relative paths avoid assuming a service-specific sandbox cwd.
        uploaded = backend.upload_files([("input.txt", b"hello\n")])
        if uploaded[0].error:
            raise RuntimeError(uploaded[0].error)
        # Read-back matters: release 0.0.5 may falsely report an upload success.
        downloaded = backend.download_files(["input.txt"])[0]
        if downloaded.error or downloaded.content != b"hello\n":
            raise RuntimeError("Upload read-back failed")
        agent = create_deep_agent(
            model=model, backend=backend,
            system_prompt="Run cat input.txt with execute and report its output."
        )
        return agent.invoke({"messages": [{"role": "user", "content": "Read input.txt using the shell."}]})
    finally:
        interpreter.stop()


async def run_plain(model, interpreter_id: str, thread_id: str):
    # Native supported LangChain toolkit; no custom tool adapter.
    toolkit, tools = await create_code_interpreter_toolkit(
        region=REGION, code_interpreter_identifier=interpreter_id
    )
    config = {"configurable": {"thread_id": thread_id}}
    try:
        by_name = {tool.name: tool for tool in tools}
        # Creates the session lazily; same config keeps upload and execution together.
        await by_name["upload_file"].ainvoke(
            {"path": "input.txt", "content": "hello\n"}, config=config
        )
        agent = create_agent(model=model, tools=tools,
                             system_prompt="Run cat input.txt with execute_command and report its output.")
        return await agent.ainvoke(
            {"messages": [{"role": "user", "content": "Read input.txt using the shell."}]},
            config=config,
        )
    finally:
        # One toolkit per request here; stops every session it created.
        await toolkit.cleanup()


# Explicit opt-in production invocation only (not run during research):
# import asyncio, os
# from langchain_aws import ChatBedrockConverse
# model = ChatBedrockConverse(model_id=os.environ["BEDROCK_MODEL_ID"], region_name=REGION)
# result = run_deep(model, os.environ["AGENTCORE_CODE_INTERPRETER_ID"])
# result = asyncio.run(run_plain(model, os.environ["AGENTCORE_CODE_INTERPRETER_ID"], "unique-job-id"))
```

## Appendix C. Complete interpreter Terraform root
```hcl
terraform {
  required_version = ">= 1.5.0, < 2.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "= 6.68.0"
    }
  }
}

provider "aws" {
  region              = "us-west-2"
  allowed_account_ids = [var.account_id]
  default_tags {
    tags = {
      Purpose = "agentcore-code-interpreter-poc"
      Owner   = var.owner
    }
  }
}

variable "account_id" {
  type = string
  validation {
    condition     = can(regex("^[0-9]{12}$", var.account_id))
    error_message = "Supply the approved company account ID."
  }
}
variable "owner" { type = string }
variable "execution_role_arn" { type = string }
variable "network_mode" {
  type    = string
  default = "SANDBOX"
  validation {
    condition     = contains(["SANDBOX", "VPC"], var.network_mode)
    error_message = "This POC permits SANDBOX or approved VPC mode; PUBLIC is intentionally excluded."
  }
}
variable "tool_subnet_ids" {
  type    = set(string)
  default = []
}
variable "tool_security_group_ids" {
  type    = set(string)
  default = []
}

resource "aws_bedrockagentcore_code_interpreter" "poc" {
  name               = "agentcore_poc"
  description        = "Deep Agents Code Interpreter POC"
  execution_role_arn = var.execution_role_arn
  network_configuration {
    network_mode = var.network_mode
    dynamic "vpc_config" {
      for_each = var.network_mode == "VPC" ? [1] : []
      content {
        subnets         = var.tool_subnet_ids
        security_groups = var.tool_security_group_ids
      }
    }
  }
  lifecycle {
    precondition {
      condition = var.network_mode != "VPC" || (
        length(var.tool_subnet_ids) >= 2 && length(var.tool_subnet_ids) <= 16 &&
        length(var.tool_security_group_ids) >= 1 && length(var.tool_security_group_ids) <= 16
      )
      error_message = "VPC requires 2-16 approved subnets in distinct supported AZs and 1-16 security groups."
    }
  }
  timeouts {
    create = "30m"
    delete = "30m"
  }
}

output "code_interpreter_id" {
  value = aws_bedrockagentcore_code_interpreter.poc.code_interpreter_id
}
output "code_interpreter_arn" {
  value = aws_bedrockagentcore_code_interpreter.poc.code_interpreter_arn
}
output "caller_policy_json" {
  value = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "bedrock-agentcore:StartCodeInterpreterSession",
        "bedrock-agentcore:InvokeCodeInterpreter",
        "bedrock-agentcore:StopCodeInterpreterSession",
        "bedrock-agentcore:GetCodeInterpreterSession",
        "bedrock-agentcore:ListCodeInterpreterSessions"
      ]
      Resource = aws_bedrockagentcore_code_interpreter.poc.code_interpreter_arn
    }]
  })
}
```

## Appendix D. Architecture and network decision reference
### A. Where the agent application runs

For this POC, run Python on an approved developer workstation or an existing company runner. Deep Agents does not have to run in AgentCore Runtime to use the Code Interpreter sandbox.[36]

The host needs an AWS credential source and permitted HTTPS reachability to AgentCore. The host also needs a separate permitted connection to the selected model provider. Do not place model calls inside the code sandbox merely because it can execute Python.

### B. How the host calls the AWS API

Choose one:

- **Regional HTTPS service endpoint:** simplest baseline, if company policy permits. Calls remain IAM-authenticated. A publicly reachable service endpoint is not anonymous access.
- **PrivateLink:** private API connectivity from a VPC or a privately routed corporate network. Private DNS, routing, endpoint policies, and caller IAM must all work. Code Interpreter supports both data-plane and control-plane endpoints.[1]

PrivateLink does not require the interpreter itself to use VPC network mode. It controls the host-to-service path; tool VPC configuration controls a different path.[1][2]

### C. What network access executed code receives

- **SANDBOX:** managed isolation with limited supported AWS access, including S3 data operations. No attachment to your customer VPC is needed. Do not describe this mode as an air gap or assume public package installation works.[3]
- **PUBLIC:** executed code can reach public internet resources. Excluded from the reference Terraform to avoid accidental enablement.[13]
- **VPC:** executed code can reach resources through approved VPC subnets and security groups. Effective egress depends on routes and controls; VPC mode alone does not prove that internet access is blocked.[2]

### Baseline flow

```text
Approved workstation / existing runner
  Python: Deep Agents + approved model client
       |                       |
       | IAM + HTTPS           | separate approved inference path
       v                       v
AgentCore data-plane API      Approved model
       |
       v
Custom Code Interpreter: SANDBOX
  isolated session -> temporary files + code execution
       |
       +-- artifacts returned through API to host

Terraform / platform identity
       |
       +-- control-plane API -> custom interpreter configuration
```

### When to extend the baseline

- Company forbids public AWS API paths: use **SANDBOX + PrivateLink**.
- Code must query a private database/internal API: use **VPC mode**, with PrivateLink independently selected for the host path.
- Company allows regional HTTPS endpoints and the task only processes uploaded files: keep **SANDBOX**, with no VPC extension.

**Stop and ask security if the first condition is unknown.** A company account does not imply a mandatory VPC, but it also does not imply permission to use public endpoints.

## Sources

[1] https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/vpc-interface-endpoints.html
[2] https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-vpc.html
[3] https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/code-interpreter-resource-management.html
[4] https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/code-interpreter-session-characteristics.html
[5] https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/bedrock-agentcore-limits.html
[6] https://aws.amazon.com/bedrock/agentcore/pricing
[7] https://docs.aws.amazon.com/bedrock-agentcore/latest/APIReference/API_StartCodeInterpreterSession.html
[8] https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/code-interpreter-s3-integration.html
[9] https://docs.aws.amazon.com/bedrock-agentcore/latest/APIReference/API_InvokeCodeInterpreter.html
[13] https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/v6.68.0/website/docs/r/bedrockagentcore_code_interpreter.html.markdown
[14] https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/v6.68.0/internal/service/bedrockagentcore/code_interpreter.go
[15] https://raw.githubusercontent.com/hashicorp/terraform-provider-awscc/v1.105.0/docs/resources/bedrockagentcore_code_interpreter_custom.md
[16] https://raw.githubusercontent.com/hashicorp/terraform-provider-awscc/v1.105.0/internal/aws/bedrockagentcore/code_interpreter_custom_resource_gen.go
[17] https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-bedrockagentcore-codeinterpretercustom.html
[18] https://docs.aws.amazon.com/bedrock-agentcore-control/latest/APIReference/API_CreateCodeInterpreter.html
[19] https://docs.aws.amazon.com/bedrock-agentcore-control/latest/APIReference/API_CodeInterpreterNetworkConfiguration.html
[20] https://docs.aws.amazon.com/bedrock-agentcore-control/latest/APIReference/API_VpcConfig.html
[23] https://docs.aws.amazon.com/vpc/latest/privatelink/create-interface-endpoint.html
[25] https://docs.aws.amazon.com/service-authorization/latest/reference/list_bedrock-agentcore.html
[26] https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/code-interpreter-resource-session-management.html
[27] https://docs.aws.amazon.com/cloudcontrolapi/latest/userguide/security.html
[28] https://docs.aws.amazon.com/cloudcontrolapi/latest/userguide/resource-operations.html
[29] https://docs.aws.amazon.com/cloudcontrolapi/latest/userguide/vpc-interface-endpoints.html
[30] https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/service-linked-roles.html
[35] https://aws.amazon.com/privatelink/pricing
[36] https://docs.langchain.com/oss/python/deepagents/data-analysis
[38] https://files.pythonhosted.org/packages/24/6f/4a5f80869c319eb5a74b98b397a3164879bfa98309fd20804a171ece3501/langchain_agentcore_codeinterpreter-0.0.5-py3-none-any.whl
[39] https://pypi.org/pypi/bedrock-agentcore/json
[40] https://pypi.org/pypi/deepagents/json
[41] https://pypi.org/pypi/langchain/json
[42] https://pypi.org/pypi/langchain-aws/json
[44] https://raw.githubusercontent.com/langchain-ai/langchain-aws/a0e80b9febaf21cf1cead8f0dc16b3ffd8633976/libs/agentcore-codeinterpreter/langchain_agentcore_codeinterpreter/sandbox.py
[45] https://raw.githubusercontent.com/aws/bedrock-agentcore-sdk-python/45260c882cb6adab7b24446fffb38009f92fae2c/src/bedrock_agentcore/tools/code_interpreter_client.py
[47] https://raw.githubusercontent.com/langchain-ai/langchain-aws/a0e80b9febaf21cf1cead8f0dc16b3ffd8633976/libs/aws/langchain_aws/tools/code_interpreter_toolkit.py
[49] https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/code-interpreter-filesystem-configurations.html
[50] https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html
[51] https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps_evaluation.html
[52] https://docs.aws.amazon.com/IAM/latest/UserGuide/troubleshoot_access-denied.html
[53] https://docs.aws.amazon.com/cli/latest/reference/organizations/list-policies-for-target.html
[54] https://docs.aws.amazon.com/cli/latest/reference/bedrock-agentcore-control/create-code-interpreter.html
[55] https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/code-interpreter-create.html
[56] https://servicereference.us-east-1.amazonaws.com/v1/bedrock-agentcore/bedrock-agentcore.json
[57] https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html
[58] https://docs.aws.amazon.com/cli/latest/reference/organizations/list-parents.html
[59] https://docs.aws.amazon.com/cli/latest/reference/iam/put-role-policy.html
