FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir httpx pandas tqdm

COPY import_csv_async.py .

COPY import_database.csv /data/import_database.csv

ENTRYPOINT ["python", "import_csv_async.py"]

