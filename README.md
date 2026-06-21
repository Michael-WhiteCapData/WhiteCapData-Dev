<!-- mcp-name: io.github.Michael-WhiteCapData/WhiteCapData-Dev -->

# WhiteCapData-Dev

**Operate a k3s / Kubernetes cluster straight from your AI agent — safe by default.**

[![CI](https://github.com/Michael-WhiteCapData/WhiteCapData-Dev/actions/workflows/ci.yml/badge.svg)](https://github.com/Michael-WhiteCapData/WhiteCapData-Dev/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/whitecapdata-dev?color=3775A9&logo=pypi&logoColor=white)](https://pypi.org/project/whitecapdata-dev/)
[![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-server-D97757)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An [MCP](https://modelcontextprotocol.io/) server that lets an agent (Claude Code, Claude Desktop, Cursor, …) inspect and operate a **Kubernetes / k3s** cluster — your homelab box, a dev cluster, whatever your kubeconfig points at — **without shelling out to `kubectl`**. It talks to the Kubernetes API directly using your existing kubeconfig (or an in-cluster service account).

The design goal is **safe by default**: reads are always on; every mutating action (restart / scale / delete) is gated *before the API call* by a read-only switch and a namespace allowlist, so an over-eager agent can't touch `kube-system` or nuke a deployment you didn't sandbox.

> **Name note:** the PyPI package is `whitecapdata-dev` (the `homelab-k8s`-style name was taken); the import package and tools are k8s/homelab-focused as described here.

---

## Why you'd want this

- 🩺 **One-call health.** `cluster_summary` gives node + pod totals and the unhealthy pods, so the agent starts triage with real data.
- 🔒 **Safe by default.** Mutations are blocked unless the namespace is on your allowlist; flip `HOMELAB_MCP_READONLY=1` to make the whole server read-only.
- 🧰 **The operations you actually do.** Pods, deployments, events, logs, node health, rollout-restart, scale, delete-pod.
- 🪶 **No bespoke backend.** Uses the standard Kubernetes API + your kubeconfig — nothing to deploy server-side.
- ✅ **Tested.** Pure logic is unit-tested with fakes; guard logic is tested against a mocked API. No cluster needed to run the suite.

## Requirements

- A reachable cluster and a working **kubeconfig** (the same one `kubectl` uses), or run it in-cluster with a service account.
- Python 3.11+ (or just `uvx`).

## Install

```bash
uvx whitecapdata-dev          # run directly
# or
pip install whitecapdata-dev  # then run: whitecapdata-dev
```

### Claude Code

```bash
claude mcp add homelab -- uvx whitecapdata-dev
```

### Claude Desktop / Cursor

```jsonc
{
  "mcpServers": {
    "homelab": {
      "command": "uvx",
      "args": ["whitecapdata-dev"],
      "env": {
        "HOMELAB_MCP_MUTABLE_NAMESPACES": "default,apps,monitoring",
        "HOMELAB_MCP_READONLY": "0"
      }
    }
  }
}
```

## Tools

| Tool | Kind | Description |
| --- | --- | --- |
| `cluster_summary` | read | Node/pod health totals + unhealthy pods |
| `list_pods` | read | Pods (optionally one namespace), unhealthy first |
| `list_deployments` | read | Deployments with ready/desired replicas |
| `list_events` | read | Recent events, Warnings first |
| `pod_logs` | read | Tail a pod's logs |
| `node_health` | read | Per-node readiness, kubelet, capacity, pressure |
| `restart_deployment` | **write** | Rollout-restart (allowlisted namespaces) |
| `scale_deployment` | **write** | Scale to N replicas (0..max, allowlisted) |
| `delete_pod` | **write** | Delete a pod; its controller recreates it (allowlisted) |
| `server_info` | read | Effective config (context, read-only, allowlist) |

## Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `HOMELAB_MCP_CONTEXT` | current-context | kubeconfig context to use |
| `HOMELAB_MCP_READONLY` | `0` | `1`/`true` disables all mutating tools |
| `HOMELAB_MCP_MUTABLE_NAMESPACES` | `default,apps,monitoring,ci` | Namespaces mutations may touch; `*` = all |
| `HOMELAB_MCP_MAX_REPLICAS` | `10` | Upper bound for `scale_deployment` |

## Safety model

1. **Read-only switch** — `HOMELAB_MCP_READONLY=1` rejects every mutating tool up front.
2. **Namespace allowlist** — mutating tools refuse any namespace not in `HOMELAB_MCP_MUTABLE_NAMESPACES` (default a homelab-friendly set; `*` opts into all).
3. **Bounded scale** — `scale_deployment` clamps to `0..HOMELAB_MCP_MAX_REPLICAS`.

The cluster's own RBAC still applies on top — this server can only do what the kubeconfig identity is permitted to do.

## Development

```bash
git clone https://github.com/Michael-WhiteCapData/WhiteCapData-Dev
cd WhiteCapData-Dev
uv pip install -e ".[dev]"
ruff check .
pytest          # no cluster required — APIs are faked/mocked
```

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE) © Michael Tierney
