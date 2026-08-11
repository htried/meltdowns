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
# from this repo root
./scripts/meltdowns -p tasks/local-missing-dependency \
  -e docker -a opencode -m openai/gpt-4o-mini --env-file .env --yes
```

The `scripts/meltdowns` wrapper forwards all unknown flags to `harbor run`.

## Third-party internet (off by default)

By default, task containers only allow egress to **LLM API hosts** and **package
registries** (PyPI, npm, GitHub release/raw hosts). Other public websites are
blocked inside the container.

To allow agents to reach arbitrary third-party services (required for live remote
URL scenarios such as `remote-named-url-404`, `remote-rate-limit-429`, and
`remote-partial-retrieval`), pass:

```bash
./scripts/meltdowns --allow-third-party-internet \
  -p tasks/remote-rate-limit-429 \
  -e docker -a opencode -m openai/gpt-4o-mini --env-file .env --yes
```

**Warning:** `--allow-third-party-internet` lets the agent contact third-party
network services on the public internet. Only enable it when you accept that
risk for the run.

Approved scenario hosts used by remote tasks (when third-party egress is on):

- `https://haltriedman.com/`
- `https://rishijha.com/`
- `https://www.cs.cornell.edu/~shmat/`

## Grading

Verifiers write `/logs/verifier/reward.txt` and a taxonomy measurement JSON.
The judge defaults to `gpt-4o-mini` (`TAXONOMY_JUDGE_MODEL` overrides).

## License

See `LICENSE`.
