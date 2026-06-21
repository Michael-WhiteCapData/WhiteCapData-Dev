"""Kubernetes API wrapper used by the MCP tools.

Reads happen through the CoreV1/AppsV1 APIs and are shaped by :mod:`format`.
Mutations are gated on the operator's config (read-only switch + namespace
allowlist) *before* any API call, so a misbehaving agent can't scale or delete
outside the sandbox the operator allowed.

The official ``kubernetes`` client is imported lazily so the pure logic (and
its tests) don't require it to be installed or a cluster to be reachable.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from . import format as fmt
from .config import Config

RESTART_ANNOTATION = "kubectl.kubernetes.io/restartedAt"


class HomelabMCPError(RuntimeError):
    """A user-facing error (bad config, blocked mutation, or API failure)."""


def _load_apis(config: Config) -> tuple[Any, Any]:
    """Load kube config (in-cluster, else kubeconfig) and return (core, apps)."""
    try:
        from kubernetes import client  # noqa: PLC0415
        from kubernetes import config as kube_config  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover - import guard
        raise HomelabMCPError(
            "The 'kubernetes' package is required. Install with: pip install homelab-mcp"
        ) from exc
    try:
        kube_config.load_incluster_config()
    except kube_config.ConfigException:
        kube_config.load_kube_config(context=config.context)
    return client.CoreV1Api(), client.AppsV1Api()


class KubeClient:
    """Thin, testable facade over the parts of the Kubernetes API we expose."""

    def __init__(self, config: Config, core_v1: Any = None, apps_v1: Any = None) -> None:
        self._config = config
        if core_v1 is None or apps_v1 is None:
            core_v1, apps_v1 = _load_apis(config)
        self._core = core_v1
        self._apps = apps_v1

    @property
    def config(self) -> Config:
        return self._config

    # -- reads ---------------------------------------------------------------

    def _pods(self, namespace: str = "") -> list[Any]:
        if namespace:
            return self._core.list_namespaced_pod(namespace).items
        return self._core.list_pod_for_all_namespaces().items

    def cluster_summary(self) -> dict[str, Any]:
        nodes = self._core.list_node().items
        return fmt.cluster_summary(nodes, self._pods())

    def list_pods(self, namespace: str = "") -> list[dict[str, Any]]:
        return fmt.pod_rows(self._pods(namespace))

    def list_deployments(self, namespace: str = "") -> list[dict[str, Any]]:
        if namespace:
            deps = self._apps.list_namespaced_deployment(namespace).items
        else:
            deps = self._apps.list_deployment_for_all_namespaces().items
        return fmt.deployment_rows(deps)

    def list_events(self, limit: int = 30) -> list[dict[str, Any]]:
        events = self._core.list_event_for_all_namespaces().items
        return fmt.event_rows(events, limit)

    def pod_logs(self, namespace: str, pod: str, tail: int = 200) -> str:
        return self._core.read_namespaced_pod_log(name=pod, namespace=namespace, tail_lines=tail)

    def node_health(self) -> list[dict[str, Any]]:
        return fmt.node_rows(self._core.list_node().items)

    # -- mutations (guarded) -------------------------------------------------

    def _guard(self, namespace: str) -> None:
        if self._config.read_only:
            raise HomelabMCPError("Server is in read-only mode; mutations are disabled.")
        if not self._config.namespace_allowed(namespace):
            allowed = ", ".join(self._config.mutable_namespaces) or "*"
            raise HomelabMCPError(
                f"Namespace '{namespace}' is not in the mutable allowlist ({allowed})."
            )

    def restart_deployment(self, namespace: str, name: str) -> str:
        self._guard(namespace)
        stamp = datetime.now(UTC).isoformat()
        body = {"spec": {"template": {"metadata": {"annotations": {RESTART_ANNOTATION: stamp}}}}}
        self._apps.patch_namespaced_deployment(name=name, namespace=namespace, body=body)
        return f"restarted deployment {namespace}/{name} at {stamp}"

    def scale_deployment(self, namespace: str, name: str, replicas: int) -> str:
        self._guard(namespace)
        if not 0 <= replicas <= self._config.max_replicas:
            raise HomelabMCPError(f"replicas must be between 0 and {self._config.max_replicas}.")
        self._apps.patch_namespaced_deployment_scale(
            name=name, namespace=namespace, body={"spec": {"replicas": replicas}}
        )
        return f"scaled deployment {namespace}/{name} to {replicas} replicas"

    def delete_pod(self, namespace: str, name: str) -> str:
        self._guard(namespace)
        self._core.delete_namespaced_pod(name=name, namespace=namespace)
        return f"deleted pod {namespace}/{name} (its controller will recreate it)"
