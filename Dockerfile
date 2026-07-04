FROM ubuntu:latest
RUN apt-get update && apt-get install -y wget iproute2 iputils-ping
CMD ["tail", "-f", "/dev/null"]
