FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Only copy what the worker needs — keep the image lean
COPY worker/requirements.txt /app/worker-requirements.txt
COPY python /app/python
COPY worker /app/worker

# Install Azure + scientific deps, then install the shieldlab library in editable mode
RUN pip install --no-cache-dir -r /app/worker-requirements.txt \
    && pip install --no-cache-dir -e /app/python

# Run as a non-root user (security best-practice)
RUN addgroup --system worker && adduser --system --ingroup worker worker
USER worker

CMD ["python", "worker/queue_worker.py"]
