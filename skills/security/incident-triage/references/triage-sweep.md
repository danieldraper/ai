# Triage sweep

Work through the areas that the available sources can answer. Compare the window against a baseline period of normal activity, defined up front: the same length and the same days of the week, with its bounds recorded in `INCIDENT.md`, so "unusual" means something. Record each check run, including checks that found nothing, in the Sweep coverage table so coverage is visible.

Each anomaly becomes a lead with an evidence reference and its open benign explanations. Common benign explanations are listed per area.

## Log completeness (before any negative finding)

- Volume over the window at a granularity that would show a gap: hourly for a window of days, daily for a window of months. Align buckets to UTC midnight (`WITH TIMEZONE 'UTC'` or equivalent); a series anchored to query time shifts every date label.
- Counts reconciled across layers for the same host and period: edge, load balancer, web server, application. Explain every difference (health checks excluded, static assets served at the edge, an error page logged twice) or record it as a gap.
- Dropped-data and ingest-limit events on the platform, and the platform's own audit log for logging or retention changes in the window.
- The logging configuration for excluded routes, sampling, and log level, read from the code or config rather than assumed.
- A positive control for every absence query: the same predicate returning a known event before it is trusted to return nothing.
- Retention read from the platform, or marked `inferred` with the method.

## Authentication

- Failed login spikes, overall and per account, IP, and application.
- Success shortly after a run of failures for the same account (guessing or stuffing that worked).
- One IP or user agent attempting many accounts; one account seen from many IPs.
- Accounts authenticating from an IP, network, user agent, or client application not seen in the baseline.
- Password resets, email changes, MFA enrolment or removal, and new signups on existing identities.
- Token and refresh-token use continuing after containment actions or after the account owner logged out.
- Authentication through an unexpected application, connection, or grant type.

Benign: password managers and SSO retries, mobile networks changing IPs, VPNs, new devices, load tests.

## Authorization and privileged actions

- Administrative actions, role or permission changes, and new API keys or clients.
- Identity provider and cloud configuration changes: callbacks, connections, rules or actions, IAM policies, security groups, WAF rules.
- Access denied (403) responses followed by success on the same resource.
- Requests for resource IDs belonging to other accounts or tenants, especially sequential IDs.

Benign: scheduled maintenance, deploy automation, support staff acting on tickets.

## Routes and requests

- Routes requested in the window that never appear in the baseline, including routes that should not exist or should be internal.
- The first request ever seen for an affected route.
- Error spikes (4xx and 5xx) by route and source, which often mark probing.
- Known scanner and exploit patterns in paths and parameters: traversal, injection, template, and deserialization payloads.
- Unusual methods, oversized requests, and unusual content types.

Benign: new releases, crawlers, uptime monitors, security scanners run internally.

## Data access and exfiltration

- Large or unusually many successful responses per account, IP, or route.
- Exports, downloads, reports, and bulk or paginated listing endpoints walked end to end.
- Egress volume changes in metrics, if raw logs are missing.

Benign: month-end reporting, integrations, backfills.

## Timing and shape

- Activity outside normal hours for an account or integration.
- Highly regular intervals suggesting automation.
- Bursts that start or stop near deploys, configuration changes, or containment actions.

## Logging integrity

- Gaps where records should exist, and drops in volume.
- Logging, alerting, or retention configuration changes during the window, including alert conditions edited hours before detection.
- Deleted or truncated files, and clock jumps between related sources.
- Edge or firewall changes that stop blocked traffic reaching origin logs; an attacker "going quiet" may be a visibility change.

A gap during suspicious activity is a lead in its own right.

## Query traps that produce false negatives

- Equality on a multi-hop forwarded header (`X-Forwarded-For = '1.2.3.4'`) never matches a three-hop value. Extract the first hop once, the same way, for every pivot.
- A facet or row query whose result count equals its `LIMIT` is truncated. `latest(field)` shows one value per group, not all of them.
- `uniqueCount`-style cardinality is approximate above about a thousand values.
- `SINCE x UNTIL y` is half-open; say which end is inclusive when a bound lands on an edge.
- A data-lake query whose partition filter matches nothing returns zero rows and scans zero bytes.
- A response-size or timing heuristic for success or failure is an inference until calibrated against a known case, and stays labelled `inferred`.
