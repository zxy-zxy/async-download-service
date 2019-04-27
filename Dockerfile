FROM python:3.7-alpine

RUN apk --no-cache add zip

ENV PYTHONUNBUFFERED 1

COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY .env .env
COPY ./app/ /app/

WORKDIR /app/

EXPOSE 8080