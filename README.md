# Meltdowns

Harbor task pack for evaluating AI agents under controlled local and network faults.

Each directory under `tasks/` is a self-contained Harbor task (`task.toml`,
Docker environment, prompts, verifier). Fault injection uses a lightweight
noisy overlay (`_noisy_overlay/`: `libnoisy.so` + mitmproxy).

## Prerequisites

- Docker
- Harbor CLI
- An LLM API key for the agent (and for the taxonomy verifier judge), typically `OPENAI_API_KEY`

## Quick start

```bash
# from this repo root (default network mode: allowlist)
./scripts/meltdowns -p tasks/local-missing-dependency \
  -e docker -a opencode -m openai/gpt-4o-mini --env-file .env --yes
```

The `scripts/meltdowns` wrapper forwards all unknown flags to `harbor run`.

## Network egress modes

Containers enforce one of three outbound network modes via `--egress`:

| Mode | Flag | What the agent can reach |
|------|------|--------------------------|
| **allowlist** (default) | `--egress allowlist` | LLM API hosts + package registries only (PyPI, npm, GitHub release/raw). No general web. |
| **lockdown** | `--egress lockdown` | Loopback only (`localhost` / `127.0.0.1`). Blocks LLM APIs, package installs, and all third-party sites. |
| **open** (full access) | `--egress open` | Unrestricted public internet. |

Aliases:

- `--network-allowlist` → allowlist
- `--network-lockdown` → lockdown
- `--network-full` / `--allow-third-party-internet` → open

Examples:

```bash
# Default: allowlist (LLM + package hosts only)
./scripts/meltdowns -p tasks/local-missing-dependency \
  -e docker -a opencode -m openai/gpt-4o-mini --env-file .env --yes

# Complete lockdown (no outbound internet at all)
./scripts/meltdowns --egress lockdown \
  -p tasks/local-missing-dependency \
  -e docker -a opencode -m openai/gpt-4o-mini --env-file .env --yes

# Full third-party internet (needed for live remote URL scenarios)
./scripts/meltdowns --egress open \
  -p tasks/remote-rate-limit-429 \
  -e docker -a opencode -m openai/gpt-4o-mini --env-file .env --yes
```

**Warnings:**

- `--egress open` lets the agent contact arbitrary third-party services on the
  public internet. Only enable it when you accept that risk.
- `--egress lockdown` also blocks LLM provider APIs and package registries, so
  typical cloud-backed agents will fail unless they do not need outbound calls.

Remote scenarios that hit live approved hosts
(`remote-named-url-404`, `remote-rate-limit-429`, `remote-partial-retrieval`)
require `--egress open`.

Approved scenario hosts (reachable only when egress is `open`):

- `https://haltriedman.com/`
- `https://rishijha.com/`
- `https://www.cs.cornell.edu/~shmat/`

## Grading

Verifiers write `/logs/verifier/reward.txt` and a taxonomy measurement JSON.
The judge defaults to `gpt-4o-mini` (`TAXONOMY_JUDGE_MODEL` overrides).

## License

See `LICENSE`.
