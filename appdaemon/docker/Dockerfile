FROM python:3.10
RUN apt update && apt -y install locales && locale-gen ru_RU.UTF-8
ENV LANG ru_RU.UTF-8
ENV LANGUAGE ru_RU:ru
ENV LC_ALL ru_RU.UTF-8
ENV PYTHONIOENCODING=utf-8

VOLUME /conf
VOLUME /certs
EXPOSE 5050

# Copy appdaemon into image
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# Download and build appdaemon, 4.0.0b2
# --branch=4.0.0b1
RUN git clone --recurse-submodules https://github.com/home-assistant/appdaemon.git .
RUN pip install --upgrade pip . && pip3 install requests python-dateutil beautifulsoup4

# Start script
RUN chmod +x /usr/src/app/dockerStart.sh

RUN pip3 install \
      attrs==19.1.0 \
      #emp_mos_api==0.12 \
      packaging==16.8 \
      #python-Levenshtein==0.12.0 \
      voluptuous==0.13.1

ADD ./emp_mos_api /emp_mos_api

CMD [ "./dockerStart.sh" ]
