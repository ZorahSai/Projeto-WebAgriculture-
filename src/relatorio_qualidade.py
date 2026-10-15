"""Tarefa 1 — relatório de qualidade da coleta bruta, ainda sem classe.

Uso (na raiz do repositório):
    python src/relatorio_qualidade.py

Lê data/raw/medicoes_brutas.csv.gz e grava docs/relatorio_qualidade_tarefa1.md com:
registros e início/fim por fluxo, campos ausentes, duplicatas, timeouts, RTT e perda
descritos (mínimo, mediana, máximo), separação entre Período A e Período B e os caminhos
mais curtos e mais longos. O relatório não usa nenhuma classe.
"""
import argparse
import json
import numbers
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent


def tabela_md(df):
    colunas = list(df.columns)
    linhas = ["| " + " | ".join(colunas) + " |", "|" + "---|" * len(colunas)]
    for _, linha in df.iterrows():
        linhas.append("| " + " | ".join(formatar(linha[c]) for c in colunas) + " |")
    return "\n".join(linhas)


def formatar(valor):
    if isinstance(valor, numbers.Integral):
        return f"{int(valor):,}".replace(",", ".")
    if isinstance(valor, numbers.Real):
        return "" if pd.isna(valor) else f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return str(valor).replace("|", "\\|")  # o fluxo_id tem "|", que quebraria a tabela


def main():
    parser = argparse.ArgumentParser(description="Relatório de qualidade da coleta bruta (Tarefa 1).")
    parser.add_argument("--entrada", type=Path, default=RAIZ / "data" / "raw" / "medicoes_brutas.csv.gz")
    parser.add_argument("--config", type=Path, default=RAIZ / "config" / "coleta.json")
    parser.add_argument("--saida", type=Path, default=RAIZ / "docs" / "relatorio_qualidade_tarefa1.md")
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    df = pd.read_csv(args.entrada, parse_dates=["timestamp"])
    fluxos_esperados = sum(1 for d in config["destinos"] for p in d["probes"] if "excluir" not in p)

    duplicatas = int(df.duplicated(["fluxo_id", "timestamp"]).sum())
    sem_periodo = int(df["periodo"].isna().sum())
    fim_a = df[df["periodo"] == "A"].groupby("fluxo_id")["timestamp"].max()
    inicio_b = df[df["periodo"] == "B"].groupby("fluxo_id")["timestamp"].min()
    sobreposicao = int((fim_a.reindex(inicio_b.index) >= inicio_b).sum())

    por_fluxo = df.groupby("fluxo_id").agg(
        destino=("destino_fqdn", lambda s: s.iloc[0].split(".")[0]),
        origem=("pais_origem", "first"),
        registros=("timestamp", "size"),
        registros_A=("periodo", lambda s: int((s == "A").sum())),
        rtt_validos_A=("latencia_ms", lambda s: int(s[df.loc[s.index, "periodo"] == "A"].notna().sum())),
        registros_B=("periodo", lambda s: int((s == "B").sum())),
        inicio=("timestamp", "min"),
        fim=("timestamp", "max"),
        timeouts=("timeout_atual", "sum"),
        rtt_mediano_ms=("latencia_ms", "median"),
    ).reset_index()
    por_fluxo["inicio"] = por_fluxo["inicio"].dt.strftime("%d/%m %H:%M")
    por_fluxo["fim"] = por_fluxo["fim"].dt.strftime("%d/%m %H:%M")
    por_fluxo["timeouts"] = por_fluxo["timeouts"].astype(int)

    ausentes = pd.DataFrame({
        "coluna": df.columns,
        "vazios": [int(df[c].isna().sum()) for c in df.columns],
    })
    ausentes = ausentes[ausentes["vazios"] > 0]

    descricao = pd.DataFrame([
        {"medida": nome, "mínimo": df[col].min(), "mediana": df[col].median(), "máximo": df[col].max(),
         "vazios": int(df[col].isna().sum())}
        for nome, col in [("RTT médio (ms)", "latencia_ms"), ("perda (%)", "perda_pct"), ("jitter (ms)", "jitter_ms")]
    ])

    ordenado = por_fluxo.sort_values("rtt_mediano_ms")
    curtos = ordenado.head(3)[["fluxo_id", "destino", "origem", "rtt_mediano_ms"]]
    longos = ordenado.tail(3)[["fluxo_id", "destino", "origem", "rtt_mediano_ms"]]
    abaixo_minimo = por_fluxo[por_fluxo["rtt_validos_A"] < 1500]

    periodos = config["periodos"]
    texto = f"""# Relatório de qualidade — Tarefa 1 (coleta bruta, sem classe)

Gerado por `src/relatorio_qualidade.py` a partir de `data/raw/medicoes_brutas.csv.gz`.

## Resumo

| Item | Valor |
|---|---|
| Registros brutos | {formatar(len(df))} |
| Fluxos (`fluxo_id`) | {df['fluxo_id'].nunique()} (esperados pelo config, sem os excluídos: {fluxos_esperados}) |
| Destinos | {df['destino_fqdn'].nunique()} |
| Período A (baseline) | {periodos['A']['inicio_utc']} a {periodos['A']['fim_utc']}: {formatar(int((df['periodo'] == 'A').sum()))} registros |
| Período B (a rotular) | {periodos['B']['inicio_utc']} a {periodos['B']['fim_utc']}: {formatar(int((df['periodo'] == 'B').sum()))} registros |
| Registros fora dos dois períodos | {sem_periodo} |
| Fluxos com sobreposição entre A e B | {sobreposicao} |
| Duplicatas (mesmo `fluxo_id` e `timestamp`) | {duplicatas} |
| Timeouts (`timeout_atual` = 1) | {formatar(int(df['timeout_atual'].sum()))} |
| RTT igual a 0 | {int((df['latencia_ms'] == 0).sum())} |
| Jitter igual a 0 | {int((df['jitter_ms'] == 0).sum())} |
| Fluxos com menos de 1.500 RTT válidos no Período A | {len(abaixo_minimo)} |

## Campos ausentes

RTT vazio é ausência de resposta, não zero. O jitter fica vazio quando a rajada teve menos de 2 respostas.

{tabela_md(ausentes)}

## RTT, perda e jitter (todos os registros)

{tabela_md(descricao)}

## Caminhos curtos e longos no mesmo período

Os três fluxos de menor e de maior RTT mediano. A diferença entre eles é só de distância; nenhum deles é tratado como problema.

**Mais curtos**

{tabela_md(curtos)}

**Mais longos**

{tabela_md(longos)}

## Por fluxo

{tabela_md(por_fluxo)}
"""
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(texto, encoding="utf-8")
    print(f"Relatório salvo em {args.saida}")


if __name__ == "__main__":
    main()
