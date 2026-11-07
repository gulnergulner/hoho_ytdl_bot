FROM denoland/deno:bin-2.5.6 AS deno
FROM python:3.13.5-slim-bookworm
COPY --from=deno /deno /usr/local/bin/deno
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir --require-hashes -r requirements.txt
COPY bot.py ./
ENV PYTHONUNBUFFERED=1 TZ=Asia/Seoul
RUN useradd --uid 10001 --create-home bot
USER bot
ENTRYPOINT ["python", "/app/bot.py"]
