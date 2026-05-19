FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY new_energy_broker ./new_energy_broker
EXPOSE 8765
CMD ["uvicorn", "new_energy_broker.main:app", "--host", "0.0.0.0", "--port", "8765"]

