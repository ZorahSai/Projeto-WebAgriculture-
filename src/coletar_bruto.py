"""Tarefa 1 — coleta bruta (sem rótulo) das medições públicas de ping do RIPE Atlas.

Uso (na raiz do repositório):
    python src/coletar_bruto.py [--config config/coleta.json] [--saida data/raw/json]

Para cada destino do config e cada bloco de `bloco_horas` dentro dos Períodos A e B, faz um
GET em /measurements/{id}/results/ filtrado pelas origens (probe_ids) do destino e grava a
resposta da API exatamente como veio (bytes originais, compactados em gzip):

    data/raw/json/<destino>/m<measurement_id>_<inicio>_<fim>.json.gz
    data/raw/json/<destino>/m<measurement_id>_<inicio>_<fim>.meta.json   (URL, parâmetros, status, sha256)

Regras:
- Somente GET em medições já existentes; nenhuma medição é criada e nenhum crédito é gasto.
- Os blocos são contíguos e não se sobrepõem: cada um vai de `inicio` até `fim - 1 s`.
- Idempotente: um bloco cujo arquivo já existe não é baixado de novo (rodar outra vez não duplica).
  O arquivo é gravado num temporário e renomeado no fim, então uma interrupção não deixa arquivo pela metade.
- Erros transitórios (timeout, conexão, HTTP 429 e 5xx) são tentados de novo com espera crescente.
"""
import argparse
import gzip
import hashlib
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent.parent


def ler_data(texto):
    return datetime.fromisoformat(texto.replace("Z", "+00:00"))


def formatar_data(data):
    return data.strftime("%Y%m%dT%H%MZ")


def blocos(periodos, bloco_horas):
    """Gera (periodo, inicio, fim) cobrindo os períodos em blocos contíguos de bloco_horas."""
    for nome, periodo in periodos.items():
        inicio, fim = ler_data(periodo["inicio_utc"]), ler_data(periodo["fim_utc"])
        atual = inicio
        while atual < fim:
            proximo = min(atual + timedelta(hours=bloco_horas), fim)
            yield nome, atual, proximo
            atual = proximo


def requisitar(url, params, api):
    for tentativa in range(1, api["tentativas"] + 1):
        try:
            resposta = requests.get(url, params=params, timeout=api["timeout_s"])
            if resposta.status_code in (429, 500, 502, 503, 504) and tentativa < api["tentativas"]:
                time.sleep(2 ** tentativa)
                continue
            resposta.raise_for_status()
            return resposta
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            if tentativa == api["tentativas"]:
                raise
            time.sleep(2 ** tentativa)


def coletar_bloco(destino, inicio, fim, api, pasta):
    nome_base = f"m{destino['measurement_id']}_{formatar_data(inicio)}_{formatar_data(fim)}"
    caminho_json = pasta / f"{nome_base}.json.gz"
    if caminho_json.exists():
        return "existente", None

    url = f"{api['base_url']}/measurements/{destino['measurement_id']}/results/"
    params = {
        "start": int(inicio.timestamp()),
        "stop": int(fim.timestamp()) - 1,  # fim exclusivo: o próximo bloco começa em `fim`
        "probe_ids": ",".join(str(p["probe_id"]) for p in destino["probes"]),
        "format": "json",
    }
    coletado_em = datetime.now(timezone.utc)
    resposta = requisitar(url, params, api)
    conteudo = resposta.content
    quantidade = len(json.loads(conteudo))

    pasta.mkdir(parents=True, exist_ok=True)
    temporario = caminho_json.with_suffix(".tmp")
    with gzip.GzipFile(temporario, "wb", mtime=0) as arquivo:
        arquivo.write(conteudo)

    metadados = {
        "destino_fqdn": destino["destino_fqdn"],
        "measurement_id": destino["measurement_id"],
        "probe_ids": [p["probe_id"] for p in destino["probes"]],
        "inicio_utc": inicio.isoformat(),
        "fim_utc_exclusivo": fim.isoformat(),
        "url": url,
        "parametros": params,
        "status_http": resposta.status_code,
        "quantidade_registros": quantidade,
        "coletado_em_utc": coletado_em.isoformat(),
        "sha256_resposta": hashlib.sha256(conteudo).hexdigest(),
        "arquivo": caminho_json.name,
    }
    (pasta / f"{nome_base}.meta.json").write_text(
        json.dumps(metadados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporario.replace(caminho_json)
    return "baixado", quantidade


def main():
    parser = argparse.ArgumentParser(description="Coleta bruta (Tarefa 1) das medições do RIPE Atlas.")
    parser.add_argument("--config", type=Path, default=RAIZ / "config" / "coleta.json")
    parser.add_argument("--saida", type=Path, default=RAIZ / "data" / "raw" / "json")
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    api = config["api"]
    lista_blocos = list(blocos(config["periodos"], config["bloco_horas"]))
    total = len(lista_blocos) * len(config["destinos"])
    print(f"{len(config['destinos'])} destinos x {len(lista_blocos)} blocos = {total} arquivos")

    feitos = 0
    for destino in config["destinos"]:
        pasta = args.saida / destino["destino_fqdn"].split(".")[0]
        for periodo, inicio, fim in lista_blocos:
            situacao, quantidade = coletar_bloco(destino, inicio, fim, api, pasta)
            feitos += 1
            detalhe = f"{quantidade} registros" if quantidade is not None else "já existia, não baixado"
            print(f"[{feitos}/{total}] {destino['destino_fqdn'].split('.')[0]} {periodo} "
                  f"{formatar_data(inicio)} -> {formatar_data(fim)}: {detalhe}", flush=True)
            if situacao == "baixado":
                time.sleep(api["pausa_entre_requisicoes_s"])


if __name__ == "__main__":
    main()
