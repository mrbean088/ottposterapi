# Use official Playwright Python image
FROM mcr.microsoft.com/playwright/python:v1.59.0-noble

# Install system dependencies for Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    libasound2 libatk-bridge2.0-0 libatk1.0-0 libc6 \
    libcairo2 libcups2 libdbus-1-3 libdrm2 libgdk-pixbuf2.0-0 \
    libnspr4 libnss3 libx11-xcb1 libxcomposite1 libxdamage1 \
    libxrandr2 libgbm1 libxss1 libxtst6 libxkbcommon0 \
    libpango-1.0-0 libcairo-gobject2 libgtk-3-0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers with dependencies
RUN python -m playwright install --with-deps chromium

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Start the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
