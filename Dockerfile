# syntax=docker/dockerfile:1
# Container image for the WhiteCapData-Dev (k3s / Kubernetes) MCP server.
#
# The server speaks MCP (JSON-RPC) over stdio and talks to your cluster through a
# mounted kubeconfig. Run interactively (-i), mounting your kubeconfig read-only:
#
#   docker build -t whitecapdata-dev .
#   docker run --rm -i \
#     -v "$HOME/.kube/config:/home/app/.kube/config:ro" \
#     -e HOMELAB_MCP_READONLY=1 \
#     whitecapdata-dev
#
# Set HOMELAB_MCP_READONLY=1 to disable all mutating tools (recommended for a
# first run). See the README for the full environment-variable reference.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    KUBECONFIG=/home/app/.kube/config

WORKDIR /app
COPY . /app
RUN pip install . \
    && useradd --create-home --uid 10001 app

USER app

ENTRYPOINT ["whitecapdata-dev"]
