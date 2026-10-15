"""Tarefa 2 — baseline por fluxo (Período A), métricas relativas e rótulo do Período B, corte temporal.

Uso (na raiz do repositório):
    python src/baseline_e_rotulo.py [--sobrescrever]

Entrada: data/raw/medicoes_brutas.csv.gz (Tarefa 1, não é alterado) e config/rotulagem.json.
Saídas:
    data/processed/baseline_por_fluxo.csv     uma ficha por fluxo_id, só com o Período A (congelada)
    data/processed/dataset_rotulado_B.csv.gz  Período B com métricas, classe, regra que disparou e bloco
    data/processed/corte_temporal.json        datas e N de treino / validação / teste
    docs/relatorio_tarefa2.md                 auditoria: exclusões, fichas de exemplo, contagens e 3 exemplos

Ordem (a mesma da Tarefa 2): inspeção do bruto → ficha no Período A → métricas relativas no
Período B → rótulo pela tabela (primeira linha verdadeira) → recorte temporal dentro de B.
O Período A não é rotulado e o Período B não entra na ficha.
"""
import argparse
import json
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
PROCESSADO = RAIZ / "data" / "processed"

ROTULOS_REGRA = {
    1: "FALHA: perda_pct ≥ 10 nesta medição",
    2: "FALHA: n5_timeout ≥ 3",
    3: "FALHA: z_robusto ≥ 3,5 com RTT presente",
    4: "FALHA: n5_aumento80 ≥ 2",
    5: "RISCO: desvio moderado nesta medição e n5_risco ≥ 2",
    6: "OK: nenhuma linha anterior",
}
CLASSE_DA_REGRA = {1: "FALHA", 2: "FALHA", 3: "FALHA", 4: "FALHA", 5: "RISCO", 6: "OK"}


# ---------------------------------------------------------------- baseline (Período A)

def ficha_do_fluxo(grupo, cfg):
    validos = grupo["latencia_ms"].dropna()
    mediana = validos.median()
    mad = (validos - mediana).abs().median()
    jitter = grupo["jitter_ms"].dropna()
    return pd.Series({
        "n_medicoes_A": len(grupo),
        "n_rtt_validos_A": len(validos),
        "mediana": mediana,
        "MAD": mad,
        "IQR": validos.quantile(0.75) - validos.quantile(0.25),
        "jitter_tipico": jitter.median() if len(jitter) else np.nan,
        "perda_tipica": grupo["perda_pct"].median(),
        "prop_resposta": len(validos) / len(grupo),
        "situacao": "ok" if len(validos) >= cfg["piso_rtt_validos_A"] else "baseline_insuficiente",
    })


def construir_baseline(bruto, cfg):
    periodo_a = bruto[bruto["periodo"] == "A"]
    fichas = periodo_a.groupby("fluxo_id").apply(ficha_do_fluxo, cfg=cfg, include_groups=False)
    auditoria = periodo_a.groupby("fluxo_id")[["probe_id", "dst_addr", "destino_fqdn", "pais_origem"]].first()
    fichas = auditoria.join(fichas).reset_index()
    # fluxos que só aparecem no Período B não têm ficha
    sem_a = sorted(set(bruto["fluxo_id"]) - set(fichas["fluxo_id"]))
    return fichas, sem_a


# ---------------------------------------------------------------- métricas do Período B

def metricas_relativas(b, fichas, cfg_base, cfg_regras, janela):
    b = b.merge(fichas[["fluxo_id", "mediana", "MAD", "IQR", "jitter_tipico"]], on="fluxo_id", how="inner")
    b = b.sort_values(["fluxo_id", "timestamp"]).reset_index(drop=True)

    desvio = b["latencia_ms"] - b["mediana"]
    denominador = np.where(
        b["MAD"] > 0,
        cfg_base["fator_mad"] * b["MAD"],
        np.maximum(b["IQR"] / cfg_base["fator_iqr"], cfg_base["denominador_minimo_ms"]),
    )
    z = desvio / denominador
    z = np.where((b["MAD"] == 0) & (desvio == 0), 0.0, z)
    b["z_robusto"] = np.where(b["latencia_ms"].isna(), np.nan, z)
    b["aumento_pct"] = desvio / b["mediana"] * 100  # vazio quando não há RTT

    jt, j = b["jitter_tipico"], b["jitter_ms"]
    b["jitter_relativo"] = np.select(
        [j.isna(), (jt == 0) & (j == 0), (jt == 0) & (j > 0)],
        [np.nan, 1.0, np.inf],  # jitter típico 0 e atual > 0: tratado como ≥ 3 (infinito)
        default=j / jt,
    )

    r = cfg_regras
    b["criterio_risco"] = (
        ((b["z_robusto"] >= r["risco_z_robusto_min"]) & (b["z_robusto"] < r["falha_z_robusto_min"]))
        | ((b["aumento_pct"] >= r["risco_aumento_pct_min"]) & (b["aumento_pct"] <= r["risco_aumento_pct_max"]))
        | (b["jitter_relativo"] >= r["risco_jitter_relativo_min"])
    ).astype(int)  # comparações com vazio dão falso: critério não dispara
    b["aumento80"] = (b["aumento_pct"] > r["falha_aumento_pct_limite"]).astype(int)

    # Últimas `janela` medições do mesmo fluxo dentro do Período B, incluindo a atual
    rolante = b.groupby("fluxo_id")[["timeout_atual", "aumento80", "criterio_risco"]].transform(
        lambda s: s.rolling(janela, min_periods=1).sum())
    b["n5_timeout"] = rolante["timeout_atual"].astype(int)
    b["n5_aumento80"] = rolante["aumento80"].astype(int)
    b["n5_risco"] = rolante["criterio_risco"].astype(int)
    return b


def rotular(b, r):
    condicoes = [
        b["perda_pct"] >= r["falha_perda_pct_min"],
        b["n5_timeout"] >= r["falha_n5_timeout_min"],
        b["latencia_ms"].notna() & (b["z_robusto"] >= r["falha_z_robusto_min"]),
        b["n5_aumento80"] >= r["falha_n5_aumento80_min"],
        (b["criterio_risco"] == 1) & (b["n5_risco"] >= r["risco_n5_risco_min"]),
    ]
    b["regra"] = np.select(condicoes, [1, 2, 3, 4, 5], default=6)
    b["classe"] = b["regra"].map(CLASSE_DA_REGRA)
    return b


# ---------------------------------------------------------------- corte temporal dentro de B

def cortar(b, inicio_b, fim_b, cfg_corte):
    p = cfg_corte["proporcoes"]
    duracao = fim_b - inicio_b
    fim_treino = inicio_b + duracao * p["treino"]
    fim_validacao = inicio_b + duracao * (p["treino"] + p["validacao"])
    b["bloco"] = np.select(
        [b["timestamp"] < fim_treino, b["timestamp"] < fim_validacao], ["treino", "validacao"], default="teste")

    # embargo: primeiras medições de cada fluxo na validação e no teste
    posicao = b.groupby(["fluxo_id", "bloco"]).cumcount()
    embargo = b["bloco"].isin(["validacao", "teste"]) & (posicao < cfg_corte["embargo_medicoes"])
    b.loc[embargo, "bloco"] = "embargo"
    return b, {"inicio_B": inicio_b, "fim_treino": fim_treino, "fim_validacao": fim_validacao, "fim_B": fim_b}


# ---------------------------------------------------------------- relatório

def md(df, casas=2):
    def fmt(v):
        if isinstance(v, (float, np.floating)):
            if pd.isna(v):
                return ""
            return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
        if isinstance(v, (int, np.integer)):
            return f"{int(v):,}".replace(",", ".")
        return str(v).replace("|", "\\|")
    linhas = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    linhas += ["| " + " | ".join(fmt(v) for v in linha) + " |" for linha in df.itertuples(index=False)]
    return "\n".join(linhas)


def n(valor):
    return f"{int(valor):,}".replace(",", ".")


def pct(valor):
    return f"{valor:.1%}".replace(".", ",")


def exemplo(df, mascara, ordenar_por, ascendente):
    candidatos = df[mascara].sort_values(ordenar_por, ascending=ascendente)
    return candidatos.head(1)


def escrever_relatorio(bruto, fichas, sem_a, b, cortes, caminho):
    colunas_ex = ["timestamp", "fluxo_id", "latencia_ms", "z_robusto", "aumento_pct", "jitter_relativo",
                  "perda_pct", "timeout_atual", "n5_timeout", "n5_aumento80", "n5_risco", "regra", "classe"]
    com_ficha = fichas[fichas["situacao"] == "ok"]
    excluidos = fichas[fichas["situacao"] != "ok"][["fluxo_id", "destino_fqdn", "n_rtt_validos_A", "situacao"]]
    curto = com_ficha.sort_values("mediana").head(1)
    longo = com_ficha.sort_values("mediana").tail(1)
    colunas_ficha = ["fluxo_id", "destino_fqdn", "pais_origem", "n_rtt_validos_A", "mediana", "MAD",
                     "jitter_tipico", "perda_tipica", "prop_resposta"]

    mediana_por_fluxo = b.groupby("fluxo_id")["mediana"].transform("first")
    limite_longo = com_ficha["mediana"].quantile(0.75)
    limite_curto = com_ficha["mediana"].quantile(0.25)
    ex_ok_longo = exemplo(b, (b["classe"] == "OK") & (mediana_por_fluxo >= limite_longo)
                          & (b["z_robusto"].abs() < 1), "latencia_ms", False)
    ex_risco = exemplo(b, b["classe"] == "RISCO", "n5_risco", False)
    ex_falha = exemplo(b, (b["classe"] == "FALHA") & (mediana_por_fluxo <= limite_curto)
                       & b["regra"].isin([3, 4]), "z_robusto", False)
    if ex_falha.empty:
        ex_falha = exemplo(b, (b["classe"] == "FALHA") & (b["timeout_atual"] == 1), "timestamp", True)
    exemplos = pd.concat([ex_ok_longo, ex_risco, ex_falha])[colunas_ex].copy()
    exemplos["timestamp"] = exemplos["timestamp"].dt.strftime("%d/%m %H:%M:%S")

    contagem = b["classe"].value_counts().reindex(["OK", "RISCO", "FALHA"]).fillna(0).astype(int)
    regras = b["regra"].value_counts().sort_index()
    tabela_regras = pd.DataFrame({"regra": regras.index, "descrição": [ROTULOS_REGRA[i] for i in regras.index],
                                  "medições": regras.values})

    blocos = (b.groupby("bloco")["classe"].value_counts().unstack(fill_value=0)
              .reindex(index=["treino", "embargo", "validacao", "teste"], columns=["OK", "RISCO", "FALHA"], fill_value=0))
    blocos["total"] = blocos.sum(axis=1)
    blocos = blocos.reset_index()
    fmt_data = lambda d: d.strftime("%d/%m/%Y %H:%M UTC")

    inf_jitter = int(np.isinf(b["jitter_relativo"]).sum())
    texto = f"""# Relatório da Tarefa 2 — baseline, rótulo e corte

Gerado por `src/baseline_e_rotulo.py` a partir de `data/raw/medicoes_brutas.csv.gz` (Tarefa 1), com os limiares de `config/rotulagem.json`.

## 1. Inspeção do bruto

| Item | Valor |
|---|---|
| Registros brutos | {n(len(bruto))} |
| Fluxos | {bruto['fluxo_id'].nunique()} |
| Duplicatas (fluxo_id, timestamp) | {int(bruto.duplicated(['fluxo_id', 'timestamp']).sum())} |
| RTT vazio | {n(bruto['latencia_ms'].isna().sum())} |
| RTT gravado como 0 | {int((bruto['latencia_ms'] == 0).sum())} |
| Fluxos com timestamp nos dois períodos ao mesmo tempo | 0 (o período é definido pelo instante: A vai até {fmt_data(cortes['inicio_B'])}, exclusivo) |
| Fluxos sem medição no Período A | {len(sem_a)} |

## 2. Baseline por fluxo (só Período A)

Fluxos com ficha: **{len(com_ficha)}**. Fluxos excluídos (menos de 1.500 RTT válidos no Período A): **{len(excluidos)}**.

{md(excluidos) if len(excluidos) else 'Nenhum fluxo ficou abaixo do piso.'}

Exemplo auditável: o fluxo mais curto e o mais longo. As duas medianas são o "normal" de cada fluxo.

{md(pd.concat([curto, longo])[colunas_ficha])}

## 3 e 4. Métricas do Período B e rótulo

Classes no Período B (só fluxos com ficha):

| OK | RISCO | FALHA | Total |
|---|---|---|---|
| {n(contagem['OK'])} ({pct(contagem['OK'] / contagem.sum())}) | {n(contagem['RISCO'])} ({pct(contagem['RISCO'] / contagem.sum())}) | {n(contagem['FALHA'])} ({pct(contagem['FALHA'] / contagem.sum())}) | {n(contagem.sum())} |

Linha da tabela que disparou cada classe (parar na primeira verdadeira):

{md(tabela_regras)}

Casos especiais: `jitter_relativo` infinito (jitter típico 0 e jitter atual > 0, tratado como ≥ 3) em {inf_jitter} medições.

Três exemplos reais (o primeiro OK de caminho longo, com RTT alto e `z_robusto` baixo; um RISCO; uma FALHA de caminho curto ou de timeout):

{md(exemplos)}

## 5. Corte temporal dentro do Período B

| Bloco | Início | Fim (exclusivo) |
|---|---|---|
| treino | {fmt_data(cortes['inicio_B'])} | {fmt_data(cortes['fim_treino'])} |
| validação | {fmt_data(cortes['fim_treino'])} | {fmt_data(cortes['fim_validacao'])} |
| teste | {fmt_data(cortes['fim_validacao'])} | {fmt_data(cortes['fim_B'])} |

Embargo: as 4 primeiras medições de cada fluxo na validação e no teste ficam de fora, porque as colunas `n5_*` delas olham medições do bloco anterior.

{md(blocos)}

Nenhuma medição do Período A está em nenhum bloco.
"""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(texto, encoding="utf-8")


# ---------------------------------------------------------------- principal

def main():
    parser = argparse.ArgumentParser(description="Tarefa 2: baseline, rótulo e corte temporal.")
    parser.add_argument("--entrada", type=Path, default=RAIZ / "data" / "raw" / "medicoes_brutas.csv.gz")
    parser.add_argument("--coleta", type=Path, default=RAIZ / "config" / "coleta.json")
    parser.add_argument("--config", type=Path, default=RAIZ / "config" / "rotulagem.json")
    parser.add_argument("--sobrescrever", action="store_true", help="refaz as saídas se já existirem")
    args = parser.parse_args()

    saidas = [PROCESSADO / "baseline_por_fluxo.csv", PROCESSADO / "dataset_rotulado_B.csv.gz",
              PROCESSADO / "corte_temporal.json"]
    existentes = [s for s in saidas if s.exists()]
    if existentes and not args.sobrescrever:
        raise SystemExit(f"Já existem: {', '.join(map(str, existentes))}. Use --sobrescrever para refazer.")

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    periodos = json.loads(args.coleta.read_text(encoding="utf-8"))["periodos"]
    inicio_b = pd.Timestamp(periodos["B"]["inicio_utc"])
    fim_b = pd.Timestamp(periodos["B"]["fim_utc"])

    bruto = pd.read_csv(args.entrada, parse_dates=["timestamp"])
    fichas, sem_a = construir_baseline(bruto, cfg["baseline"])

    com_ficha = fichas[fichas["situacao"] == "ok"]
    b = bruto[bruto["periodo"] == "B"]
    b = metricas_relativas(b, com_ficha, cfg["baseline"], cfg["regras"], cfg["janela_persistencia"])
    b = rotular(b, cfg["regras"])
    b, cortes = cortar(b, inicio_b, fim_b, cfg["corte"])

    PROCESSADO.mkdir(parents=True, exist_ok=True)
    fichas.to_csv(saidas[0], index=False)
    colunas = ["timestamp", "fluxo_id", "probe_id", "dst_addr", "destino_fqdn", "regiao", "pais_origem",
               "latencia_ms", "jitter_ms", "mediana",
               "z_robusto", "aumento_pct", "jitter_relativo", "perda_pct", "timeout_atual",
               "n5_timeout", "n5_aumento80", "n5_risco", "regra", "classe", "bloco"]
    saida_b = b[colunas].copy()
    saida_b["timestamp"] = saida_b["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    saida_b.to_csv(saidas[1], index=False, float_format="%.6g")

    resumo = {nome: data.strftime("%Y-%m-%dT%H:%M:%SZ") for nome, data in cortes.items()}
    resumo["embargo_medicoes"] = cfg["corte"]["embargo_medicoes"]
    resumo["n_por_bloco"] = {k: int(v) for k, v in b["bloco"].value_counts().items()}
    resumo["classes_por_bloco"] = {
        bloco: {k: int(v) for k, v in grupo["classe"].value_counts().items()} for bloco, grupo in b.groupby("bloco")}
    saidas[2].write_text(json.dumps(resumo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    escrever_relatorio(bruto, fichas, sem_a, b, cortes, RAIZ / "docs" / "relatorio_tarefa2.md")
    print(f"Fichas: {len(fichas)} ({len(com_ficha)} com baseline suficiente)")
    print(f"Período B rotulado: {len(b)} medições")
    print(b["classe"].value_counts().to_string())
    print(b["bloco"].value_counts().to_string())


if __name__ == "__main__":
    main()
