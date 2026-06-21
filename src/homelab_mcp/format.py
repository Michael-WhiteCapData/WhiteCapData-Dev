"""Pure mappers from Kubernetes API objects to plain JSON-able structures.

These take any object that exposes the same attributes as the official
``kubernetes`` client models, so they're unit-testable with lightweight fakes
(e.g. ``types.SimpleNamespace``) — no cluster required.
"""

from __future__ import annotations

from typing import Any


def _attr(obj: Any, *path: str, default: Any = None) -> Any:
    """Safely walk a chain of attributes, returning ``default`` on any miss."""
    cur = obj
    for name in path:
        if cur is None:
            return default
        cur = getattr(cur, name, None)
    return cur if cur is not None else default


def pod_is_healthy(pod: Any) -> bool:
    """A pod is healthy if it's Running/Succeeded and all containers are ready."""
    phase = _attr(pod, "status", "phase", default="")
    if phase == "Succeeded":
        return True
    if phase != "Running":
        return False
    statuses = _attr(pod, "status", "container_statuses", default=[]) or []
    return all(getattr(cs, "ready", False) for cs in statuses)


def pod_row(pod: Any) -> dict[str, Any]:
    statuses = _attr(pod, "status", "container_statuses", default=[]) or []
    restarts = sum(getattr(cs, "restart_count", 0) or 0 for cs in statuses)
    return {
        "namespace": _attr(pod, "metadata", "namespace", default=""),
        "name": _attr(pod, "metadata", "name", default=""),
        "phase": _attr(pod, "status", "phase", default=""),
        "ready": pod_is_healthy(pod),
        "restarts": restarts,
        "node": _attr(pod, "spec", "node_name", default=""),
    }


def pod_rows(pods: list[Any]) -> list[dict[str, Any]]:
    """Rows for a pod list, unhealthy first then by namespace/name."""
    rows = [pod_row(p) for p in pods]
    rows.sort(key=lambda r: (r["ready"], r["namespace"], r["name"]))
    return rows


def deployment_row(dep: Any) -> dict[str, Any]:
    desired = _attr(dep, "spec", "replicas", default=0) or 0
    ready = _attr(dep, "status", "ready_replicas", default=0) or 0
    return {
        "namespace": _attr(dep, "metadata", "namespace", default=""),
        "name": _attr(dep, "metadata", "name", default=""),
        "ready_replicas": ready,
        "desired_replicas": desired,
        "available": ready >= desired and desired > 0,
    }


def deployment_rows(deps: list[Any]) -> list[dict[str, Any]]:
    rows = [deployment_row(d) for d in deps]
    rows.sort(key=lambda r: (r["available"], r["namespace"], r["name"]))
    return rows


def node_row(node: Any) -> dict[str, Any]:
    conditions = _attr(node, "status", "conditions", default=[]) or []
    ready = any(getattr(c, "type", "") == "Ready" and getattr(c, "status", "") == "True" for c in conditions)
    # Pressure conditions are healthy when "False".
    pressures = {
        getattr(c, "type", ""): getattr(c, "status", "")
        for c in conditions
        if getattr(c, "type", "").endswith("Pressure")
    }
    cap = _attr(node, "status", "capacity", default={}) or {}
    return {
        "name": _attr(node, "metadata", "name", default=""),
        "ready": ready,
        "kubelet": _attr(node, "status", "node_info", "kubelet_version", default=""),
        "cpu": cap.get("cpu", ""),
        "memory": cap.get("memory", ""),
        "pressure": [k for k, v in pressures.items() if v == "True"],
    }


def node_rows(nodes: list[Any]) -> list[dict[str, Any]]:
    return [node_row(n) for n in nodes]


def cluster_summary(nodes: list[Any], pods: list[Any]) -> dict[str, Any]:
    node_data = node_rows(nodes)
    pod_data = pod_rows(pods)
    unhealthy = [p for p in pod_data if not p["ready"]]
    phases: dict[str, int] = {}
    for p in pod_data:
        phases[p["phase"]] = phases.get(p["phase"], 0) + 1
    return {
        "nodes": {"total": len(node_data), "ready": sum(1 for n in node_data if n["ready"])},
        "pods": {"total": len(pod_data), "by_phase": phases, "unhealthy": len(unhealthy)},
        "unhealthy_pods": unhealthy,
    }


def event_row(ev: Any) -> dict[str, Any]:
    return {
        "type": _attr(ev, "type", default=""),
        "reason": _attr(ev, "reason", default=""),
        "object": f"{_attr(ev, 'involved_object', 'kind', default='')}/"
        f"{_attr(ev, 'involved_object', 'name', default='')}",
        "namespace": _attr(ev, "metadata", "namespace", default=""),
        "message": _attr(ev, "message", default=""),
    }


def event_rows(events: list[Any], limit: int) -> list[dict[str, Any]]:
    rows = [event_row(e) for e in events]
    # Warnings first so problems surface at the top.
    rows.sort(key=lambda r: r["type"] != "Warning")
    return rows[:limit]
