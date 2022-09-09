FROM python:3.9-slim

LABEL author="Yasnov Kirill"

WORKDIR /app

COPY ./requirements.txt /app

RUN pip install -r requirements.txt --no-cache-dir

COPY . .

COPY ./static/redoc.yaml ./static

CMD ["gunicorn", "api_yamdb.wsgi:application", "--bind", "0:8000"]
