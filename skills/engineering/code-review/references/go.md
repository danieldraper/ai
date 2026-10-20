# Go review

Read the section for your lens. These are investigation targets, not automatic findings: confirm behaviour at the Go version in `go.mod` (loop-variable capture changed in 1.22; generics arrived in 1.18) and on the actual execution path before reporting. Where the repository documents a convention that differs from this file, the repository wins. Skip anything `gofmt`, `go vet`, `staticcheck`, or the repo's `golangci-lint` configuration already catches.

Contents: [Correctness](#correctness) · [Security](#security) · [Performance](#performance) · [Idioms and patterns](#idioms-and-patterns) · [Architecture](#architecture)

## Correctness

**Errors**

- Ignored errors (`_ = f()`, unchecked `defer f.Close()` on writable files, `json.Marshal` results); errors logged and then execution continues as if they had not happened.
- `err` shadowed by `:=` in nested scopes so the outer error is never set; `if err := ...; err != nil` chains where a later branch reuses a stale `err`.
- Wrapping with `%w` so `errors.Is`/`errors.As` work; comparing errors with `==` where wrapping is in play; sentinel errors exported and documented; returning a non-nil error together with a usable value, or a nil error with a nil value the caller dereferences.
- Errors inside goroutines that nobody collects (use `errgroup` or a channel); panics in goroutines that crash the process; `recover` that only works in the same goroutine.

**nil, zero values, and interfaces**

- Writes to a nil map; methods on nil pointer receivers; typed-nil pointers stored in interfaces (`var p *T; var i I = p` is not nil).
- Nil slice versus empty slice when it reaches JSON (`null` versus `[]`) or a caller that checks `== nil`.
- Type assertions without the `, ok` form; `switch` on an enum without a `default`, or missing a newly added case (the `exhaustive` linter if the repo uses it).

**Slices, maps, and loops**

- `append` aliasing a shared backing array (sub-slices passed to callers that append); modifying a slice while ranging; retaining large arrays through small sub-slices.
- Map iteration order relied on in output, tests, or ordering-sensitive logic; concurrent map access without a lock.
- Loop variable capture in closures and goroutines before Go 1.22; `defer` inside a loop running at function end, not iteration end.

**Concurrency and context**

- Goroutine leaks: sends on channels nobody reads, `select` without a `ctx.Done()` case, `time.After` in loops, workers without shutdown.
- `sync.WaitGroup` `Add` inside the goroutine; `wg.Wait` with no guarantee the goroutines started; closing a channel from the receiver side or twice.
- Data races on shared struct fields or maps (would `-race` catch it in a test?); a mutex copied by value when a struct is passed or embedded; locks not released on every path (`defer mu.Unlock()`); `sync.Once` misuse.
- `context.Background()` or `context.TODO()` in a request path; `ctx` accepted but not passed on; deadlines not set on outbound calls; cancellation not observed in long loops.

**Numbers, time, and money**

- Integer overflow and signed/unsigned conversions from untrusted sizes; `int` width assumptions; division by zero on computed denominators.
- `time.Duration` arithmetic with untyped versus typed ints; `time.Now()` monotonic clock versus wall time for comparisons; `time.Equal` versus `==`; UTC normalisation before storage and comparison; truncation when round-tripping through the database.
- `float64` for money or rates: use integer minor units or a decimal type, with explicit rounding and the currency carried alongside.

**Serialisation and I/O**

- JSON: unexported fields silently ignored; struct tag typos; `omitempty` dropping meaningful zero values; `interface{}` numbers decoding as `float64`; `DisallowUnknownFields` where strictness matters.
- `database/sql`: `rows.Err()` checked after the loop; `rows.Close()` on every path; transactions rolled back on every error path (`defer tx.Rollback()` pattern); `sql.ErrNoRows` distinguished from real errors; `QueryRow` versus `Query`.
- HTTP: `resp.Body.Close()` on every path and the body drained for connection reuse; status codes checked before decoding; writing a response after `http.Error`; handlers that return without writing anything.
- `defer` argument evaluation timing; `init()` ordering assumptions; package-level variables initialised with I/O.

**Tests**

- The new behaviour has a test that fails without the change; table-driven cases cover error paths and boundaries; `t.Parallel()` safe with shared fixtures; `t.Cleanup` used; no `time.Sleep` for synchronisation; concurrency changes have a test run with `-race`.

## Security

For a whole-system audit use the `security-assessment` skill. Here, trace each new or altered entry point: `source → validation → authorization → business logic → sink`.

- **Authentication and authorization**: new routes or handlers registered outside the auth middleware chain, or with middleware ordered so auth runs after side effects; per-resource and per-tenant scoping on lookups; JWT handling (`ParseUnverified`, unchecked `alg`, expiry, audience); API keys compared with `==` instead of `subtle.ConstantTimeCompare`/`hmac.Equal`.
- **Injection**: SQL built with `fmt.Sprintf` or concatenation instead of placeholders; `exec.Command("sh", "-c", ...)` or user input in arguments; `text/template` where `html/template` is needed, and `template.HTML`/`template.JS` wrapping user data; LDAP, NoSQL, or log injection through unescaped input.
- **Files and paths**: `filepath.Join` with user segments (traversal), `http.ServeFile`/`http.Dir` roots, zip and tar extraction without path validation, file permissions (`0600` versus `0644`/`0777`), temp files predictable.
- **Outbound requests**: user-controlled URLs reaching `http.Client` (SSRF, cloud metadata endpoints), redirects followed by default, DNS rebinding where allowlists are host-based.
- **Untrusted input size and shape**: `io.ReadAll` on request bodies without `http.MaxBytesReader`; decompression without limits; slice indexes or lengths taken from input (panic → denial of service); unbounded `make` sizes from input; `encoding/gob`, YAML into `interface{}`, or other deserialisation of untrusted data.
- **Crypto**: `math/rand` for anything secret (`crypto/rand`); MD5/SHA-1 for security purposes; `InsecureSkipVerify`; TLS `MinVersion` lowered; keys or nonces reused; home-grown signing.
- **Secrets and sensitive data**: hard-coded credentials; `%+v`/`%v` of structs containing secrets; `Authorization` headers, request bodies, or card data in logs, error messages, or traces; secrets in env dumps or panics. For payments code, the PCI boundary: does the change move PAN, CVV, or track data somewhere it was not before?
- **Web**: CORS origins widened; CSRF on cookie-authenticated state changes; cookie flags (`Secure`, `HttpOnly`, `SameSite`); error responses leaking internals; panics in handlers without a recovery middleware.
- **Replay and idempotency**: webhook signatures verified on the raw body with timestamp tolerance; idempotency keys scoped to the right actor; duplicate processing of financial events.
- **Dependencies and unsafe code**: new modules vetted (`govulncheck` if available), versions pinned, `go.sum` updated; new uses of `unsafe`, `reflect`, or cgo justified.

## Performance

- **Allocations in hot paths**: string concatenation in loops (`strings.Builder`), `fmt.Sprintf` for simple joins, `[]byte`↔`string` conversions, interface boxing of small values, closures capturing large state; slices and maps without capacity hints when size is known; `sync.Pool` only where profiling justifies it.
- **Goroutines and locks**: unbounded fan-out (use `errgroup.SetLimit` or a semaphore); locks held across I/O; a single mutex where `RWMutex` or sharding fits the access pattern; channels used where a slice would do; busy `select` loops with `default`.
- **Repeated work**: `regexp.MustCompile` inside functions instead of at package level; reflection or JSON marshalling per call in a hot loop; `defer` in tight loops; time formatting per log line.
- **Database**: queries in loops (N+1); `SELECT *`; missing `LIMIT`; missing indexes for new predicates; transactions spanning network calls; pool limits (`SetMaxOpenConns`, `SetConnMaxLifetime`) unset or mismatched with the database; batch inserts versus per-row.
- **HTTP clients**: a new `http.Client` or `Transport` per request instead of a shared one; no `Timeout` (the default is none); `MaxIdleConnsPerHost` for high fan-out; bodies not drained; retries without backoff and jitter; no context deadline.
- **Memory**: `io.ReadAll` where streaming would do; large maps that never shrink; caches without bounds or TTL; retaining references in long-lived slices.
- **Caching and dedup**: `singleflight` for stampedes; cache key includes every input; invalidation path exists.
- **Logging and metrics**: expensive arguments computed regardless of level; high-cardinality labels on new metrics.
- **Evidence**: if the change claims a speed-up, is there a `Benchmark*` or profile? If it adds a hot path, say what the cost is proportional to.

## Idioms and patterns

Compare first against the neighbouring files from the context pack; the repository's own way beats the generic idiom. Skip anything `gofmt`, `go vet`, or the repo's linters enforce. Defaults come from Effective Go, Go Code Review Comments, and the Uber style guide when the repo has not chosen.

- **Packages**: no `util`, `common`, or `helpers` dumping grounds; package names short and lower-case without stutter (`user.Service`, not `user.UserService`); `internal/` for non-public code; `cmd/` for binaries; tests in the same package or `_test` package as the neighbours do.
- **Interfaces**: defined by the consumer, kept small, accepted as parameters while concrete types are returned; no interface with a single implementation added only for mocking unless the repo does that everywhere.
- **Functions and signatures**: `ctx context.Context` first, `error` last; functional options or a config struct consistent with siblings; no naked returns in long functions; early returns over deep nesting; receivers short and consistent, pointer versus value receivers consistent per type.
- **Naming and docs**: MixedCaps, acronyms as `ID`, `HTTP`, `URL`; no `Get` prefix on getters; exported identifiers documented; enums as typed constants with `iota` and a `String()` method where the repo does so.
- **Errors**: wrapped with context (`fmt.Errorf("opening config: %w", err)`), not logged and returned; typed or sentinel errors where callers branch; no panics in library code; error strings lower-case without trailing punctuation.
- **Construction and state**: `NewX` constructors; useful zero values; no `init()` with side effects; no package-level mutable state; dependencies injected rather than reached for globally.
- **Generics and `any`**: generics where they remove real duplication, not for show; `any` only where the type truly varies.
- **Tests**: table-driven with named cases; `t.Helper()` in helpers; `t.Parallel()` where safe; `testify` or stdlib assertions as the repo uses; mocks generated the way the repo generates them; golden files handled as the neighbours do.
- **Tooling and hygiene**: `//nolint` carries a reason; build tags consistent; `go.mod` tidy; generated code regenerated, not hand-edited.
- **Logging, metrics, config**: the repo's structured logger (`slog`, `zap`, `zerolog`) with its field conventions; metrics named and labelled like existing ones; configuration read through the existing config layer, not ad hoc `os.Getenv`.

## Architecture

- **Dependency direction**: domain packages importing transport (`net/http`, gRPC), storage (`database/sql`, drivers), or framework packages; import cycles avoided through awkward indirection; `internal` boundaries respected.
- **Layer placement**: HTTP handlers that hold business rules; repositories that make decisions; domain types leaking `*sql.DB`, `*http.Request`, or driver types; transport DTOs used as domain models or vice versa.
- **Boundaries with external systems**: clients and gateways wrap third-party APIs; error translation at the boundary into the application's error taxonomy; timeouts, retries, circuit breaking, and idempotency keys live at the boundary, not in every caller.
- **Error taxonomy**: errors mapped to HTTP or gRPC status codes in one place; new error types fit the existing hierarchy; user-facing messages separated from internal detail.
- **Wiring and lifecycle**: construction and configuration in `main` or the existing wiring layer; graceful shutdown honoured by new servers, workers, and background loops; health and readiness updated for new dependencies.
- **Abstractions**: a new interface, generic, or base struct with a single user is speculative; a near-copy of an existing component with small variations is missed reuse; does the abstraction match the one the neighbours use?
- **Data and compatibility**: schema changes safe before and after deploy; protobuf and JSON contracts evolved compatibly (field numbers, optionality); event payload changes versioned; queued work with old argument shapes still processable; feature flags for behaviour switches; rollback story for data changes.
- **Concurrency as design**: goroutine ownership and shutdown clear; shared state encapsulated behind one owner; channels and locks not exposed across package boundaries.
- **Observability**: new paths emit logs, metrics, and traces the way surrounding code does; failures visible, not swallowed; audit events for sensitive actions.
- **Trajectory**: does this change make the next likely change easier or harder? Name the pressure (duplication growing, a package changing for unrelated reasons, a boundary leaking) rather than citing a rule.
