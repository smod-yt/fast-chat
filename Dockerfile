FROM python:3.14-slim

WORKDIR /

COPY ./requirements.txt .

RUN pip install -r ./requirements.txt --no-cache-dir --upgrade

COPY . .

CMD [ "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000" ]