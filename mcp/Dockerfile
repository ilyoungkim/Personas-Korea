FROM python:3.12-slim

WORKDIR /app

COPY mcp/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY mcp/ /app/
COPY sql/ /app/sql/

EXPOSE 19000

# 기본은 stdio, 컨테이너에서는 streamable-http 사용
CMD ["python", "server.py", "--http"]
