"""The homelab-mcp MCP server.

Tools return JSON strings so the calling agent gets structured, compact data.
Reads are always available; mutations are gated by the operator's config
(read-only switch + namespace allowlist) enforced in :class:`KubeClient`.
"""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from .config import Config
from .kube import KubeClient

mcp = FastMCP("homelab")

_client: KubeClient | None = None


def get_client() -> KubeClient:
    """Lazily build the cluster client (so import never touches a cluster)."""
    global _client
    if _client is None:
        _client = KubeClient(Config.from_env())
    return _client


def set_client(client: KubeClient) -> None:
    """Replace the module-level client (used by tests)."""
    global _client
    _client = client


def _json(data: Any) -> str:
    return json.dumps(data, indent=2, default=str)


# -- reads -------------------------------------------------------------------


@mcp.tool()
def cluster_summary() -> str:
    """Node and pod health totals plus the list of unhealthy pods. Start here."""
    return _json(get_client().cluster_summary())


@mcp.tool()
def list_pods(namespace: str = "") -> str:
    """List pods (optionally one namespace). Unhealthy pods sort first."""
    return _json(get_client().list_pods(namespace))


@mcp.tool()
def list_deployments(namespace: str = "") -> str:
    """List deployments with ready/desired replica counts."""
    return _json(get_client().list_deployments(namespace))


@mcp.tool()
def list_events(limit: int = 30) -> str:
    """Recent cluster events; Warning-type events sort first."""
    return _json(get_client().list_events(limit))


@mcp.tool()
def pod_logs(namespace: str, pod: str, tail: int = 200) -> str:
    """Tail a pod's logs."""
    return get_client().pod_logs(namespace, pod, tail)


@mcp.tool()
def node_health() -> str:
    """Per-node readiness, kubelet version, capacity, and pressure conditions."""
    return _json(get_client().node_health())


# -- mutations (guarded by read-only + namespace allowlist) ------------------


@mcp.tool()
def restart_deployment(namespace: str, name: str) -> str:
    """Rollout-restart a deployment (subject to the mutable-namespace allowlist)."""
    return get_client().restart_deployment(namespace, name)


@mcp.tool()
def scale_deployment(namespace: str, name: str, replicas: int) -> str:
    """Scale a deployment to N replicas (0..max), subject to the allowlist."""
    return get_client().scale_deployment(namespace, name, replicas)


@mcp.tool()
def delete_pod(namespace: str, name: str) -> str:
    """Delete a pod so its controller recreates it (subject to the allowlist)."""
    return get_client().delete_pod(namespace, name)


@mcp.tool()
def server_info() -> str:
    """Report the effective configuration (context, read-only, allowlist)."""
    return _json(get_client().config.as_dict())


def main() -> None:
    """Console-script entry point: run the server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
