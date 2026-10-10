FROM python:3.14-slim

WORKDIR /app

COPY ./requirements.txt /app

RUN pip install -r ./requirements.txt --no-cache-dir --upgrade

COPY . /app