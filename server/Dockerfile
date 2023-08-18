FROM alpine:latest
FROM python:alpine

LABEL authors="Vlad Korol"

ENV PYTHONPATH "${PYTHONPATH}:/app"

WORKDIR /app
COPY . /app
RUN pip install -r /app/requirements.txt


EXPOSE 5000
ENTRYPOINT ["python3", "-m", "src"]