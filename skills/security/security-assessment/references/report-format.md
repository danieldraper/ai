# Report format

Use the following structure. Empty sections should say that no items were identified in the assessed scope. Do not manufacture findings to fill the template.

## Required document structure

```markdown
# Security Assessment

## Executive Summary
## Attack Surface
## Findings
## Potential Attack Chains
## Security Concerns Requiring Verification
## Hardening Recommendations
## Positive Security Controls
## Prioritized Remediation Plan
### Immediate
### Short term
### Longer term
## Coverage and Limitations
```

In the executive summary, state the assessed target/revision and environment, overall posture supported by evidence, counts of Critical/High/Medium/Low findings (and Informational if present), the largest 3–5 risks or fewer when warranted, and whether systemic authorization or tenant-isolation failures were found. Count only the actionable Findings section; list uncertain candidates separately. State early if the assessment is partial.

Attack Surface summarizes the application's exposed boundaries, actors, sensitive assets, and trust transitions.

## Per-finding evidence

Order findings by severity and assign stable IDs: `SEC-001`, `SEC-002`, and so on. Do not reuse an ID for a different issue during follow-up.

For each finding include:

- **Title:** a short description of the security failure.
- **Severity:** Critical, High, Medium, Low, or Informational, justified by realistic impact and prerequisites. Treat confidence independently. Do not assign High merely for a missing header. Prioritize authentication bypass, command execution, signing-secret compromise, systemic cross-tenant exposure, and attacker-controlled financial movement according to demonstrated scope and impact.
- **Confidence:** Confirmed, High confidence, Medium confidence, or Requires verification, using the definitions in the skill. Identify runtime reproduction versus source proof and any remaining assumptions.
- **Classification:** applicable CWE and/or OWASP category; omit or qualify mappings that cannot be established reliably.
- **Location:** filename, class/module, method/action, and relevant line numbers at the assessed revision. Include other affected occurrences.
- **Vulnerable code:** the smallest useful snippet, with secrets and personal data redacted.
- **Why vulnerable:** source-to-sink path, failed control, attacker capabilities, and necessary conditions.
- **Exploitation scenario:** realistic local/test steps, an example HTTP request, or parameter manipulation where useful. Use synthetic actors/data and placeholders for credentials. Do not supply destructive instructions against third-party systems.
- **Impact:** what the attacker can read, change, impersonate, execute, disrupt, or cause financially, and whose assets are affected.
- **Recommended remediation:** a specific code/configuration change; show corrected code where practical. Do not imply the fix has been applied or tested unless it has.
- **Regression test:** setup, attack/action, expected denial or safe behavior, and side-effect assertions. Use the project's existing test framework, including RSpec/Minitest for Rails when applicable.

## Other sections

Attack chains reference component finding IDs, prerequisites, evidence for each link, and combined impact. Clearly mark hypothetical links. Do not count a chain as another independent vulnerability unless it contains a distinct root cause.

Concerns requiring verification state the suspicious path, missing fact, and smallest check that would resolve it. Hardening recommendations explain their benefit without presenting them as established exploits. Positive controls cite inspected implementations or tests and avoid generalizing beyond observed coverage.

The remediation plan groups urgent production-blocking issues, important near-term fixes, and longer-term architectural/defense-in-depth improvements. Reference finding IDs and prioritize root-cause fixes that close multiple paths.

End with major areas reviewed, areas not adequately assessed, runtime tests actually performed, blocked/unrun checks, unavailable history or deployment configuration, and additional runtime/infrastructure information needed. State confidence in completeness based on the coverage ledger; do not confuse lack of findings with proof of security.
