FROM python:3.7-slim-stretch

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
RUN mkdir -p /kiks
COPY ./requirements.txt /kiks/requirements.txt
RUN pip install -r /kiks/requirements.txt
COPY . /kiks
WORKDIR /kiks
