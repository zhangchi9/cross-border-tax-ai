# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app/backend

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY science/requirements.txt ./science/requirements.txt
COPY backend_eng/requirements.txt ./backend_eng/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r science/requirements.txt
RUN pip install --no-cache-dir -r backend_eng/requirements.txt

# Copy application code
COPY . .

# Parse knowledge base on build
RUN python -c "import sys; sys.path.insert(0, '/app/backend'); from science.services.knowledge_parser import parse_knowledge_base; parse_knowledge_base(); print('Knowledge base parsed successfully')"

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app

USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run the application with new structure
CMD ["python", "-m", "backend_eng.api.main"]