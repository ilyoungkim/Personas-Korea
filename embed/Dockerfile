FROM python:3.12-slim

WORKDIR /app

COPY embed/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY etl/embed_poc.py /app/embed_poc.py

# 모델 사전 다운로드를 위한 캐시 (선택)
ENV HF_HOME=/app/.cache

CMD ["python", "embed_poc.py"]
