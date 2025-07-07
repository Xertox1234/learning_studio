# Python Code Execution Environment
# Secure, isolated container for running student code
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Create a non-root user for security
RUN groupadd -r coderunner && useradd -r -g coderunner coderunner

# Install system dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install common Python packages for educational purposes
RUN pip install --no-cache-dir \
    numpy==1.24.3 \
    pandas==2.0.3 \
    matplotlib==3.7.2 \
    requests==2.31.0 \
    beautifulsoup4==4.12.2 \
    pillow==10.0.0 \
    scipy==1.11.1 \
    scikit-learn==1.3.0

# Create necessary directories
RUN mkdir -p /app/code /app/output /app/tests
RUN chown -R coderunner:coderunner /app

# Set working directory
WORKDIR /app

# Copy the code execution script
COPY execute_code.py /app/execute_code.py
RUN chmod +x /app/execute_code.py

# Switch to non-root user
USER coderunner

# Set resource limits (will be overridden by Docker run command)
# Memory: 128MB, CPU: 0.5 cores, Time: 30 seconds
ENV MEMORY_LIMIT=128m
ENV CPU_LIMIT=0.5
ENV TIME_LIMIT=30

# Default command
CMD ["python", "/app/execute_code.py"]