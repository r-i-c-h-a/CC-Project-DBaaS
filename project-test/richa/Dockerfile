FROM python:3.7-slim-stretch

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
RUN mkdir -p /richa
COPY ./requirements.txt /richa/requirements.txt
RUN pip install -r /richa/requirements.txt
COPY . /richa
WORKDIR /richa
