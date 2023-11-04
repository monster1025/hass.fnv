#!/bin/sh

if [ "$MQTT_USERNAME" != "" ] && [ "$MQTT_PASSWORD" != "" ];
then
        sed -i -e 's/#allow_anonymous true/allow_anonymous false/g' /mosquitto/config/mosquitto.conf
        sed -i -e 's/#password_file/password_file \/mosquitto\/passwd/g' /mosquitto/config/mosquitto.conf
        touch /mosquitto/passwd
        mosquitto_passwd -b /mosquitto/passwd $MQTT_USERNAME $MQTT_PASSWORD
fi
mosquitto -c /mosquitto/config/mosquitto.conf -v
