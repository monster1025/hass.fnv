FROM golang:latest as builder  
RUN mkdir -p /src && cd /src && git clone https://github.com/thekvs/yandex-ddns .
WORKDIR /src
RUN go get -d
#GOOS=linux GOARCH=amd64
RUN CGO_ENABLED=0 go build -a -installsuffix cgo -o app .    


FROM alpine:latest  
WORKDIR /
ADD ./run.sh /run.sh
RUN chmod +x /run.sh
COPY --from=builder /src/app .
CMD ["/run.sh"]