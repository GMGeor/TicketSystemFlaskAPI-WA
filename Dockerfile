FROM python:3.9

COPY ./requirements.txt /app/requirements.txt
COPY . /app
WORKDIR /app

RUN apk --update add python py-pip openssl ca-certificates py-openssl wget bash linux-headers
RUN apk --update add --virtual build-dependencies libffi-dev openssl-dev python-dev py-pip build-base \
  # ENV IBM_DB_HOME /mnt/c/Users/GeorgiGeorgiev/wa-action-skill/clidriver./app/clidriver \
  # ENV LD_LIBRARY_PATH ${IBM_DB_HOME}/lib \
  && pip install --upgrade pip \
  && pip install --upgrade pipenv\
  && pip install --upgrade --no-cache-dir -r /app/requirements.txt\
  && apk del build-dependencies


ENTRYPOINT [ "python" ]

CMD [ "main.py" ]