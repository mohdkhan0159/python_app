# ---------------------------------------------------------
# Base image
# ---------------------------------------------------------
FROM python:3.11-slim

# ---------------------------------------------------------
# Install system dependencies (ODBC + GCC for pyodbc)
# ---------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    unixodbc \
    unixodbc-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------
# Install Microsoft ODBC Driver 18 for SQL Server
# ---------------------------------------------------------
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/12/prod.list \
        > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql18

# ---------------------------------------------------------
# Set work directory
# ---------------------------------------------------------
WORKDIR /app

# ---------------------------------------------------------
# Install Python dependencies
# ---------------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------
# Copy application code
# ---------------------------------------------------------
COPY . .

# ---------------------------------------------------------
# Expose port
# ---------------------------------------------------------
EXPOSE 8000

# ---------------------------------------------------------
# Start command for FastAPI
# ---------------------------------------------------------
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
