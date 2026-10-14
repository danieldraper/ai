# Review coverage

Use during architecture mapping and the assessment. Account for each applicable category in the coverage ledger; combine overlapping checks when they share a path.

## Identity, access, and exposure

- Authentication and API authentication: login, recovery, verification, MFA, credential changes, bypass paths, and identity confusion.
- Authorization, IDOR/broken object-level authorization, horizontal/vertical privilege escalation, tenant/account isolation, and administrative access.
- Sessions, cookies, token lifecycle, revocation, fixation, replay, brute-force protections, rate limits, and enumeration.
- Sensitive-data exposure in responses, exports, downloads, files, caches, error messages, logs, and cross-user or cross-tenant cache keys.
- Mass assignment and manipulation of ownership, role, account, status, permission, or financial fields.

## Inputs and execution boundaries

- SQL and other injection, dynamic queries, command/shell execution, template execution, and unsafe deserialization.
- Cross-site scripting across HTML, JavaScript, attributes, URLs, and stored/rendered content; CSRF on relevant state-changing paths.
- SSRF, open redirects, URL parsing/normalization discrepancies, callbacks, and other user-controlled destinations.
- Path traversal, arbitrary file access, unsafe uploads, content-type handling, download authorization, and file processing.
- Attacker-controlled expensive operations, unbounded queries/fan-out, decompression or parser costs, and resource exhaustion. Use bounded proofs rather than disruptive tests.

## Business logic and financial integrity

Look beyond conventional vulnerability labels. Model valid transitions and test how a caller can violate them:

- Skip approvals or workflow states; edit completed/finalized records; act on archived, deleted, suspended, or inaccessible objects.
- Manipulate ownership, account IDs, status, amounts, settlement state, or other protected fields directly.
- Repeat or reorder requests, race concurrent actions, bypass quotas/restrictions, or abuse bulk imports/exports.
- Trigger duplicate or missed processing, expose identifiers, or exploit differences between UI and API workflows.

Where money or financial records exist, assess idempotency key scope and persistence, transaction boundaries, locks/atomic updates, duplicate processing, balance changes, settlement calculations, refunds/reversals, reconciliation, precision/rounding, currency handling, and attacker-controlled amounts. Correctness and integrity are security properties. Check that webhook replay protection and application idempotency work together.

## Deferred work and integrations

- Webhook signatures: exact signed payload, normalization, key selection, comparison, timestamp/replay handling, and failure behavior.
- Jobs: actor/tenant context, permissions at enqueue and execution, ownership changes, arbitrary class/method invocation, retries, duplicate processing, and unsafe serialized arguments.
- Audit logs: missing or bypassable recording, actor attribution, tampering, sensitive contents, and failures that silently lose important events.
- External calls and callbacks: destination restrictions, credentials, trust boundaries, and sensitive-data leakage.
- Race conditions that undermine authorization, limits, one-time tokens, or financial state.

## Secrets, cryptography, and configuration

Search current code, fixtures/examples, configuration, and available local history for API keys, passwords, private keys, signing/webhook secrets, database/cloud/AWS credentials, bearer tokens, and development credentials potentially valid in production. Redact before displaying evidence. Record apparent exposure separately from unverified current validity.

Assess token generation, cryptographic choices, key handling, comparison, expiration, and purpose/audience binding. Inspect filtering and logging of passwords, tokens, financial information, and personal data.

Inspect applicable manifests and lockfiles, Dockerfiles/Compose, deployment and Kamal definitions, nginx/Caddy/proxy configuration, CI/CD workflows, environment configuration, initializers, credentials references, and database configuration. Assess security headers, CSP, CORS, cookies, host controls, TLS assumptions, trusted proxies/IPs, and production defaults. Do not assume a setting is effective without tracing how deployment applies it.

Treat dependency/framework issues as candidates until the version and advisory conditions are verified. A scanner result is a lead, not a substitute for applicability analysis.

## Attack chains and controls

Look for established combinations such as object access plus ownership reassignment, SSRF plus reachable privileged metadata, or webhook replay plus duplicate financial processing. Document prerequisites and incremental impact, without double-counting component findings.

Record well-supported positive controls: tenant scoping, authorization, cryptographic and webhook verification, secure session configuration, parameter filtering, idempotency, and audit logging. Name the paths inspected and limits of each conclusion.
