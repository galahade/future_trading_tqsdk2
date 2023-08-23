# syntax = docker/dockerfile:1.4
FROM --platform=$BUILDPLATFORM python:3.11-bullseye AS builder

WORKDIR /app

COPY requirements.txt requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install -r requirements.txt
ENV TZ Asia/Shanghai

COPY . .
ENTRYPOINT ["python3"]
CMD ["main.py"]
