FROM python:3.12-slim

# Metadata
LABEL maintainer="diego"
LABEL description="SNCF MCP Server — French train search"

# No .pyc files, unbuffered stdout (important for stdio MCP transport)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY server.py .

# NAVITIA_TOKEN must be provided at runtime via env var
# Never hardcode tokens in the image
ENV NAVITIA_TOKEN=""

# MCP stdio transport — no port needed
CMD ["python", "server.py"]
