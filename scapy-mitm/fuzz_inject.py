"""
fuzz_inject.py
Construye manualmente una conexion TCP (three-way handshake) con Scapy y
envia peticiones HTTP deliberadamente malformadas (fuzzing) directamente
hacia Nginx, sin usar Wget. Esto cumple el requisito de "inyeccion de
trafico mediante tecnicas de fuzzing" del enunciado.

Uso:
    python3 fuzz_inject.py --target 172.19.0.2 --case 1
    python3 fuzz_inject.py --target 172.19.0.2 --case 2
"""
import argparse
import random
import time
from scapy.all import IP, TCP, send, sr1, conf

conf.verb = 0
SERVER_PORT = 80


def handshake(target_ip, sport):
    """Realiza el three-way handshake TCP y retorna (seq, ack) listos
    para enviar el payload de datos."""
    ip = IP(dst=target_ip)
    syn = TCP(sport=sport, dport=SERVER_PORT, flags="S", seq=random.randint(1000, 9000))
    syn_ack = sr1(ip / syn, timeout=3)
    if syn_ack is None or "S" not in syn_ack[TCP].flags:
        raise RuntimeError("No hubo respuesta SYN-ACK, revisa la IP objetivo.")

    ack = TCP(sport=sport, dport=SERVER_PORT, flags="A",
               seq=syn_ack.ack, ack=syn_ack.seq + 1)
    send(ip / ack)
    return ip, syn_ack.ack, syn_ack.seq + 1


def enviar_payload(ip, sport, seq, ack, payload_bytes):
    push = TCP(sport=sport, dport=SERVER_PORT, flags="PA", seq=seq, ack=ack)
    respuesta = sr1(ip / push / payload_bytes, timeout=3)
    return respuesta


CASOS = {
    # Caso 1: metodo HTTP invalido / version de protocolo corrupta.
    # Hipotesis: Nginx debe rechazar la linea de peticion con 400 Bad Request
    # o cerrar la conexion abruptamente al no reconocer el metodo/version.
    1: b"GEEET / HTTTP/9.9\r\nHost: servidor_http\r\n\r\n",

    # Caso 2: header Host desmedido / repetido muchas veces (fuzzing de
    # longitud de cabecera). Hipotesis: Nginx debe responder 400/431 o
    # cerrar la conexion por exceder el limite de tamano de cabecera
    # (large_client_header_buffers).
    2: b"GET / HTTP/1.1\r\n" + (b"Host: " + b"A" * 9000 + b"\r\n") + b"\r\n",
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, help="IP del servidor Nginx")
    parser.add_argument("--case", type=int, choices=CASOS.keys(), required=True)
    args = parser.parse_args()

    sport = random.randint(20000, 60000)
    print(f"[+] Iniciando handshake hacia {args.target}:{SERVER_PORT} desde puerto {sport}")
    ip, seq, ack = handshake(args.target, sport)

    payload = CASOS[args.case]
    print(f"[+] Enviando payload de fuzzing (caso {args.case}, {len(payload)} bytes)...")
    respuesta = enviar_payload(ip, sport, seq, ack, payload)

    if respuesta is None:
        print("[!] Sin respuesta del servidor (posible timeout o conexion cerrada abruptamente).")
    else:
        print("[+] Respuesta cruda del servidor:")
        if respuesta.haslayer("Raw"):
            print(respuesta["Raw"].load.decode(errors="replace"))
        else:
            respuesta.show()
