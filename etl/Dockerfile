# ETL: parquet → PostgreSQL 적재용 컨테이너 (일회성)
FROM python:3.13-slim

WORKDIR /app

COPY etl/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY etl/ /app/
COPY sql/ /app/sql/

CMD ["python", "load_data.py"]
