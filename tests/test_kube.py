from unittest.mock import MagicMock

import pytest
from conftest import make_node, make_pod

from homelab_mcp.config import Config
from homelab_mcp.kube import HomelabMCPError, KubeClient


def _client(config=None, core=None, apps=None):
    return KubeClient(config or Config(), core_v1=core or MagicMock(), apps_v1=apps or MagicMock())


def test_cluster_summary_calls_apis_and_shapes():
    core = MagicMock()
    core.list_node.return_value.items = [make_node("n1")]
    core.list_pod_for_all_namespaces.return_value.items = [make_pod("a")]
    summary = _client(core=core).cluster_summary()
    assert summary["nodes"]["ready"] == 1
    core.list_node.assert_called_once()


def test_list_pods_uses_namespaced_call_when_given():
    core = MagicMock()
    core.list_namespaced_pod.return_value.items = [make_pod("a", namespace="apps")]
    _client(core=core).list_pods("apps")
    core.list_namespaced_pod.assert_called_once_with("apps")
    core.list_pod_for_all_namespaces.assert_not_called()


def test_read_only_blocks_mutations_before_api_call():
    apps = MagicMock()
    client = _client(Config(read_only=True), apps=apps)
    with pytest.raises(HomelabMCPError, match="read-only"):
        client.scale_deployment("apps", "web", 2)
    apps.patch_namespaced_deployment_scale.assert_not_called()


def test_namespace_not_in_allowlist_is_blocked():
    apps = MagicMock()
    client = _client(Config(mutable_namespaces=("apps",)), apps=apps)
    with pytest.raises(HomelabMCPError, match="not in the mutable allowlist"):
        client.delete_pod("kube-system", "coredns-x")
    # delete_pod is on core, but the guard runs first — ensure no apps call either
    apps.assert_not_called()


def test_scale_rejects_out_of_range():
    client = _client(Config(mutable_namespaces=("apps",), max_replicas=10))
    with pytest.raises(HomelabMCPError, match="between 0 and 10"):
        client.scale_deployment("apps", "web", 99)


def test_allowed_scale_calls_api():
    apps = MagicMock()
    client = _client(Config(mutable_namespaces=("apps",)), apps=apps)
    msg = client.scale_deployment("apps", "web", 3)
    apps.patch_namespaced_deployment_scale.assert_called_once()
    assert "3 replicas" in msg


def test_restart_sets_annotation_and_returns_message():
    apps = MagicMock()
    client = _client(Config(mutable_namespaces=("apps",)), apps=apps)
    msg = client.restart_deployment("apps", "web")
    args, kwargs = apps.patch_namespaced_deployment.call_args
    body = kwargs["body"]
    ann = body["spec"]["template"]["metadata"]["annotations"]
    assert "kubectl.kubernetes.io/restartedAt" in ann
    assert "restarted deployment apps/web" in msg
