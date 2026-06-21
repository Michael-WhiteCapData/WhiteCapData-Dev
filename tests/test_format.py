from conftest import make_deployment, make_event, make_node, make_pod

from homelab_mcp import format as fmt


def test_pod_health():
    assert fmt.pod_is_healthy(make_pod("a")) is True
    assert fmt.pod_is_healthy(make_pod("b", phase="Pending")) is False
    assert fmt.pod_is_healthy(make_pod("c", ready=False)) is False
    assert fmt.pod_is_healthy(make_pod("d", phase="Succeeded", ready=False)) is True


def test_pod_rows_sort_unhealthy_first():
    pods = [make_pod("ok"), make_pod("bad", phase="CrashLoopBackOff", ready=False)]
    rows = fmt.pod_rows(pods)
    assert rows[0]["name"] == "bad" and rows[0]["ready"] is False
    assert rows[1]["name"] == "ok"


def test_pod_row_aggregates_restarts():
    assert fmt.pod_row(make_pod("x", restarts=5))["restarts"] == 5


def test_cluster_summary_counts():
    nodes = [make_node("n1"), make_node("n2", ready=False)]
    pods = [make_pod("a"), make_pod("b", phase="Pending", ready=False)]
    s = fmt.cluster_summary(nodes, pods)
    assert s["nodes"] == {"total": 2, "ready": 1}
    assert s["pods"]["total"] == 2
    assert s["pods"]["unhealthy"] == 1
    assert len(s["unhealthy_pods"]) == 1


def test_deployment_rows():
    rows = fmt.deployment_rows([make_deployment("web", ready=2, replicas=3)])
    assert rows[0]["ready_replicas"] == 2
    assert rows[0]["desired_replicas"] == 3
    assert rows[0]["available"] is False


def test_node_row_reports_pressure():
    node = make_node("n1", pressures={"MemoryPressure": "True", "DiskPressure": "False"})
    row = fmt.node_row(node)
    assert row["pressure"] == ["MemoryPressure"]
    assert row["ready"] is True


def test_event_rows_warning_first_and_limited():
    events = [
        make_event("Scheduled", type_="Normal"),
        make_event("BackOff", type_="Warning"),
        make_event("Pulled", type_="Normal"),
    ]
    rows = fmt.event_rows(events, limit=2)
    assert len(rows) == 2
    assert rows[0]["type"] == "Warning"
