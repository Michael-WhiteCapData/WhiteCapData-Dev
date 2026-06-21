"""Tool layer delegates to the client and serializes JSON; client is stubbed."""

import json

from homelab_mcp import server
from homelab_mcp.config import Config


class StubClient:
    def __init__(self):
        self.config = Config()
        self.calls = []

    def cluster_summary(self):
        return {"nodes": {"total": 1, "ready": 1}, "pods": {"total": 0}, "unhealthy_pods": []}

    def list_pods(self, namespace=""):
        self.calls.append(("list_pods", namespace))
        return [{"name": "a", "ready": True}]

    def restart_deployment(self, namespace, name):
        self.calls.append(("restart", namespace, name))
        return f"restarted {namespace}/{name}"


def test_cluster_summary_tool_returns_json():
    server.set_client(StubClient())
    out = json.loads(server.cluster_summary())
    assert out["nodes"]["ready"] == 1


def test_list_pods_tool_delegates_namespace():
    stub = StubClient()
    server.set_client(stub)
    json.loads(server.list_pods("apps"))
    assert ("list_pods", "apps") in stub.calls


def test_restart_tool_delegates():
    stub = StubClient()
    server.set_client(stub)
    assert server.restart_deployment("apps", "web") == "restarted apps/web"
    assert ("restart", "apps", "web") in stub.calls


def test_server_info_tool_serializes_config():
    server.set_client(StubClient())
    info = json.loads(server.server_info())
    assert "mutable_namespaces" in info and "read_only" in info
