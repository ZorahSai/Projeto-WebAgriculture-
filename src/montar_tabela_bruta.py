"""Tarefa 1 — monta a tabela de medições brutas (sem rótulo) a partir dos JSONs de data/raw/json.

Uso (na raiz do repositório):
    python src/montar_tabela_bruta.py [--sobrescrever]

Lê os JSONs sem alterá-los e grava data/raw/medicoes_brutas.csv.gz, uma linha por medição
ICMP de um fluxo. As colunas estão descritas em docs/dicionario_v0.1.md. Regras principais:
- RTT ausente fica vazio, nunca 0 (a API devolve avg/min/max = -1 quando nada volta).
- jitter_ms = desvio-padrão amostral dos RTTs da rajada, só com 2 ou mais respostas; senão vazio.
- timeout_atual = 1 quando não há RTT ou a perda é 100%. O timeout continua na tabela.
- Nenhuma coluna de classe (OK, RISCO, FALHA): a rotulagem é da Tarefa 2.
"""
import argparse
import csv
import gzip
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

COLUNAS = [
    "timestamp", "periodo", "measurement_id", "probe_id", "dst_addr", "fluxo_id",
    "latencia_ms", "rtt_min_ms", "rtt_max_ms", "enviados", "recebidos", "perda_pct",
    "jitter_ms", "timeout_atual",
    # somente auditoria de diversidade; fora da futura árvore
    "destino_fqdn", "regiao", "pais_origem", "src_addr",
]


def ler_data(texto):
    return datetime.fromisoformat(texto.replace("Z", "+00:00"))


def rtt_ou_vazio(valor):
    return round(valor, 3) if isinstance(valor, (int, float)) and valor >= 0 else None


def periodo_de(instante, periodos):
    for nome, (inicio, fim) in periodos.items():
        if inicio <= instante < fim:
            return nome
    return None


def converter(registro, destino, paises, periodos):
    instante = datetime.fromtimestamp(registro["timestamp"], tz=timezone.utc)
    enviados = registro.get("sent")
    recebidos = registro.get("rcvd")
    rtts = [r["rtt"] for r in registro.get("result", []) if "rtt" in r and not r.get("dup")]

    perda = round((enviados - recebidos) / enviados * 100, 2) if enviados else None
    rtt_medio = rtt_ou_vazio(registro.get("avg")) if recebidos else None
    jitter = round(statistics.stdev(rtts), 6) if len(rtts) >= 2 else None
    timeout = 1 if rtt_medio is None or perda == 100 else 0

    return {
        "timestamp": instante.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "periodo": periodo_de(instante, periodos),
        "measurement_id": registro["msm_id"],
        "probe_id": registro["prb_id"],
        "dst_addr": registro.get("dst_addr"),
        "fluxo_id": f"{registro['prb_id']}|{registro.get('dst_addr')}",
        "latencia_ms": rtt_medio,
        "rtt_min_ms": rtt_ou_vazio(registro.get("min")) if recebidos else None,
        "rtt_max_ms": rtt_ou_vazio(registro.get("max")) if recebidos else None,
        "enviados": enviados,
        "recebidos": recebidos,
        "perda_pct": perda,
        "jitter_ms": jitter,
        "timeout_atual": timeout,
        "destino_fqdn": destino["destino_fqdn"],
        "regiao": destino["regiao"],
        "pais_origem": paises.get(registro["prb_id"]),
        "src_addr": registro.get("src_addr"),
    }


def main():
    parser = argparse.ArgumentParser(description="Monta a tabela de medições brutas a partir dos JSONs.")
    parser.add_argument("--config", type=Path, default=RAIZ / "config" / "coleta.json")
    parser.add_argument("--entrada", type=Path, default=RAIZ / "data" / "raw" / "json")
    parser.add_argument("--saida", type=Path, default=RAIZ / "data" / "raw" / "medicoes_brutas.csv.gz")
    parser.add_argument("--sobrescrever", action="store_true", help="refaz a tabela se ela já existir")
    args = parser.parse_args()

    if args.saida.exists() and not args.sobrescrever:
        raise SystemExit(f"{args.saida} já existe. Use --sobrescrever para refazer a tabela a partir dos JSONs.")

    config = json.loads(args.config.read_text(encoding="utf-8"))
    periodos = {nome: (ler_data(p["inicio_utc"]), ler_data(p["fim_utc"])) for nome, p in config["periodos"].items()}

    linhas, fora_do_config, sem_envio, excluidos = [], 0, 0, {}
    for destino in config["destinos"]:
        paises = {p["probe_id"]: p["pais"] for p in destino["probes"] if "excluir" not in p}
        motivos = {p["probe_id"]: p["excluir"] for p in destino["probes"] if "excluir" in p}
        pasta = args.entrada / destino["destino_fqdn"].split(".")[0]
        for arquivo in sorted(pasta.glob(f"m{destino['measurement_id']}_*.json.gz")):
            with gzip.open(arquivo, "rb") as entrada:
                for registro in json.loads(entrada.read()):
                    if registro["prb_id"] in motivos:
                        chave = f"{registro['prb_id']} -> {destino['destino_fqdn']}: {motivos[registro['prb_id']]}"
                        excluidos[chave] = excluidos.get(chave, 0) + 1
                        continue
                    if registro["prb_id"] not in paises:
                        fora_do_config += 1
                        continue
                    if not registro.get("sent"):  # Guia de coleta: "Sem sent, a linha sai"
                        sem_envio += 1
                        continue
                    linhas.append(converter(registro, destino, paises, periodos))

    linhas.sort(key=lambda linha: (linha["fluxo_id"], linha["timestamp"]))
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(args.saida, "wt", newline="", encoding="utf-8") as saida:
        escritor = csv.DictWriter(saida, fieldnames=COLUNAS, lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(linhas)

    print(f"{len(linhas)} medições, {len({l['fluxo_id'] for l in linhas})} fluxos -> {args.saida}")
    print(f"Registros sem pacotes enviados (sent ausente ou 0), fora da tabela: {sem_envio}")
    for chave, quantidade in excluidos.items():
        print(f"Fluxo excluído pelo config ({quantidade} registros): {chave}")
    if fora_do_config:
        print(f"ATENÇÃO: {fora_do_config} registros de probes fora do config foram ignorados.")


if __name__ == "__main__":
    main()
