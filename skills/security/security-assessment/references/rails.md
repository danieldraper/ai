# Rails security review

Read for Rails applications. These are investigation targets, not automatic findings. Establish attacker control, framework behavior at the pinned version, and the effective execution path.

## Controllers, routes, and authorization

- Inventory routes, unintended exposed actions, API endpoints, Turbo/Stimulus actions, and controller authorization coverage.
- Trace `before_action` inheritance, ordering, skips, and conditional checks. Check view-only authorization and actions with side effects before denial.
- Inspect global lookups such as `Model.find(params[:id])` against the actual ownership checks and intended account scope. A global lookup alone does not prove a bypass.
- Check nested resources, bulk actions, exports, downloads, and per-record authorization. Test parent/descendant and unrelated-account behavior against the documented model.
- Inspect strong parameters, `permit!`, nested attributes, mass assignment, and protected owner/account/role/status fields. Model validations are not a substitute for authorization.

## Queries, dispatch, and rendering

- Trace user input into `where`, `order`, `select`, `joins`, raw SQL fragments, and other dynamic query construction; distinguish bound parameters from interpolation.
- Trace `constantize`, `safe_constantize`, `send`, `public_send`, reflection, and class/method selection. A safe-looking method name does not establish an allowlist.
- Inspect `html_safe`, `raw`, HTML/JavaScript interpolation, templates, and rendering contexts for escaping failures.
- Inspect YAML loading, Marshal, serialization/deserialization, ERB/template evaluation, and object construction.
- Inspect `system`, backticks, Open3, process execution, shell interpolation, and argument handling.

## Files, URLs, and tokens

- Review ActiveStorage upload, preview, processing, serving, and attachment authorization, including direct file routes.
- Trace signed IDs and GlobalID usage for purpose, expiration, object authorization, and unintended capability reuse. A valid signature does not automatically authorize every use of the referenced object.
- Inspect `redirect_to`, return URLs, URL parsing, external HTTP requests, callback destinations, and attacker-controlled hosts/paths.
- Review webhook signature validation and timing-safe token comparisons, including handling of invalid lengths and malformed input.

## Sessions and deployment configuration

- Inspect encrypted/signed cookies, session settings, CSRF enforcement and exceptions, CORS, CSP, host authorization, trusted proxies/IP handling, and TLS assumptions.
- Inspect environment-specific overrides and effective production settings, not only defaults.
- Review `Rails.application.credentials`, environment-variable use, secrets handling, and parameter/log filtering. Avoid displaying decrypted credentials or raw secrets.

## Persistence and deferred behavior

- Trace security-relevant callbacks and whether alternate write paths bypass them.
- Review job arguments, serialized objects, arbitrary class/method names, tenant context, retries, and deferred authorization/ownership policy.
- Inspect transaction boundaries, locking, database constraints, idempotency, and concurrent behavior for sensitive state transitions.
- For remediations, describe focused RSpec or Minitest regression cases matching the existing suite. Include an allowed actor and the relevant denied or cross-tenant case; test persisted side effects as well as response status.
