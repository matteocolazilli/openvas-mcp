FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

RUN addgroup --gid 1001 mcp && \
    useradd -g 1001 -u 1001 mcp && \
    mkdir -p /openvas-mcp/ && \
    chown -R mcp:mcp /openvas-mcp

WORKDIR /openvas-mcp

COPY --chown=mcp:mcp . .

USER mcp

ENV UV_CACHE_DIR=/tmp/.cache/uv

RUN uv sync --no-dev

CMD ["uv", "run", "--frozen", "--no-sync", "-m", "src.main"]
