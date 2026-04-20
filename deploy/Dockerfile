FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY stack/ ./stack/
COPY transparency/ ./transparency/

RUN pip install --no-cache-dir -e . httpx pyyaml

CMD ["python", "-m", "stack.orchestrator.main"]
