FROM python:3.8

LABEL version="1.0" maintainer="Daniel Stichling <stichling@fortiss.org>" tags="mqtt-client, timescaledb-client"]

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

ADD requirements.txt /usr/src/app/

RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt

ADD test-requirements.txt /usr/src/app/
ADD tox.ini /usr/src/app/
ADD setup.py /usr/src/app/

RUN tox

COPY . /usr/src/app

EXPOSE 8090

CMD ["python3", "run.py"]
