#!/bin/bash
sudo apt install -y wakeonlan
sudo mkfifo /dev/hass-wolpipe

sudo chmod 644 /dev/hass-wolpipe
sudo cp -R docker-wol.service /etc/systemd/system/docker-wol.service

sudo systemctl daemon-reload
sudo systemctl start docker-wol
sudo systemctl enable docker-wol
