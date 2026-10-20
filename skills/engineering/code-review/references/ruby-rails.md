# Ruby and Rails review

Read the section for your lens. These are investigation targets, not automatic findings: confirm the behaviour at the pinned Rails and gem versions and on the actual execution path before reporting. Where the repository documents a convention that differs from this file, the repository wins.

Contents: [Correctness](#correctness) · [Security](#security) · [Performance](#performance) · [Idioms and patterns](#idioms-and-patterns) · [Architecture](#architecture)

## Correctness

**Nil, truthiness, and keys**

- `&.` chains that turn a programming error into a silent nil; `dig` and `[]` where `fetch` would name the missing key. Ask what the caller does with the nil.
- `||=` and `||` defaults that misfire on `false`; `blank?`/`present?` on booleans and on `0`.
- String versus symbol keys across `params`, JSON, job arguments, and cache payloads; `HashWithIndifferentAccess` leaking or being assumed.
- Mutable constants and default arguments; missing `# frozen_string_literal: true` where the repo uses it.

**ActiveRecord semantics**

- Ignored return values of `save`, `update`, `destroy`; `save!` versus `save` chosen deliberately, and the caller handling the raise or the false.
- `update_column`, `update_columns`, `update_all`, `delete`, `delete_all`, `insert_all`, `upsert_all`: they skip validations and callbacks. Is that intended, and does anything rely on the skipped callbacks?
- `find` raises, `find_by` returns nil; `first` without `order` depends on the database.
- `transaction` blocks: `return`/`break`/`throw` inside them, rescued exceptions that prevent rollback, nested transactions without `requires_new: true`, and work that must not be rolled back (emails, HTTP calls, job enqueues) happening inside. Side effects belong in `after_commit`, and `perform_later` inside a transaction enqueues before the row is visible unless the adapter defers it.
- Callback ordering and conditional callbacks; `dependent:` on new associations; `default_scope` interactions; `inverse_of` for new `has_many`/`belongs_to` pairs.
- Enum and state changes: transitions that skip validation, `enum` value collisions, state machines updated without the guard.
- Uniqueness validations without a unique index are races, not guarantees.

**Time and money**

- `Time.now`/`Date.today` versus `Time.current`/`Date.current`; comparisons across time zones; DST around day boundaries; comparing times with `==` after a database round-trip (microsecond truncation).
- Floats for money or rates; `BigDecimal` or integer minor units; rounding mode made explicit; currency carried alongside amounts.

**Errors and control flow**

- `rescue Exception` or bare `rescue` swallowing `SignalException`/`NoMemoryError`; `rescue => e` that logs and continues where the caller expects a result; `retry` without a bound; `ensure` with an explicit `return`.
- Trailblazer or other operation/service objects: every step's failure path leads to a result the caller handles; `ctx` keys set on one track and read on the other; subprocess failures routed to the right terminus. Use the `railway-diagram` skill to map branching when it is not obvious.

**Concurrency and jobs**

- Class-level mutable state and memoisation (`@x ||=`) under Puma threads; `Thread.current` leaking between requests.
- Sidekiq/ActiveJob: jobs idempotent under retry, arguments serialisable (pass ids, not records, unless GlobalID is intended), `retry` and `dead` settings, the record possibly deleted or changed by the time the job runs, `perform_later` from inside callbacks firing more than once.

**Migrations**

- Irreversible `change` methods; schema and data changes in the same migration; backfills that lock a large table.
- New columns without `null: false`/default where the model requires them; new `where`/`order` columns without an index; foreign keys without constraints where the schema otherwise uses them.
- PostgreSQL: adding indexes without `algorithm: :concurrently` and `disable_ddl_transaction!`; renaming or removing columns still read by the running release; `strong_migrations` warnings if the gem is present.

**Tests**

- The new behaviour has a test that would fail without the change; the test asserts persisted state and side effects, not only the response status.
- `let!` versus `let` ordering, `travel_to` for time, no `sleep`, no order dependence, factories not creating unneeded associations, stubs at the boundary rather than on the object under test.

## Security

For a whole-system audit use the `security-assessment` skill. Here, trace each new or altered entry point: `source → validation → authorization → business logic → sink`.

- **Authorization and scoping**: new or changed actions covered by `before_action` or the policy layer (Pundit, CanCanCan, custom); `skip_before_action` additions; global lookups (`Model.find(params[:id])`) where the repository otherwise scopes through `current_user`/`current_account`; nested resources and bulk operations checked per record; exports and downloads.
- **Mass assignment**: `permit!`, broad `permit` lists, nested attributes, and whether owner, account, role, status, or amount fields are reachable through params.
- **Injection**: string interpolation into `where`, `order`, `select`, `joins`, `pluck`, `group`, `having`, and `Arel.sql`; `sanitize_sql` used correctly; `send`/`public_send`/`constantize`/`method` with user-influenced names; `eval`, `instance_eval`; `system`, backticks, `Open3`, `Kernel#open` with user input; `YAML.load`, `Marshal.load`, `JSON.parse(create_additions: true)` on untrusted data.
- **Output**: `html_safe`, `raw`, `<%== %>`, `render inline`, `content_tag` with user HTML, `link_to` with user-supplied URLs (`javascript:`), JSON embedded in script tags.
- **Redirects and outbound requests**: `redirect_to params[...]` without `allow_other_host: false` or an allowlist; user-controlled URLs reaching `Net::HTTP`, Faraday, or webhook delivery (SSRF, internal metadata endpoints).
- **Secrets and sensitive data**: credentials in code or fixtures; `filter_parameters` covering new sensitive fields; card numbers, tokens, or personal data in logs, exception messages, error trackers, job arguments, or `inspect` output. For payments code, the PCI boundary: does the change move PAN, CVV, or track data somewhere it was not before?
- **Crypto and comparison**: `SecureRandom` not `rand`; `ActiveSupport::SecurityUtils.secure_compare` for tokens and signatures; `MessageVerifier`/`MessageEncryptor` with purpose and expiry; signed and global ids checked for purpose before use.
- **Sessions, CSRF, CORS**: `protect_from_forgery` exceptions, `skip_forgery_protection`, cookie flags, CORS origins widened, host authorization changes.
- **Webhooks and replay**: signature verification on the exact raw payload, timestamp tolerance, idempotency keys scoped correctly, duplicate processing of financial events.
- **Rate limiting and enumeration** on new authentication-adjacent endpoints; error messages that reveal existence.
- **Dependencies**: new gems checked for maintenance and advisories (`bundle audit` if present); pinned versions; native extensions.

## Performance

- **Queries in loops**: new association access inside `each`, `map`, partials, serializers, or presenters without `includes`/`preload`/`eager_load`; `includes` that should be `preload` to avoid a giant join, or `joins` where only filtering is needed.
- **Counting and existence**: `count` on a loaded relation (`size` or `length`), `.any?`/`.present?`/`.empty?` loading records where `exists?` would not; `pluck` versus `map`; `select` only needed columns on wide tables.
- **Unbounded sets**: new index/list endpoints without pagination or `limit`; `all.to_a`, `each` where `find_each`/`in_batches` is needed; exports that load everything; `destroy_all` where `delete_all` plus explicit cleanup is intended.
- **Indexes**: new predicates, orderings, and foreign keys backed by indexes; composite index column order matching the query; partial indexes for status-style filters where the repo uses them.
- **Transactions and locks**: HTTP calls, job enqueues, or sleeps inside transactions; `with_lock`/`lock!` ordering across tables (deadlocks); long transactions on hot tables; optimistic versus pessimistic locking consistency.
- **External calls**: `Net::HTTP` and Faraday clients with explicit open/read timeouts (defaults are 60 seconds); retries with backoff and a bound; circuit breaking where the repo has it; calls made from a request path that could be a job.
- **Caching**: `Rails.cache` keys that include every input, expiries set, stampede risk on hot keys, caching objects that are not safe to serialise, memoisation on long-lived objects.
- **Jobs**: large serialised arguments; fan-out in loops (`perform_later` per record) versus batching; retry storms; queue choice.
- **Ruby hot paths**: string building with `+=` in loops, regex literals compiled per call inside loops, `Array#include?` on large arrays (use a `Set`), repeated `Hash#merge` allocating, `sort` with expensive block versus `sort_by`, `Object#dup`/`deep_dup` of large structures, symbol-to-string churn.
- **Middleware and filters** that run on every request and now do queries or network calls.
- **Views**: partial rendering in loops without `collection:`; helper methods issuing queries; N+1 through decorators.

## Idioms and patterns

Compare first against the neighbouring files from the context pack; the repository's own way beats the generic idiom. Skip anything RuboCop enforces.

**Ruby**

- Guard clauses and early returns over nested conditionals; `unless` without `else`; no `and`/`or` for control flow.
- Keyword arguments for more than two parameters; `Struct`/`Data` or a small class for data clumps; predicate methods end in `?`, dangerous ones in `!` with a safe counterpart.
- `attr_reader` over bare instance variables inside methods; `private` sections ordered consistently; constants frozen.
- Pattern matching (`case/in`) and `then` where the repo has adopted them; avoid where it has not.
- Exceptions for exceptional paths, result objects or operation outcomes for expected failures, matching what neighbouring code does.
- Comments explain why, not what; no commented-out code; TODOs carry an owner or ticket.

**Rails**

- Where things live: controllers thin, business logic in the layer the repository uses (operations, services, models, form objects, concerns). Follow the neighbours, not the textbook.
- Models: scopes over class methods for query fragments; validations in the model or form object as the repo does; `enum` with explicit values when stored as integers; no callbacks for cross-model side effects when the repo uses operations.
- Controllers: strong params in a private method; `respond_to`/API conventions matching siblings; status codes consistent with existing endpoints; errors rendered through the shared handler.
- Naming: tables, columns, associations, and routes following existing naming; REST verbs for new routes; namespaces and API versions consistent.
- Configuration via `Rails.configuration`, credentials, or ENV as the repo does, not constants in code; i18n for user-facing strings where the app is localised.
- Serialisers, presenters, and view components consistent with neighbours; no logic in views.
- Migrations: `t.timestamps`, `null: false`, foreign keys, and indexes following existing schema conventions; schema or structure file updated.

**Tests (RSpec or Minitest, as the repo uses)**

- The kind of test matches the neighbours (request specs versus controller specs, operation specs, system specs); factories versus fixtures as established; shared examples and matchers reused.
- `describe`/`context` naming reads as a specification; one behaviour per example; no testing of private methods; `subject` and `let` not overused; time controlled with `travel_to`; external HTTP stubbed with WebMock/VCR as established.
- Coverage of the failure paths, not only the happy path.

## Architecture

- **Layer placement**: a controller or job that now holds business rules; a model that knows about HTTP, sessions, or the current user; a view or serializer that issues queries; a library class that reaches into Rails internals it should not need.
- **Dependency direction**: lower layers calling upward (models calling controllers' helpers, operations calling other controllers); concerns used to hide a growing god object; circular requires; new global state.
- **Boundaries with external systems**: gateways, adapters, or clients wrap third-party APIs; error translation at the boundary; timeouts, retries, and idempotency keys live at the boundary, not scattered in callers; secrets injected, not read ad hoc.
- **Abstractions**: a new base class, module, or metaprogramming hook that has one user is speculative; a copy of an existing pattern with small variations is a missed reuse. Does the abstraction match the one the neighbours use?
- **Data model**: new tables and columns consistent with existing conventions (id type, timestamps, soft delete, tenant/account column, money representation); JSON columns hiding structure that will be queried; status fields without a state machine where the repo uses one; denormalisation without a sync strategy.
- **Deploy and compatibility**: migrations safe to run before the code is live (and after); job arguments changed while old jobs are queued; API response and event payload changes that break consumers; feature flags for behaviour switches; rollback story for data changes.
- **Observability**: new paths emit the logs, metrics, traces, or audit events the surrounding code does; failures are visible, not swallowed.
- **Trajectory**: does this change make the next likely change easier or harder? Name the pressure (duplication growing, a module changing for unrelated reasons, a boundary leaking) rather than citing a rule.
