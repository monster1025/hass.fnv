#!/bin/sh
while [ 1 ];
do
 certbot renew --agree-tos --standalone
 sleep 1d
done
