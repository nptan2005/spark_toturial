# Dockerfile token-service
FROM python:3.12-slim

WORKDIR /app

# Copy code vào
COPY app.py /app

# Cài Flask
RUN pip install flask

# Expose port
EXPOSE 5000

# Start service
CMD ["python", "app.py"]