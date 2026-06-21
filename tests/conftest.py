"""Lightweight fakes that mimic the kubernetes client model attributes."""

from __future__ import annotations

from types import SimpleNamespace as NS


def make_pod(name, namespace="default", phase="Running", ready=True, restarts=0, node="n1"):
    cs = NS(ready=ready, restart_count=restarts)
    return NS(
        metadata=NS(name=name, namespace=namespace),
        status=NS(phase=phase, container_statuses=[cs]),
        spec=NS(node_name=node),
    )


def make_node(name, ready=True, kubelet="v1.30.0", cpu="4", memory="8Gi", pressures=None):
    conditions = [NS(type="Ready", status="True" if ready else "False")]
    for p, status in (pressures or {}).items():
        conditions.append(NS(type=p, status=status))
    return NS(
        metadata=NS(name=name),
        status=NS(
            conditions=conditions,
            node_info=NS(kubelet_version=kubelet),
            capacity={"cpu": cpu, "memory": memory},
        ),
    )


def make_deployment(name, namespace="default", replicas=3, ready=3):
    return NS(
        metadata=NS(name=name, namespace=namespace),
        spec=NS(replicas=replicas),
        status=NS(ready_replicas=ready),
    )


def make_event(reason, type_="Warning", kind="Pod", name="p", namespace="default", message="msg"):
    return NS(
        type=type_,
        reason=reason,
        involved_object=NS(kind=kind, name=name),
        metadata=NS(namespace=namespace),
        message=message,
    )
