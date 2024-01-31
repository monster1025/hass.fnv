FROM python:3.10
WORKDIR /app

ADD ./src/requirements.txt /app/requirements.txt
RUN pip3 install -r requirements.txt

ADD ./src /app

CMD [ "python3", "-u", "hc2mqtt.py", "config.json" ]
