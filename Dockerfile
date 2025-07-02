# Start from a lightweight python base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install the necessary system-level packages
# ADDED 'wamerican' TO THIS LIST
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    wamerican \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy your python dependencies file
COPY requirements.txt .

# Install the python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy all your project files (like main.py) into the container
COPY . .

# This is the command that koyeb will run to start your server
CMD ["python3", "main.py"]
