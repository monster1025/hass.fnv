FROM python:3

ADD ./src /src
RUN pip3 install -r /src/requirements.txt

CMD ["python", "-u", "/src/neptun2mqtt.py"]