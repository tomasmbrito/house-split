FROM python:3.12-slim

WORKDIR /app

# install the dependencies first, so this layer is cached when only the code changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# don't run as root; /data is where the SQLite file lives
RUN useradd --create-home appuser && mkdir /data && chown appuser /data
USER appuser
ENV DB_PATH=/data/house.db

EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "app.main:app"]
