FROM python:3.10-slim

WORKDIR /app

# Install system dependencies required for mysqlclient and other packages
RUN apt-get update && apt-get install -y \
    pkg-config \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV DATABASE_URL="mysql+pymysql://root:Test%40123456@db/MessengerDB"
ENV SECRET_KEY="dev-secret-key-change-in-production"

EXPOSE 5000

# Use gunicorn with threads since app uses async_mode='threading'
CMD ["gunicorn", "--threads", "100", "--bind", "0.0.0.0:5000", "app:app"]
