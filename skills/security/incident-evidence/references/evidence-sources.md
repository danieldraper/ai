# Evidence sources

Use these as prompts for where to look and what can go wrong. They are not evidence that a source exists, is enabled, or retains data in a given environment. Verify retention, sampling, and event coverage for the actual account, plan, and configuration; vendor defaults change.

## Identity provider (for example Auth0, Okta, Entra ID)

- **Answers:** authentication successes and failures, token exchanges, MFA events, password resets, account changes, and administrative configuration changes, usually with IP, user agent, client/application, and connection.
- **Look for:** first and last events for the affected application or connection; token and refresh-token exchanges after containment; administrative or Management API changes to applications, connections, rules/actions, and allowed callbacks; signups or password resets on affected accounts.
- **Traps:** dashboard retention depends on plan and is often short; a log stream to a SIEM or bucket may hold more. Event type codes and their meanings are vendor-specific; check them against current vendor documentation rather than memory. Silent authentication and refresh-token use can show continued access without any interactive login. Tenant settings change history may be only partially covered by logs.

## Observability platforms (for example New Relic, Datadog, Splunk)

- **Answers:** application and access logs, APM transactions and errors, alert history and the platform's own audit log, often across many services in one query language.
- **Look for:** `[AUDIT]`-style structured lines that carry the authenticated user and client IP; the platform audit log for alert-condition changes during the window; alert incidents that fired before anyone noticed.
- **Traps:** retention differs per data type (logs, transactions, spans, alert events) and APM data is usually sampled, so a trace ID present in logs may be absent from transactions. Facet queries return a default of 100 groups and cap at a few thousand; a result count equal to the `LIMIT` is truncated, not complete. "Query too big" errors must be chunked by time, with each chunk logged. Day buckets in time series and `FACET ... BY day` are labelled in the account's timezone unless you add `WITH TIMEZONE 'UTC'`, so dates can be off by one against raw timestamps. Field discovery with `SELECT *` dumps unrelated users' personal data into the transcript; use `keyset()` or the schema tool instead.

## Application logs

- **Answers:** requests to specific routes with status, authenticated user, session or request ID, and response size.
- **Look for:** the first request ever served by the affected route; requests from IPs or sessions seen in identity-provider logs; responses whose size suggests data returned.
- **Traps:** log level and sampling; routes or health checks excluded from logging; timestamps at request start versus completion; client IP taken from an untrusted `X-Forwarded-For`; logs rotated on hosts that no longer exist.

## WAF, CDN, and load balancer logs

- **Answers:** raw inbound requests, including unauthenticated ones that never reached the application, with the true client IP rather than a forwarded header.
- **Look for:** reconnaissance before the first successful access; paths, user agents, and TLS fingerprints (JA3/JA4) shared across IPs; request volume to the affected route over time; the same actor's requests to hosts the application logs do not cover.
- **Traps:** sampled logging; logs enabled only on some distributions or listeners; edge-cached responses that never reached the origin; a CDN distribution added part-way through retention, so the edge log starts later than the origin log for some hostnames. Blocked requests disappear from origin logs once the edge is locked down, which can look like an attacker stopping.

## Data lake queries (for example Athena over S3 logs)

- **Answers:** the longest-retained raw copy of edge, load balancer, WAF and control-plane logs, often a year.
- **Look for:** actor IPs and techniques before the observability platform's retention begins; the true client IP for events already seen elsewhere.
- **Traps:** tables are partitioned by day or hour, and a query whose partition filter matches nothing returns zero rows with zero bytes scanned. That is a query failure, not a negative finding: check `bytes_scanned` and run a known-positive control (an event you have already seen in another source) before citing any absence. Partition projection ranges and table definitions may not cover every log prefix; creating a table is a change to a production account and needs the user's explicit go-ahead even when the data is read-only. Result pages are capped, so `LIMIT` and pagination both matter. Retention is rolling, so the oldest month is expiring while you work.

## Product analytics (for example PostHog, Amplitude, Segment)

- **Answers:** a per-browser device identifier and the identities that signed in from it, with IP and user agent, often retained longer than server logs.
- **Look for:** one device identifier used across unrelated accounts (stronger than a shared IP, which carrier-grade NAT or a VPN explains); page views of credential, user, MFA and payout screens per device.
- **Traps:** the client can block analytics, so absence of events for an actor proves nothing; IP anonymisation may be enabled for some periods; device identifiers are cookies and reset when the actor clears a profile; identity merging can attach an actor's device to a victim's person record. Project metadata calls can return the project API token; do not echo it.

## Chat, ticket and wiki records (for example Slack, Jira, Confluence)

- **Answers:** who did what during the response, when it was noticed, and what people believed at the time.
- **Look for:** containment actions with times, the first message raising the alarm, decisions and their rationale, earlier incidents involving the same accounts.
- **Traps:** these are statements, not system records: mark them `reported` until a log shows the effect. The reading tool may display times in a local offset (one Slack integration showed UTC+10 during AEDT); convert from the raw message `ts` and record the tool's display timezone against the source. Save the thread text into the ledger with `evidence.py note`; a channel read that lives only in the conversation cannot be cited later.

## Metrics and billing

- **Answers:** aggregate request counts, error rates, and egress over time, often retained much longer than raw logs.
- **Look for:** when traffic to a route or service first appeared or changed shape, to bound activity after raw logs have expired.
- **Traps:** aggregation hides individual requests and actors; metrics only bound volume, not identity.

## Cloud control-plane audit (for example CloudTrail, GCP Audit Logs, Azure Activity Log)

- **Answers:** infrastructure and IAM actions, secret access, key usage, and configuration changes.
- **Look for:** use of credentials tied to the affected system; secret reads; changes to security groups, WAF rules, or IAM around the window.
- **Traps:** data-plane events, such as object reads, are often not enabled by default; regional trails; event time versus delivery delay.

## Database audit and change history

- **Answers:** writes and sometimes reads to sensitive tables.
- **Look for:** audit or version tables (for example `paper_trail` versions), `updated_at` changes on affected records, query logs if enabled.
- **Traps:** reads are rarely logged, so "no evidence of data access" is often unprovable from the database alone; `updated_at` only shows the latest change; restored backups can rewrite timestamps.

## Deploy, release, and source history

- **Answers:** when vulnerable code or configuration was live.
- **Look for:** the deploy that first served the affected route or configuration and the deploy that removed it; feature flag change history; infrastructure-as-code applies.
- **Traps:** commit, merge, and deploy times differ, and rollbacks can re-expose code; a flag can expose a route independently of a deploy; rebased or squashed history can move commit dates.

## Secrets and credential management

- **Answers:** when a credential was created, read, rotated, or revoked.
- **Look for:** secret access logs for the affected credential; rotation records; outstanding sessions and tokens issued before rotation; for static credentials (API tokens, shared secrets), the last successful authenticated request from each client and the first 401 after rotation.
- **Traps:** rotation does not revoke sessions or tokens already issued; old versions may remain valid until explicitly disabled. A static credential has no lifetime: it is valid until the last 200 and rotated at the first 401 on a known-good client. A "rotated" message with no 401 transition in the logs means the rotation is unverified. Session stores with sliding expiry keep a session alive indefinitely while it is in use, and a password reset email does not end it.

## Messaging providers (email, SMS, push)

- **Answers:** password reset, verification, and MFA messages sent, with recipient and time.
- **Look for:** messages to affected accounts around suspicious authentication events; bounces or changed recipient addresses.
- **Traps:** provider retention is often short; message content may not be retained.

## Endpoint and corporate systems

- **Answers:** whether an employee device or account was the access path.
- **Look for:** EDR alerts, SSO logs for staff accounts, password manager or VPN logs where an insider or compromised staff credential is plausible.

## External reports

- **Answers:** effects visible outside the system.
- **Look for:** customer support tickets, fraud reports, chargebacks, researcher or bug bounty reports, and third-party breach notifications that mention the affected system or accounts.
- **Traps:** reports give the time someone noticed, not the time something happened; treat them as `reported` until corroborated.

## Backups and snapshots

- **Answers:** system or data state at points in time.
- **Look for:** configuration or records before and after the suspected window, to establish what changed.
- **Traps:** snapshots show state, not who changed it or when within the interval.
