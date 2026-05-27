# C3 — Cisco Compliance Checker

C3 evaluates Cisco IOS device configurations against a YAML-defined policy file and outputs a JSON compliance report with a numeric score and a list of violations.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Single device:

```bash
python -m c3.main <config.cfg> <policy.yml>
```

All `.cfg` files in a directory (combined report):

```bash
python -m c3.main --dir <path> <policy.yml>
```

The report is printed to stdout as JSON. For a single device this is an object; for `--dir` it is an array of per-device objects:

```json
{
  "device": "router1",
  "score": 70,
  "status": "warning",
  "violations": [
    {
      "rule": "aaa-model",
      "severity": "warning",
      "message": "An AAA model must be defined",
      "example": "aaa new-model\n...",
      "scope": "hostname router1"
    }
  ]
}
```

### Exit codes

| Code | Meaning |
|------|---------|
| `0`  | Fully compliant — no violations |
| `1`  | Warnings present, no critical violations |
| `2`  | One or more critical violations |
| `64` | Bad usage (wrong number of arguments) |

### Scoring

Each violation deducts points from a starting score of 100, floored at 0:

| Severity   | Deduction |
|------------|-----------|
| `critical` | 100       |
| `warning`  | 10        |
| `info`     | 0         |

A single critical violation drops the score to 0 and the check fails. Warnings accumulate — 10 or more warnings also reduce the score to 0. Info violations are reported but do not affect the score.

## Policy file format

Policies are defined in YAML. The top-level structure is `policies → required|forbidden → policy_name → rules`.

```yaml
policies:
  required:
    <policy_name>:
      scope: global | interfaces | vty | <regex>
      rules:
        <rule_name>:
          severity: info | warning | critical
          conditions:        # filter which scope objects are evaluated
            all: [{pattern, not_pattern}]
            any: [{pattern, not_pattern}]
          match:             # compliance check against child lines
            all: [{pattern}]
            any: [{pattern}]
          message: <string>
          example: |
            <remediation example>
  forbidden:
    ...
```

### Scopes

| Scope        | Matches                          |
|--------------|----------------------------------|
| `global`     | Evaluated against the full config (anchored to the `hostname` line) |
| `interfaces` | Each `interface ...` block       |
| `vty`        | Each `line vty ...` block        |
| `<regex>`    | Any top-level line matching the regex |

### `conditions` vs `match`

- **`conditions`** — filters *which* objects within the scope are subject to the rule (e.g. only interfaces whose description contains "Client"). Objects that do not satisfy the conditions are silently skipped.
- **`match`** — the compliance check itself. For `required` rules a missing pattern is a violation; for `forbidden` rules a present pattern is a violation.

Patterns use Python `re` syntax. Use single-quoted strings in YAML to preserve backslash escapes (e.g. `'^shutdown$'`). For child-line scopes (`interfaces`, `vty`) the loader automatically inserts the required leading space after `^` — policy authors do not need to add it.

## Extending policies

Policy files can include other policy files, allowing a base policy to be shared across many devices while child policies add or override rules for specific roles.

### Including a base policy

Add a top-level `include` list to any policy file. Paths are relative to the including file's location.

```yaml
# ios-access.yml
include:
  - ios.yml          # loaded first; its rules become the base

policies:
  required:
    access-switch:
      scope: interfaces
      rules:
        storm-control:
          severity: warning
          match:
            all:
              - pattern: '^storm-control broadcast level 20$'
          message: Storm control must be configured on access ports
```

Rules from `ios.yml` are evaluated first, followed by the rules defined in `ios-access.yml`. Multiple files can be listed under `include` and they are loaded in order. Includes can be nested — a base policy can itself include another base.

Circular includes (A → B → A) are detected at load time and raise an error.

### Overriding inherited rules

A child policy can replace any rule it inherits by redefining it under the same `policy_name` and `rule_name`. The child's version is used and the inherited version is discarded — no duplicate evaluation.

```yaml
# ios-critical.yml
include:
  - ios.yml

policies:
  required:
    global:              # same policy_name as in ios.yml
      scope: global
      rules:
        aaa-model:       # same rule_name — overrides the inherited rule
          severity: critical   # escalated from warning in ios.yml
          match:
            all:
              - pattern: '^aaa new-model$'
          message: AAA model is mandatory and its absence is a critical failure
```

Any rule that is not redefined is inherited unchanged.

## Running tests

```bash
pytest
```

---

## TODO

### Juniper OS support

Abstract the parser layer so that the same YAML policies can be evaluated against Junos configurations as well as IOS. The `ciscoconfparse2` dependency is IOS-specific; this would require either a Junos-capable parser or a normalisation layer that maps Junos config structure into the same scope/child-line model C3 already uses.

### JUnit XML output

Add a `--format junit` flag that emits a JUnit XML report in addition to (or instead of) JSON. GitLab's native test-report feature parses JUnit XML and surfaces each violation as a failed test case directly in the merge request pipeline UI, without operators needing to inspect raw JSON artifacts.

### Configurable fail threshold

Add a `--fail-on <severity>` flag (default: `warning`) so CI pipelines can choose the minimum severity that produces a non-zero exit code. Setting `--fail-on critical` keeps the exit code `0` for warning-only results, allowing pipelines to report warnings without blocking a merge.

