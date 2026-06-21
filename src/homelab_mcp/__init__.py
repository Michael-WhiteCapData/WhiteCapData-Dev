"""homelab-mcp — operate a k3s / Kubernetes cluster from an MCP client.

Exposes read and (guarded) write tools over the Kubernetes API so an agent
(Claude Code, Claude Desktop, Cursor, …) can inspect cluster health and perform
safe, allowlisted operations — without shelling out to kubectl.
"""

from .config import Config
from .kube import HomelabMCPError, KubeClient

__all__ = ["Config", "KubeClient", "HomelabMCPError", "__version__"]
__version__ = "0.1.1"
