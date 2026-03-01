FROM python:3.14-alpine

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Copy requirements first for better layer caching
COPY app/requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

COPY app/ .

RUN mkdir /config && \
    adduser -D -u 1000 ticketflow && \
    chown -R ticketflow:ticketflow /app /config

USER ticketflow
CMD ["python", "ticketflow.py"]
