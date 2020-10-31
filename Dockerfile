# https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xix-deployment-on-docker-containers

FROM python:3.8-slim
RUN apt-get update && apt-get install -y \
    pkg-config \
    build-essential python3-dev python3-cffi \
    libcairo2 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info \
    libcairo2-dev libjpeg-dev libgif-dev

RUN adduser --system --group --home /usr/src/app --disabled-login flourish
WORKDIR /usr/src/app

RUN python -m venv venv && venv/bin/pip install -U pip
COPY requirements.txt requirements.txt
RUN venv/bin/pip install -r requirements.txt

COPY *.py docker_entry.sh ./
COPY templates templates/
RUN chmod +x docker_entry.sh

ENV FLASK_APP webapp
RUN chown -R flourish: ./
USER flourish

EXPOSE 5000
ENTRYPOINT ["./docker_entry.sh"]
