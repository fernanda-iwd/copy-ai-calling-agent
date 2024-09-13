# syntax=docker/dockerfile:1.4
FROM python:3.10 AS builder
ARG bland_api_key
ARG azure_openai_api_key

WORKDIR /app

COPY requirements.txt /app

RUN pip3 install -r requirements.txt

COPY ./src/* /app/

ENV BLAND_API_KEY=$bland_api_key
ENV AZURE_OPENAI_API_KEY=$azure_openai_api_key
EXPOSE 5000
ENTRYPOINT ["python3"]
CMD ["app.py"]
