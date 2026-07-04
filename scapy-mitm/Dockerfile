FROM ubuntu:latest

RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv \
    iptables iproute2 tcpdump net-tools \
    build-essential libnetfilter-queue-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip3 install --break-system-packages -r requirements.txt

COPY . /app

CMD ["tail", "-f", "/dev/null"]
