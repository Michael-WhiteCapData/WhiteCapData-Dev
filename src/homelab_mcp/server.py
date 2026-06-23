"""The homelab-mcp MCP server.

Tools return JSON strings so the calling agent gets structured, compact data.
Reads are always available; mutations are gated by the operator's config
(read-only switch + namespace allowlist) enforced in :class:`KubeClient`.
"""

from __future__ import annotations

import json
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP
from pydantic import Field

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
    """Summarize overall cluster health in a single call.

    Start here when triaging a cluster: it returns node and pod totals plus the
    full list of unhealthy pods, giving the fastest picture of what is wrong
    before drilling in with `list_pods`, `pod_logs`, or `node_health`. Read-only.
    Returns a JSON object with node counts, pod phase totals, and unhealthy-pod
    details (name, namespace, phase, restart count).
    """
    return _json(get_client().cluster_summary())


@mcp.tool()
def list_pods(
    namespace: Annotated[
        str,
        Field(
            description="Restrict the listing to this namespace. Empty string "
            "(the default) lists pods across all namespaces."
        ),
    ] = "",
) -> str:
    """List pods with phase, restart count, and node, unhealthy pods sorted first.

    Use after `cluster_summary` to enumerate pods, optionally scoped to one
    namespace, then feed a pod name into `pod_logs`. Read-only. Returns a JSON
    array of pod objects.
    """
    return _json(get_client().list_pods(namespace))


@mcp.tool()
def list_deployments(
    namespace: Annotated[
        str,
        Field(
            description="Restrict the listing to this namespace. Empty string "
            "(the default) lists deployments across all namespaces."
        ),
    ] = "",
) -> str:
    """List deployments with their ready/desired replica counts and namespace.

    Use to check rollout health or to find a deployment to `restart_deployment`
    or `scale_deployment`. A deployment whose ready count is below its desired
    count is still rolling out or degraded. Read-only. Returns a JSON array.
    """
    return _json(get_client().list_deployments(namespace))


@mcp.tool()
def list_events(
    limit: Annotated[
        int,
        Field(description="Maximum number of recent events to return, newest first."),
    ] = 30,
) -> str:
    """Return recent cluster events, most relevant first (Warnings before Normal).

    Use to find out *why* something is unhealthy: scheduling failures, image-pull
    errors, failed probes, and OOM kills all surface here. Pair this with
    `cluster_summary` when a pod is failing but the reason is not obvious.
    Read-only. Returns a JSON array of up to `limit` events.
    """
    return _json(get_client().list_events(limit))


@mcp.tool()
def pod_logs(
    namespace: Annotated[str, Field(description="Namespace the pod runs in, e.g. 'kube-system'.")],
    pod: Annotated[str, Field(description="Exact pod name, as shown by `list_pods`.")],
    tail: Annotated[
        int,
        Field(description="Number of log lines to return from the end of the stream."),
    ] = 200,
) -> str:
    """Return the last `tail` lines of a single pod's logs as plain text.

    Use this to investigate a specific pod after `cluster_summary` or `list_pods`
    flags it as unhealthy (CrashLoopBackOff, restarts, errors). Reads the current
    container's stdout/stderr only — it does not follow/stream or fetch
    previous-container logs. Returns the raw log text, or an error message if the
    pod or namespace does not exist.
    """
    return get_client().pod_logs(namespace, pod, tail)


@mcp.tool()
def node_health() -> str:
    """Report per-node readiness, kubelet version, capacity, and pressure conditions.

    Use to diagnose node-level problems — NotReady nodes, or memory/disk/PID
    pressure — when pods are stuck Pending or being evicted. Read-only. Returns a
    JSON array with one object per node.
    """
    return _json(get_client().node_health())


# -- mutations (guarded by read-only + namespace allowlist) ------------------


@mcp.tool()
def restart_deployment(
    namespace: Annotated[
        str,
        Field(
            description="Namespace of the deployment; must be in the operator's mutable-namespace allowlist."
        ),
    ],
    name: Annotated[str, Field(description="Name of the deployment to restart.")],
) -> str:
    """Trigger a rolling restart of a deployment (like `kubectl rollout restart`).

    Use to recycle a deployment's pods after a config/secret change or to clear a
    stuck state, without changing the replica count. Mutating: rejected unless
    read-only mode is off and the namespace is in the mutable-namespace allowlist.
    Returns a JSON status object describing the triggered rollout.
    """
    return get_client().restart_deployment(namespace, name)


@mcp.tool()
def scale_deployment(
    namespace: Annotated[
        str,
        Field(
            description="Namespace of the deployment; must be in the operator's mutable-namespace allowlist."
        ),
    ],
    name: Annotated[str, Field(description="Name of the deployment to scale.")],
    replicas: Annotated[
        int,
        Field(description="Target replica count, from 0 up to the operator's configured maximum."),
    ],
) -> str:
    """Scale a deployment to a specific replica count.

    Use to manually scale a workload up or down. Mutating: rejected unless
    read-only mode is off, the namespace is allowlisted, and `replicas` is within
    the operator's configured 0..max bound. Returns a JSON status object with the
    applied replica count.
    """
    return get_client().scale_deployment(namespace, name, replicas)


@mcp.tool()
def delete_pod(
    namespace: Annotated[
        str,
        Field(description="Namespace of the pod; must be in the operator's mutable-namespace allowlist."),
    ],
    name: Annotated[str, Field(description="Name of the pod to delete.")],
) -> str:
    """Delete a single pod so its controller recreates it.

    Use to force-recreate a wedged pod (managed by a Deployment, StatefulSet,
    etc.) without restarting the whole deployment. Mutating: rejected unless
    read-only mode is off and the namespace is allowlisted. Returns a JSON status
    object.
    """
    return get_client().delete_pod(namespace, name)


@mcp.tool()
def server_info() -> str:
    """Report the server's effective configuration.

    Returns the target kube context, the read-only flag, the mutable-namespace
    allowlist, and the maximum replica bound. Use this to confirm what the server
    is permitted to do before attempting a mutation, or to understand why a
    mutating call was rejected. Read-only. Returns a JSON object.
    """
    return _json(get_client().config.as_dict())


def main() -> None:
    """Console-script entry point: run the server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
