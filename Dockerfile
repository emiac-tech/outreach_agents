# Use a slim Python 3.10 image to keep it lightweight
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (for networking and certificate verification)
RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Ensure the memory file exists in the container
RUN touch master_scraped_domains.txt

# Expose port 5000 for n8n API calls
EXPOSE 5000

# Start the agent's API server
CMD ["python", "agent_api_server.py"]
