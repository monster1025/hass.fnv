FROM certbot/certbot:latest

ADD ./update_certs.sh /update_certs.sh
RUN chmod +x /update_certs.sh 

CMD ""
ENTRYPOINT "/update_certs.sh"
