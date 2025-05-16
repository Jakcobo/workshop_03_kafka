FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY data/ ./data 
COPY src/ ./src
COPY model/ ./model

ENV PYTHONPATH=/app/src

CMD ["bash"]
