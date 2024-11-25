# Base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Set the working directory in the container
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    libzen0v5 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Download and install MediaInfo binary
RUN wget https://mediaarea.net/download/binary/libmediainfo0/23.09/libmediainfo0v5_23.09-1_amd64.deb \
    && dpkg -i libmediainfo0v5_23.09-1_amd64.deb \
    && rm libmediainfo0v5_23.09-1_amd64.deb

# Copy requirements file to the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code into the container
COPY . .

# Expose the port FastAPI will run on
EXPOSE 8000

# Command to run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
