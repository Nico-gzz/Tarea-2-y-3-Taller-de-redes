#!/bin/bash
# medir_metricas.sh
# Ejecutar DENTRO del contenedor cliente_http (necesita cap NET_ADMIN).
# Aplica distintos valores de latencia y perdida de paquetes con tc netem
# sobre la interfaz de salida, y mide el throughput resultante de
# descargar el recurso HTTP con wget. Los resultados quedan en dos CSV
# que luego se grafican con plot_metrics.py
#
# Uso dentro del contenedor:
#   bash medir_metricas.sh latencia
#   bash medir_metricas.sh perdida

set -e
IFACE="eth0"
URL="http://servidor_http/"
REPETICIONES=5

modo="$1"
if [[ "$modo" != "latencia" && "$modo" != "perdida" ]]; then
  echo "Uso: $0 [latencia|perdida]"
  exit 1
fi

limpiar_qdisc() {
  tc qdisc del dev "$IFACE" root 2>/dev/null || true
}

medir_descarga() {
  # Descarga el recurso REPETICIONES veces, mide tiempo total y bytes,
  # calcula throughput promedio en KB/s. Cuenta fallos (timeouts).
  local total_bytes=0
  local total_tiempo=0
  local fallos=0
  local exitos=0

  for i in $(seq 1 $REPETICIONES); do
    inicio=$(date +%s.%N)
    if wget -q -T 5 -t 1 -O /tmp/descarga.html "$URL"; then
      fin=$(date +%s.%N)
      bytes=$(stat -c%s /tmp/descarga.html)
      tiempo=$(echo "$fin - $inicio" | bc)
      total_bytes=$(echo "$total_bytes + $bytes" | bc)
      total_tiempo=$(echo "$total_tiempo + $tiempo" | bc)
      exitos=$((exitos + 1))
    else
      fallos=$((fallos + 1))
    fi
  done

  if [[ $exitos -eq 0 ]]; then
    echo "0"  # throughput 0 si todas las descargas fallaron -> cota de desempeño alcanzada
  else
    # throughput en KB/s
    echo "scale=2; ($total_bytes / 1024) / $total_tiempo" | bc
  fi
  echo "$fallos" >&2
}

if [[ "$modo" == "latencia" ]]; then
  echo "delay_ms,throughput_kbps,fallos" > resultados_latencia.csv
  for delay in 0 25 50 100 150 200 300 500 800 1200 2000 3000 5000; do
    limpiar_qdisc
    if [[ $delay -gt 0 ]]; then
      tc qdisc add dev "$IFACE" root netem delay ${delay}ms
    fi
    fallos_tmp=$(mktemp)
    throughput=$(medir_descarga 2> "$fallos_tmp")
    fallos=$(cat "$fallos_tmp")
    rm -f "$fallos_tmp"
    echo "$delay,$throughput,$fallos" | tee -a resultados_latencia.csv
  done
  limpiar_qdisc
fi

if [[ "$modo" == "perdida" ]]; then
  echo "loss_pct,throughput_kbps,fallos" > resultados_perdida.csv
  for loss in 0 5 10 20 30 40 50 60 80; do
    limpiar_qdisc
    if [[ $loss -gt 0 ]]; then
      tc qdisc add dev "$IFACE" root netem loss ${loss}%
    fi
    fallos_tmp=$(mktemp)
    throughput=$(medir_descarga 2> "$fallos_tmp")
    fallos=$(cat "$fallos_tmp")
    rm -f "$fallos_tmp"
    echo "$loss,$throughput,$fallos" | tee -a resultados_perdida.csv
  done
  limpiar_qdisc
fi

echo "[+] Listo. Revisa resultados_${modo}.csv"
