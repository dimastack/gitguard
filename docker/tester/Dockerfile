FROM python:3.11-slim

# ==== system deps ====
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    openssh-client \
    curl \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ==== Python deps ====
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ==== Copy source code ====
COPY src/ src/
COPY tests/ tests/
COPY pytest.ini .

# ==== Playwright (for UI tests) ====
RUN pip install --no-cache-dir playwright pytest-playwright && \
    playwright install --with-deps chromium

# ==== SSH setup ====
RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh
# ключі монтуються через docker-compose, тому без COPY
# known_hosts будемо додавати під час runtime, не на build stage

ENV PYTHONPATH=/app/src

# Default command: run tests (can be overridden in CI)
CMD ["pytest", "-v", "-n", "auto", "--alluredir=/app/allure-results"]
