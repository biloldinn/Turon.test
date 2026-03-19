FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port (Railway will override this with PORT env var)
EXPOSE 8080

# Run bot directly with python (polling mode + Flask health check)
CMD ["python", "app.py"]
