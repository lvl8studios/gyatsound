FROM python:3.13-slim

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create directory for sound files
RUN mkdir -p sounds

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

CMD uvicorn main:app --host 0.0.0.0 --port $PORT