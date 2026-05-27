# C3 — Cisco Compliance Checker

C3 evaluates Cisco IOS device configurations against a YAML-defined policy file and outputs a JSON compliance report with a numeric score and a list of violations.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python -m c3.main <config.cfg> <policy.yml>
```

The report is printed to stdout as JSON:

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
| `critical` | 50        |
| `warning`  | 10        |
| `info`     | 2         |

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

## Running tests

```bash
pytest
```

---

## TODO

### Juniper OS support

Abstract the parser layer so that the same YAML policies can be evaluated against Junos configurations as well as IOS. The `ciscoconfparse2` dependency is IOS-specific; this would require either a Junos-capable parser or a normalisation layer that maps Junos config structure into the same scope/child-line model C3 already uses.

### Multi-file / directory scan

Add a `--dir <path>` flag that discovers and evaluates every `.cfg` file in a directory, producing a combined JSON report (array of per-device results) and a single aggregate exit code. This is a prerequisite for clean GitLab CI integration — without it the CI script must loop externally and loses a combined score.

### JUnit XML output

Add a `--format junit` flag that emits a JUnit XML report in addition to (or instead of) JSON. GitLab's native test-report feature parses JUnit XML and surfaces each violation as a failed test case directly in the merge request pipeline UI, without operators needing to inspect raw JSON artifacts.

### Configurable fail threshold

Add a `--fail-on <severity>` flag (default: `warning`) so CI pipelines can choose the minimum severity that produces a non-zero exit code. Setting `--fail-on critical` keeps the exit code `0` for warning-only results, allowing pipelines to report warnings without blocking a merge.

### Remediation script output

Add a `--remediate` flag that renders the `example` field from each violation into a `conf t` / `end` script the operator can paste directly into the device. The `example` field already exists on every rule; this is purely a formatting pass over the violation list.

### Policy tagging and filtering

Allow rules to carry one or more tags (e.g. `tags: [cis, pci-dss]`) and add a `--tags <tag,...>` CLI flag to run only the matching subset of rules. Useful when different teams own different policy subsets or when a specific audit requires only a defined framework's controls.
