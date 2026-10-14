---
name: security-assessment
description: Perform a comprehensive application security source review and vulnerability assessment, prioritizing exploitable authorization, tenant isolation, sensitive-data, and business-logic failures. Use when asked for a security assessment, penetration-test-style code review, or repository vulnerability review. Produces an evidence-based report; does not change application code unless requested.
---

# Security assessment

Act as a senior application security engineer. Find realistic production vulnerabilities and dangerous design or configuration choices. This is a security assessment, not a style review or a dependency-only scan.

## Scope and model choice

Identify the requested repository, branch/revision, relevant working changes, and any specified testing environment. By default assess the entire repository, including application code, configuration, jobs, integrations, and deployment definitions. Honor an explicitly narrower scope. Do not change application code unless instructed; proposed fixes and regression tests belong in the report.

At the start, check model/tool availability exposed by the current host, if available. Suggest a security-focused model or approved cyber workflow when it would help, including a Daybreak-enabled option when available. Daybreak is an access program with tiers, not a universal model ID. Do not assume that access includes a particular cyber-specialized model or that a skill can switch the current model. Use the actual available option names and respect the user's selection. If availability cannot be established, make the recommendation conditional once and continue with the current model. Do not install tools, change account settings, send source to another provider, or start another model run merely to satisfy this preference.

For current OpenAI access details, consult the [official Daybreak overview](https://help.openai.com/en/articles/20001258-openai-daybreak-trusted-access-for-cyber-overview). Avoid embedding model IDs that will become stale. Specialist models remain subject to the same evidence requirements; model agreement does not prove a vulnerability.

Source review does not require live exploitation. Keep demonstrations scoped to this application and local/test verification. Use existing authorization for runtime checks; do not infer permission to attack third-party services, mutate production, deliver real messages, move real money, extract customer data, or run disruptive load tests. When validation would cross that boundary, provide a controlled test proposal and continue the source review. Stop a runtime probe if it reaches an unexpected live service or causes unintended effects.

## Map the system and maintain coverage

First inspect repository instructions, architecture documentation, routes and entry points, relevant tests, and security configuration. Identify:

- Authentication, sessions, API identities, authorization engines, and the tenant/account hierarchy.
- Public and administrative interfaces, APIs/GraphQL, webhooks, uploads, exports/downloads, and high-privilege operations.
- Background jobs, callbacks, caches, external HTTP integrations, sensitive-data stores, and payment/financial functionality.
- Deployment boundaries, proxies, secrets handling, and dependencies/framework versions.

Read [review coverage](references/review-coverage.md) and assess each applicable area. For Rails, also read [Rails review](references/rails.md). Use these as coverage prompts, not as evidence that an issue exists.

Maintain a compact coverage ledger: area or entry-point group, relevant files, reviewed paths/controls, remaining questions, and status (`reviewed`, `partial`, `blocked`, or `not applicable`). Inventory the whole repository before prioritizing deep traces. Mark exclusions such as generated/vendor code and explain how relevant dependency behavior was assessed. Searching for risky function names alone does not constitute reviewing an area.

Prioritize authorization, tenant isolation, sensitive data, and business logic, but continue through every applicable major area. Do not stop after the first few findings. For a large assessment, preserve a checkpoint of coverage, findings, and next paths so work can resume without losing gaps. If a constraint prevents completion, deliver a clearly partial report rather than claiming the repository is secure.

## Threat model and tracing

Consider unauthenticated users, ordinary authenticated users, compromised accounts, malicious API clients, and users seeking horizontal or vertical privilege escalation. Treat IDs, UUIDs, query/body parameters, headers, cookies, uploads, URLs, and webhook payloads as potentially attacker-controlled. UI restrictions are not authorization; evaluate direct endpoint calls. Tenant isolation is a critical boundary where applicable.

Trace important flows explicitly:

`source → validation/normalization → authorization → business logic → database/filesystem/network/shell/HTML/external API sink`

Establish attacker control, reachability, prerequisites, intervening controls, and observable impact on the exact execution path. A dangerous function is not a finding by itself. Neither nearby sanitization nor the presence of an authorization helper establishes safety. Account for framework behavior, middleware, database constraints, and trusted upstream checks before reaching a verdict.

For each serious finding, inspect callers, related endpoints, similar implementations, and tests. Search repository-wide for the same root cause. Group related occurrences while retaining their locations and meaningful differences. Investigate plausible chains separately and identify which links are established versus assumed.

## Authorization assessment

For every meaningful action, API/GraphQL operation, job-triggering endpoint, administrative operation, and sensitive service path, establish:

1. The permitted actors, authentication requirement, and actual authorization enforcement point.
2. Resource scoping to the current user/account/tenant, including replaced IDs and nested IDs from different tenants.
3. Whether submitted fields can change ownership, account, roles, permissions, status, balances, or other protected state.
4. Whether checks precede observable reads, writes, enqueues, notifications, and other side effects.
5. Per-record authorization for bulk operations and correct scoping for exports/downloads.

Inspect custom permission engines and all significant call sites. Check missing/misspelled permissions, wildcards, deny/allow precedence, attacker-controlled context, default-allow behavior, and UI/backend discrepancies. For hierarchies, distinguish ownership, inheritance, delegated creation, viewing, and editing; do not assume parents may perform every action on descendants. Trace revoked or changed permissions through deferred execution according to the application's intended policy.

## Evidence and validation

Use targeted tests or bounded local reproductions where permitted. Keep read-only assessment distinct from application repair. Any temporary verification harness or fixture must be isolated, have a cleanup plan, and preserve the user's existing work. Do not weaken safeguards to make a test pass.

Classify confidence separately from severity:

- **Confirmed:** reproduced in an authorized environment, or established by a complete source-level proof with all material prerequisites verified. State which form of proof exists; never imply runtime testing occurred when it did not.
- **High confidence:** a clear reachable path with strong evidence and explicitly stated remaining assumptions.
- **Medium confidence:** a plausible path with material missing context.
- **Requires verification:** a specific unresolved question, environment dependency, or unverified advisory match.

Put confirmed and strongly evidenced actionable vulnerabilities in Findings. Put materially uncertain candidates in Security Concerns Requiring Verification; hardening without a demonstrated vulnerable path belongs in Hardening Recommendations. Record controls that defeat suspected attacks as positive evidence. Avoid severity inflation and duplicate counting across shared root causes or attack chains.

Redact secrets in all output, including tool output and snippets. Prefer scanners with redacted output; if reading likely secret-bearing files, extract names/locations or masked values rather than dumping contents. Distinguish examples from apparently operational credentials. Inspect available local history for credential exposure without printing values; disclose shallow or unavailable history. Never test suspected credentials against a live provider merely to establish validity.

Verify dependency claims against the pinned version and current authoritative advisories or vendor notices when accessible. Consider affected configuration and reachability. Cite the advisory and state applicability; age alone is not evidence. If verification is unavailable, label the candidate accordingly. Spend most effort on application behavior rather than version enumeration.

## Deliver the assessment

Use [the report format](references/report-format.md). Include concrete locations, minimal code evidence, realistic abuse scenarios, specific remediation, and regression tests consistent with the project's framework. Keep examples scoped to authorized local/test use. Preserve findings even when runtime validation is blocked, while clearly qualifying their confidence.

Keep reports and evidence local unless another destination is explicitly requested. If a report file is requested without a format, follow repository conventions; do not publish it or commit artifacts automatically. Never include full secrets or unnecessary personal data.

Finish with reviewed areas, gaps, additional runtime/infrastructure information needed, and an honest statement of completeness. No findings means no vulnerabilities identified within the assessed scope and limitations, not proof of security.
