FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY . .

# Create learned playbooks directory
RUN mkdir -p learned_playbooks

ENV PYTHONUNBUFFERED=1

CMD ["python", "noc_monitoring_crew.py", "anomaly"]
