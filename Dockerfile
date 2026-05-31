FROM python:3.9-slim

WORKDIR /app

# Install system dependencies required by Flet web
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Hugging Face Spaces uses port 7860
EXPOSE 7860

# Run Flet in web mode
CMD ["flet", "run", "--web", "--port", "7860", "main.py"]
