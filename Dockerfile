FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

RUN mkdir -p logs \
    && chmod +x cron.sh entrypoint.sh \
    && cp crontab /etc/cron.d/slang-cron \
    && chmod 0644 /etc/cron.d/slang-cron

CMD ["/app/entrypoint.sh"]
