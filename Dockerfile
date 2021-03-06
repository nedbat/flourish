# https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xix-deployment-on-docker-containers

FROM python:3.8-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    pkg-config \
    build-essential python3-dev python3-cffi \
    libcairo2 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info \
    libcairo2-dev libjpeg-dev libgif-dev \
 && rm -rf /var/lib/apt/lists/* \
 && adduser --system --group --home /usr/src/app --disabled-login flourish

WORKDIR /usr/src/app

COPY requirements.txt requirements.txt
RUN python -m venv venv \
 && venv/bin/pip install --no-cache-dir -U pip \
 && venv/bin/pip install --no-cache-dir -r requirements.txt

COPY --chown=flourish:flourish . ./
RUN chmod +x docker_entry.sh

ENV FLASK_APP webapp
USER flourish

EXPOSE 5000
ENTRYPOINT ["./docker_entry.sh"]
