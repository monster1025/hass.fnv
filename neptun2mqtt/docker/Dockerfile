FROM python:3.8-slim

ADD ./src/requirements.txt /src/requirements.txt
RUN pip3 install -r /src/requirements.txt

ADD ./src /src

CMD ["python", "-u", "/src/neptun2mqtt.py"]
