ARG PORT
FROM python:3.12-alpine AS base
WORKDIR /app
RUN apk add --no-cache build-base linux-headers
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./app .
COPY .env .env
EXPOSE ${PORT}

FROM base as dev
ENV PORT=${PORT}
CMD fastapi dev main.py --host 0.0.0.0 --port $PORT
