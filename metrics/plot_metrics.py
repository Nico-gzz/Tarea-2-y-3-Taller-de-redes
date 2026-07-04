"""
plot_metrics.py
Genera los graficos "metrica vs throughput" pedidos en el enunciado,
a partir de los CSV producidos por medir_metricas.sh

Uso:
    python3 plot_metrics.py resultados_latencia.csv delay_ms "Latencia (ms)" latencia_vs_throughput.png
    python3 plot_metrics.py resultados_perdida.csv loss_pct "Perdida de paquetes (%)" perdida_vs_throughput.png
"""
import sys
import pandas as pd
import matplotlib.pyplot as plt


def graficar(csv_path, columna_x, etiqueta_x, salida_png):
    df = pd.read_csv(csv_path)

    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.plot(df[columna_x], df["throughput_kbps"], marker="o", color="tab:blue", label="Throughput (KB/s)")
    ax1.set_xlabel(etiqueta_x)
    ax1.set_ylabel("Throughput (KB/s)", color="tab:blue")
    ax1.tick_params(axis="y", labelcolor="tab:blue")

    ax2 = ax1.twinx()
    ax2.plot(df[columna_x], df["fallos"], marker="x", color="tab:red", linestyle="--", label="Fallos")
    ax2.set_ylabel("Descargas fallidas (de 5 intentos)", color="tab:red")
    ax2.tick_params(axis="y", labelcolor="tab:red")

    plt.title(f"{etiqueta_x} vs Throughput HTTP (Nginx/Wget)")
    fig.tight_layout()
    plt.savefig(salida_png, dpi=150)
    print(f"[+] Grafico guardado en {salida_png}")

    # Deteccion simple de la cota de desempeño: primer punto donde
    # throughput cae a 0 o hay fallos > 0
    degradado = df[(df["throughput_kbps"] == 0) | (df["fallos"] > 0)]
    if not degradado.empty:
        cota = degradado.iloc[0][columna_x]
        print(f"[+] Cota de desempeño estimada: a partir de {columna_x} = {cota}, el servicio se degrada.")
    else:
        print("[!] No se observó degradación en el rango probado; considera ampliar los valores en medir_metricas.sh")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print(__doc__)
        sys.exit(1)
    graficar(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
