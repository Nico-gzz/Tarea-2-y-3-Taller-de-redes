# Tarea 2: Análisis del protocolo HTTP mediante contenedores Docker

Una guía práctica y técnica para el despliegue, inyección de tráfico y análisis forense del protocolo HTTP en un entorno de red aislado. Este proyecto ha sido desarrollado para el curso Taller de Redes y Servicios (2026-1) en la Universidad Diego Portales.

## Tabla de Contenidos
* [Información General](#información-general)
* [Tecnologías Utilizadas](#tecnologías-utilizadas)
* [Evidencias Lógicas (Capturas)](#evidencias-lógicas-capturas)
* [Configuración e Instalación (Setup)](#configuración-e-instalación-setup)
* [Guía de Uso](#guía-de-uso)
* [Contacto](#contacto)

## Información General
El objetivo central de este proyecto es estudiar detalladamente el comportamiento del protocolo HTTP (capa de aplicación) bajo un modelo cliente-servidor controlado. Mediante técnicas de contenedorización, se aíslan los procesos del servidor web Nginx y del cliente Wget dentro de una red virtual dedicada para capturar limpiamente las unidades de datos de protocolo (PDU) sin interferencias del sistema operativo anfitrión.

El proyecto documenta:
* La creación de imágenes personalizadas desde cero.
* El ciclo de vida completo de una transacción HTTP/1.1 (Handshake TCP, solicitud GET y respuesta 200 OK).
* El análisis de métricas e hipótesis analíticas frente a fallos por alteración de tráfico en ruta (*on-the-fly*).

## Tecnologías Utilizadas
* **Sistema Anfitrión:** Arch Linux
* **Motor de Virtualización:** Docker Engine (versión moderna con BuildKit/Buildx)
* **Imagen Base de Contenedores:** Ubuntu (latest)
* **Servidor Web:** Nginx
* **Cliente HTTP:** GNU Wget
* **Analizador de Red:** Wireshark

## Evidencias Lógicas (Capturas)
El repositorio incluye las imágenes lógicas de respaldo dentro de la estructura de archivos, las cuales sirven como evidencia del correcto funcionamiento:
* `terminal1.png`: Muestra la compilación exitosa de los Dockerfiles.
* `terminal2.png`: Registra el estado activo de los contenedores mediante `docker ps`.
* `wireshark1.png`: Expone el desglose analítico de los paquetes HTTP capturados en la interfaz bridge.

## Configuración e Instalación (Setup)
Para replicar la infraestructura localmente en una distribución basada en Linux, sigue las instrucciones detalladas a continuación.
