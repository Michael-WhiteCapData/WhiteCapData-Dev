# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/), and this project adheres to
[Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-06-20

### Added
- Read tools: `cluster_summary`, `list_pods`, `list_deployments`, `list_events`,
  `pod_logs`, `node_health`, `server_info`.
- Guarded mutating tools: `restart_deployment`, `scale_deployment`, `delete_pod`.
- Safe-by-default model: read-only switch (`HOMELAB_MCP_READONLY`), namespace
  allowlist (`HOMELAB_MCP_MUTABLE_NAMESPACES`, `*` for all), bounded scale
  (`HOMELAB_MCP_MAX_REPLICAS`).
- kubeconfig/in-cluster auth with optional context (`HOMELAB_MCP_CONTEXT`).
- Unit tests for config, mappers, guard logic, and the tool layer (no cluster
  required). GitHub Actions CI on Python 3.11 and 3.12.
- MCP registry manifest (`server.json`) and PyPI Trusted Publishing workflow.

[0.1.0]: https://github.com/Michael-WhiteCapData/homelab-mcp/releases/tag/v0.1.0
