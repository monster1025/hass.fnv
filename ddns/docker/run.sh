#!/bin/sh
while true
do
  echo "token=$TOKEN" > /yandex-ddns.toml
  echo "domain=$DOMAIN" >> /yandex-ddns.toml
  if [ -n "$SUBDOMAIN" ]; then
    echo "subdomain=$SUBDOMAIN" >> /yandex-ddns.toml
  fi
  echo "ttl=$TTL" >> /yandex-ddns.toml
  chmod 600 /yandex-ddns.toml
  #cat /yandex-ddns.toml
  ./app
  sleep 5m
done
