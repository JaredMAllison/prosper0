FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY stack/ ./stack/
COPY transparency/ ./transparency/
COPY console/ ./console/

RUN pip install --no-cache-dir -e .

CMD ["python", "-m", "stack.orchestrator.main"]
