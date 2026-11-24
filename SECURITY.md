# Security

## Threat model

`judgelab` is a local Python library. It does not make network calls, open ports, or run as a service. The user owns all inputs: the judge callable, the dataset, the labels, and the output paths.

### Trust assumptions
- The **judge file** (`--judge x.py`) is trusted code written by the user. `judgelab` executes it directly; a malicious judge file can run arbitrary code with the user's privileges.
- The **dataset** (`eval.jsonl`) is parsed as JSON. Field values are passed verbatim to the judge and embedded in reports.
- The **config** (`judgelab.yaml`) is parsed with `yaml.safe_load`; no object construction is allowed.

### Out of scope
- Securing the LLM provider API keys the user's judge uses — that is the user's responsibility.
- Protecting against a malicious judge callable — user-owned code runs with user privileges by design.

## Mitigations in place

| Risk | Mitigation |
|---|---|
| XSS in HTML report | Jinja2 `autoescape=True` on every field |
| Arbitrary code execution via `--judge` outside cwd | Path must resolve inside cwd; override with `JUDGELAB_ALLOW_ANY_PATH=1` |
| Path traversal on report output | `to_html` / `to_json` refuse paths outside cwd by default |
| YAML deserialization RCE | `yaml.safe_load` only |
| Unbounded memory via huge fields | `JUDGELAB_MAX_FIELD_CHARS` (default 200 000) |
| Unbounded memory via huge datasets | `JUDGELAB_MAX_EXAMPLES` (default 100 000) |
| Supply-chain drift | All runtime deps pinned with `<MAJOR+1` upper bounds |
| Non-`.py` judge paths | Rejected at load |

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `JUDGELAB_ALLOW_ANY_PATH` | unset | `1` disables the cwd sandbox for judge files and report outputs |
| `JUDGELAB_MAX_FIELD_CHARS` | `200000` | Max chars per prompt/response field |
| `JUDGELAB_MAX_EXAMPLES` | `100000` | Max examples per dataset |

## Reporting a vulnerability

Please open a private security advisory on GitHub or email the maintainer. Do not file public issues for undisclosed vulnerabilities.
