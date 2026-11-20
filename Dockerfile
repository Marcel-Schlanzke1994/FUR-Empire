FROM python:3.14-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.lock ./requirements.lock
RUN pip install --no-cache-dir -r requirements.lock && useradd --create-home --uid 10001 fur
COPY --chown=fur:fur fur_empire ./fur_empire
COPY --chown=fur:fur static ./static
RUN mkdir -p /app/data && chown fur:fur /app/data
USER fur
EXPOSE 8080
CMD ["python", "-m", "uvicorn", "fur_empire.api:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers", "--forwarded-allow-ips", "172.30.11.2", "--no-server-header"]
