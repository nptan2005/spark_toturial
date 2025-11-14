# Dockerfile token-service
FROM python:3.12-slim

WORKDIR /app

# Copy code
COPY app.py /app

# Install dependencies
RUN pip install flask prometheus_client

# Create logs folder
RUN mkdir -p /app/logs

EXPOSE 5000

# Optional: custom secret
ENV SECRET_KEY="6bd6666523acd883f4c01956bbc3c61a32cfb44bdcb61e73a7cbbcf1a2547d5993d59d98a81b85abff396c7e3c6bbaed7d01e4a5b350c2cc4c5c6762d8b09305"

CMD ["python", "app.py"]