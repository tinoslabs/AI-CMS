FROM python:3.11-slim

ENV PIP_DISABLE_PIP_VERSION_CHECK 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /project

RUN apt-get update -y && \
    apt-get install -y tini gcc default-libmysqlclient-dev pkg-config

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . .

ENTRYPOINT ["tini","-g","--"]

CMD ["/bin/bash","entrypoint.sh"]