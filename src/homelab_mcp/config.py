"""Environment-driven configuration for the homelab-mcp server."""

from __future__ import annotations

import os
from dataclasses import dataclass

# Sensible homelab default: only let mutating tools touch these namespaces.
# Override with HOMELAB_MCP_MUTABLE_NAMESPACES; set it to "*" to allow all.
DEFAULT_MUTABLE_NAMESPACES = ("default", "apps", "monitoring", "ci")
DEFAULT_MAX_REPLICAS = 10
_TRUE = {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Config:
    """Effective server configuration, sourced from the environment."""

    context: str | None = None
    read_only: bool = False
    mutable_namespaces: tuple[str, ...] = DEFAULT_MUTABLE_NAMESPACES
    max_replicas: int = DEFAULT_MAX_REPLICAS

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> Config:
        src = os.environ if env is None else env
        raw_ns = src.get("HOMELAB_MCP_MUTABLE_NAMESPACES")
        if raw_ns is None:
            namespaces = DEFAULT_MUTABLE_NAMESPACES
        elif raw_ns.strip() == "*":
            namespaces = ()  # empty tuple == every namespace allowed
        else:
            namespaces = tuple(n.strip() for n in raw_ns.split(",") if n.strip())
        return cls(
            context=src.get("HOMELAB_MCP_CONTEXT") or None,
            read_only=src.get("HOMELAB_MCP_READONLY", "").lower() in _TRUE,
            mutable_namespaces=namespaces,
            max_replicas=int(src.get("HOMELAB_MCP_MAX_REPLICAS", str(DEFAULT_MAX_REPLICAS))),
        )

    def namespace_allowed(self, namespace: str) -> bool:
        """True if mutating tools may act on ``namespace``.

        An empty allowlist means "all namespaces" (the operator opted in via ``*``).
        """
        return not self.mutable_namespaces or namespace in self.mutable_namespaces

    def as_dict(self) -> dict[str, object]:
        return {
            "context": self.context or "(current-context)",
            "read_only": self.read_only,
            "mutable_namespaces": list(self.mutable_namespaces) or ["*"],
            "max_replicas": self.max_replicas,
        }
