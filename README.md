# Tareas 2 y 3: Análisis, Interceptación y Modificación del Protocolo HTTP mediante Contenedores Docker y Scapy

Una guía práctica y técnica para el despliegue, inyección, modificación en tiempo real y análisis forense del protocolo HTTP en un entorno de red aislado. Este proyecto ha sido desarrollado para el curso Taller de Redes y Servicios (2026-1) en la Universidad Diego Portales.

## Tabla de Contenidos
* [Información General](#información-general)
* [Tecnologías Utilizadas](#tecnologías-utilizadas)
* [Evidencias Lógicas (Capturas)](#evidencias-lógicas-capturas)
* [Configuración e Instalación (Setup)](#configuración-e-instalación-setup)
* [Guía de Uso](#guía-de-uso)
* [Resultados Principales (Tarea 3)](#resultados-principales-tarea-3)
* [Video Demostrativo](#video-demostrativo)
* [Contacto](#contacto)

## Información General

El objetivo central de este proyecto es estudiar detalladamente el comportamiento del protocolo HTTP (capa de aplicación) bajo un modelo cliente-servidor controlado, y posteriormente intervenir activamente dicho tráfico para evaluar la resiliencia del software involucrado.

**Tarea 2** documenta el análisis pasivo del protocolo:
* La creación de imágenes personalizadas desde cero (Nginx como servidor, Wget como cliente).
* El ciclo de vida completo de una transacción HTTP/1.1 (Handshake TCP, solicitud GET y respuesta 200 OK).
* Hipótesis analíticas frente a una eventual alteración de tráfico en ruta (*on-the-fly*).

**Tarea 3** pone a prueba dichas hipótesis mediante intervención activa con Scapy:
* Interceptación del tráfico HTTP mediante ARP Spoofing + NFQUEUE, usando un tercer contenedor (`scapy_mitm`).
* Dos inyecciones de tráfico mediante técnicas de *fuzzing* (método/versión HTTP inválidos, cabecera Host sobredimensionada).
* Tres modificaciones de campos específicos del protocolo HTTP en tiempo real (línea de estado, `Content-Length`, cabecera `Host`).
* Medición de dos métricas de red (latencia y pérdida de paquetes) y sus respectivas cotas de desempeño, mediante `tc netem`.

## Tecnologías Utilizadas

* **Sistema Anfitrión:** Arch Linux (Tarea 2) / Ubuntu sobre máquina virtual VMware (Tarea 3)
* **Motor de Virtualización:** Docker Engine + Docker Compose
* **Imagen Base de Contenedores:** Ubuntu (latest)
* **Servidor Web:** Nginx
* **Cliente HTTP:** GNU Wget
* **Intercepción y Manipulación de Tráfico:** Scapy, NetfilterQueue (NFQUEUE), iptables
* **Emulación de Condiciones de Red:** `tc` / `netem`
* **Analizador de Red:** Wireshark
* **Procesamiento y Gráficos de Métricas:** Python (pandas, matplotlib)

## Evidencias Lógicas (Capturas)

El repositorio incluye las imágenes lógicas de respaldo dentro de la estructura de archivos, las cuales sirven como evidencia del correcto funcionamiento:

**Tarea 2:**
* `terminal1.png`: Muestra la compilación exitosa de los Dockerfiles.
* `terminal2.png`: Registra el estado activo de los contenedores mediante `docker ps`.
* `wireshark1.png`: Expone el desglose analítico de los paquetes HTTP capturados en la interfaz bridge.

**Tarea 3:**
* Captura de Wireshark (`.pcapng`) durante las dos inyecciones de fuzzing, evidenciando los segmentos TCP `RST` devueltos por Nginx.
* Capturas de consola de Wget para cada uno de los 3 escenarios de modificación de tráfico (403 Forbidden, descarga truncada por Content-Length, timeout por modificación del header Host).
* `resultados_latencia.csv` y `resultados_perdida.csv`: datos crudos de las mediciones de métricas de red.
* `latencia_vs_throughput.png` y `perdida_vs_throughput.png`: gráficos de las métricas de red vs throughput del enlace, con sus respectivas cotas de desempeño.

## Configuración e Instalación (Setup)

El entorno completo (servidor, cliente y el contenedor de intercepción con Scapy) se levanta mediante Docker Compose:

```bash
docker compose up -d --build
docker ps
```

Instrucciones detalladas paso a paso para reproducir cada escenario de la Tarea 3 (fuzzing, modificación en tiempo real y métricas de red) se encuentran en [`INSTRUCCIONES_TAREA3.md`](./INSTRUCCIONES_TAREA3.md).

## Guía de Uso

Ver [`INSTRUCCIONES_TAREA3.md`](./INSTRUCCIONES_TAREA3.md) para el detalle completo de comandos, incluyendo:
* Obtención de las IPs de los contenedores.
* Ejecución de las 2 inyecciones de fuzzing (`scapy-mitm/fuzz_inject.py`).
* Ejecución de ARP spoofing y los 3 escenarios de modificación en tiempo real (`scapy-mitm/arp_spoof.py`, `scapy-mitm/mitm_modify.py`).
* Medición de métricas de red y generación de gráficos (`metrics/medir_metricas.sh`, `metrics/plot_metrics.py`).

## Resultados Principales (Tarea 3)

| Escenario | Resultado observado |
|---|---|
| Fuzzing 1 — método/versión inválidos | Servidor responde con TCP `RST` |
| Fuzzing 2 — header Host sobredimensionado | Servidor responde con TCP `RST` |
| Modificación 1 — `200 OK` → `403 Forbidden` | Wget aborta con `ERROR 403: Forbidden` |
| Modificación 2 — `Content-Length` truncado | Descarga truncada sin error visible (`saved [61/61]`) |
| Modificación 3 — header `Host` alterado | Timeout y reintentos, sin respuesta |
| Métrica: Latencia | Cota de desempeño ≈ 5000 ms (0% éxito) |
| Métrica: Pérdida de paquetes | Cota de desempeño ≈ 60% (primeros fallos) |

El detalle completo de la metodología, hipótesis y análisis de cada resultado se encuentra en `informe.tex`.

## Video Demostrativo

Tarea 2 : https://youtu.be/9ynmeXAWJfw
Tarea 3 : https://youtu.be/Hv-c5St5hl4

## Contacto

Desarrollado por el Grupo de Trabajo de la Facultad de Ingeniería y Ciencias (UDP):
* **Nicolás Esteban González Fontecilla** - [nicolas.gonzalez9@mail.udp.cl](mailto:nicolas.gonzalez9@mail.udp.cl)
* **David Benjamin Fuentes Castro** - [david.fuentes2@mail.udp.cl](mailto:david.fuentes2@mail.udp.cl)
