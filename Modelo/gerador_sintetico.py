"""Gerador de dataset sintético seguindo o Contrato de Dados do projeto.

Uso:
    python gerador_sintetico.py [--registros 1500] [--dispositivos 5] [--semente 42] [--saida dataset_sintetico.csv]

Colunas (contrato): timestamp, ip, latencia_ms, perda_pacotes_pct, jitter_ms, status_real

Como os dados são gerados
-------------------------
Cada dispositivo (IP da rede local) passa por uma sequência de "episódios". Cada episódio
tem um estado (OK, RISCO ou FALHA) e dura de 5 a 20 medições seguidas, como acontece numa
rede real, em que um problema persiste por um tempo. Os estados são sorteados de três em
três (cada estado aparece uma vez a cada três episódios), o que mantém as classes equilibradas.

Em cada medição o dispositivo recebe 10 pings. Cada ping se perde com probabilidade
`p_perda`; os que voltam têm RTT = base + ruído normal(0, sigma). A partir dos pings:
- latencia_ms = média dos RTTs recebidos;
- perda_pacotes_pct = pacotes perdidos / 10 * 100;
- jitter_ms = média da diferença absoluta entre RTTs consecutivos (mesma fórmula da coleta real).
Se nenhum ping volta, latência e jitter ficam vazios (mesma convenção do dataset real limpo).

Parâmetros de cada estado (sorteados uniformemente dentro da faixa, a cada episódio):

| Estado | RTT base (ms) | sigma (ms) | p_perda       | Ideia (regra de bom senso)                     |
|--------|---------------|------------|---------------|------------------------------------------------|
| OK     | 2 a 40        | 0,5 a 5    | 0 a 0,02      | rede saudável: RTT baixo, estável, quase sem perda |
| RISCO  | 50 a 180      | 5 a 30     | 0,02 a 0,15   | rede degradada: RTT alto, oscilação, alguma perda |
| FALHA  | 150 a 500     | 20 a 80    | 0,15 a 0,6    | rede muito degradada: RTT muito alto e muita perda |
| FALHA  | -             | -          | 1             | 35% dos episódios de FALHA: dispositivo fora do ar |

As faixas se sobrepõem de propósito (ex.: RTT de 150 a 180 ms aparece em RISCO e em FALHA),
para que a árvore não acerte 100% e a acurácia no teste tenha significado.
"""
import argparse
import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

COLUNAS = ["timestamp", "ip", "latencia_ms", "perda_pacotes_pct", "jitter_ms", "status_real"]
ESTADOS = ["OK", "RISCO", "FALHA"]
PINGS_POR_MEDICAO = 10
INTERVALO_S = 10
INICIO = datetime(2026, 10, 1, tzinfo=timezone.utc)

# estado -> (faixa do RTT base, faixa do sigma, faixa da probabilidade de perda)
PARAMETROS = {
    "OK": ((2, 40), (0.5, 5), (0.0, 0.02)),
    "RISCO": ((50, 180), (5, 30), (0.02, 0.15)),
    "FALHA": ((150, 500), (20, 80), (0.15, 0.6)),
}
PROB_FALHA_TOTAL = 0.35


def sortear_episodio(estado, rng):
    if estado == "FALHA" and rng.random() < PROB_FALHA_TOTAL:
        return {"base": 0.0, "sigma": 0.0, "p_perda": 1.0}
    (base_min, base_max), (sigma_min, sigma_max), (perda_min, perda_max) = PARAMETROS[estado]
    return {
        "base": rng.uniform(base_min, base_max),
        "sigma": rng.uniform(sigma_min, sigma_max),
        "p_perda": rng.uniform(perda_min, perda_max),
    }


def medir(episodio, rng):
    """Simula uma medição de 10 pings e devolve (latencia_ms, perda_pacotes_pct, jitter_ms)."""
    rtts = [max(0.1, rng.gauss(episodio["base"], episodio["sigma"]))
            for _ in range(PINGS_POR_MEDICAO) if rng.random() >= episodio["p_perda"]]
    perda_pct = (PINGS_POR_MEDICAO - len(rtts)) / PINGS_POR_MEDICAO * 100
    if not rtts:
        return None, perda_pct, None

    latencia = sum(rtts) / len(rtts)
    if len(rtts) > 1:
        jitter = sum(abs(rtts[i] - rtts[i - 1]) for i in range(1, len(rtts))) / (len(rtts) - 1)
    else:
        jitter = 0.0
    return round(latencia, 2), round(perda_pct, 2), round(jitter, 2)


def gerar(registros, dispositivos, semente):
    rng = random.Random(semente)
    ips = [f"192.168.1.{10 + i}" for i in range(dispositivos)]
    por_dispositivo = -(-registros // dispositivos)  # divisão arredondada para cima

    linhas = []
    for ip in ips:
        instante = INICIO
        gerados = 0
        saco = []
        while gerados < por_dispositivo:
            if not saco:  # os três estados aparecem uma vez a cada três episódios, em ordem aleatória
                saco = rng.sample(ESTADOS, len(ESTADOS))
            estado = saco.pop()
            episodio = sortear_episodio(estado, rng)
            for _ in range(min(rng.randint(5, 20), por_dispositivo - gerados)):
                latencia, perda, jitter = medir(episodio, rng)
                linhas.append({
                    "timestamp": instante.isoformat(sep=" "),
                    "ip": ip,
                    "latencia_ms": latencia,
                    "perda_pacotes_pct": perda,
                    "jitter_ms": jitter,
                    "status_real": estado,
                })
                instante += timedelta(seconds=INTERVALO_S)
                gerados += 1

    linhas.sort(key=lambda linha: (linha["timestamp"], linha["ip"]))
    return linhas[:registros]


def main():
    parser = argparse.ArgumentParser(description="Gera um dataset sintético no formato do Contrato de Dados.")
    parser.add_argument("--registros", type=int, default=1500)
    parser.add_argument("--dispositivos", type=int, default=5)
    parser.add_argument("--semente", type=int, default=42)
    parser.add_argument("--saida", type=Path, default=Path(__file__).parent / "dataset_sintetico.csv")
    args = parser.parse_args()

    if args.saida.exists():
        raise SystemExit(f"{args.saida} já existe. Apague o arquivo ou use --saida para não sobrescrever.")

    linhas = gerar(args.registros, args.dispositivos, args.semente)
    with args.saida.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS, lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(linhas)

    print(f"{len(linhas)} registros salvos em {args.saida}")
    for estado in ESTADOS:
        quantidade = sum(1 for linha in linhas if linha["status_real"] == estado)
        print(f"  {estado:<6} {quantidade:>5} ({quantidade / len(linhas):.1%})")


if __name__ == "__main__":
    main()
