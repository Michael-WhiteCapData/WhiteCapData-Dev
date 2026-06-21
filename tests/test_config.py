from homelab_mcp.config import DEFAULT_MUTABLE_NAMESPACES, Config


def test_defaults():
    cfg = Config.from_env(env={})
    assert cfg.read_only is False
    assert cfg.context is None
    assert cfg.mutable_namespaces == DEFAULT_MUTABLE_NAMESPACES
    assert cfg.max_replicas == 10


def test_read_only_parsing():
    assert Config.from_env(env={"HOMELAB_MCP_READONLY": "true"}).read_only is True
    assert Config.from_env(env={"HOMELAB_MCP_READONLY": "1"}).read_only is True
    assert Config.from_env(env={"HOMELAB_MCP_READONLY": "no"}).read_only is False


def test_namespace_allowlist_explicit():
    cfg = Config.from_env(env={"HOMELAB_MCP_MUTABLE_NAMESPACES": "apps, ci"})
    assert cfg.mutable_namespaces == ("apps", "ci")
    assert cfg.namespace_allowed("apps") is True
    assert cfg.namespace_allowed("kube-system") is False


def test_namespace_wildcard_allows_all():
    cfg = Config.from_env(env={"HOMELAB_MCP_MUTABLE_NAMESPACES": "*"})
    assert cfg.mutable_namespaces == ()
    assert cfg.namespace_allowed("anything") is True


def test_as_dict_shows_star_for_empty():
    cfg = Config.from_env(env={"HOMELAB_MCP_MUTABLE_NAMESPACES": "*", "HOMELAB_MCP_CONTEXT": "homelab"})
    d = cfg.as_dict()
    assert d["mutable_namespaces"] == ["*"]
    assert d["context"] == "homelab"
