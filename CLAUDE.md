# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Install dependencies:
```
pip install -r requirements.txt
```

Run all tests:
```
pytest
```

Run a single test file:
```
pytest tests/test_evaluator.py
```

Run the compliance checker:
```
python -m c3.main <config.cfg> <policy.yml>
```

## Architecture

C3 (Cisco Compliance Checker) evaluates Cisco IOS device configurations against a YAML-defined policy file and outputs a JSON compliance report with a score (0–100) and a list of violations.

### Data flow

1. **`c3/main.py`** — entry point. Parses a `.cfg` file via `ciscoconfparse2.CiscoConfParse`, loads policy rules, calls `evaluate_rule` for each, tallies a score and `ok`/`warning`/`critical` status.
2. **`c3/loader.py`** — reads the policy YAML and normalises it into a flat list of `Rule` dataclass instances. The YAML hierarchy is `policies → {required|forbidden} → policy_name → rules[]`.
3. **`c3/scopes.py`** — maps a scope name (`global`, `interfaces`, `vty`, or an arbitrary regex) to the matching `IOSCfgLine` objects from the parsed config.
4. **`c3/evaluator.py`** — for each `IOSCfgLine` in scope: (a) runs `conditions` to decide whether this object is subject to the rule, then (b) runs `match` patterns against child lines to determine compliance. Returns `Violation` instances.
5. **`c3/conditions.py`** — implements `all`/`any` logic for `conditions` blocks using `re_search_children` on `IOSCfgLine`.
6. **`c3/types.py`** — shared dataclasses (`Rule`, `Violation`, `ComplianceResult`) and `TypedDict` schemas for YAML structures.

### Policy YAML structure

```yaml
policies:
  required:          # or `forbidden`
    <policy_name>:
      scope: global | interfaces | vty | <regex>
      rules:
        - <rule_name>:
          severity: info | warning | critical
          conditions:          # filter which scope objects are evaluated
            all: [{pattern, not_pattern}]
            any: [{pattern, not_pattern}]
          match:               # check child lines for compliance
            all: [{pattern}]
            any: [{pattern}]
          message: <string>
          example: |
            <example config>
```

- **`conditions`** — filters which objects within the scope are subject to the rule (e.g., only interfaces with "Client" in the description). All `pattern` entries use `re_search_children`.
- **`match`** — the compliance check itself. For `required` rules a missing pattern is a violation; for `forbidden` rules a present pattern is a violation.
- Use single-quoted regex strings in YAML to preserve backslash escapes. Child-line patterns must include the correct leading whitespace (e.g., `'^ shutdown$'`).

### Test fixtures

- `tests/fixtures/configs/` — Cisco IOS `.cfg` snippets used as test inputs.
- `tests/fixtures/policies/test_policy.yml` — policy file used across all tests.
- `tests/conftest.py` — pytest fixtures: `compliant_config`, `telnet_config`, `policies`.
