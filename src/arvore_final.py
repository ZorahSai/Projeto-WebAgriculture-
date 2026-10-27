"""Tarefa 5 — Árvore final e teste único.

Uso (na raiz do repositório):
    python src/arvore_final.py

Entra a árvore da Tarefa 4 (parâmetros lidos de results/tarefa4/metricas_validacao.json,
escolhidos só na validação) e o dataset rotulado da Tarefa 2. O bloco de teste é medido
uma única vez. Não há reescolha de hiperparâmetros olhando o teste.

Saídas em results/tarefa5/:
    metricas_teste.json   matriz, F1 por classe, F1 macro, fluxo não visto, casos
    arvore_final.txt      regras da árvore (export_text)
"""
import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import (
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)
from sklearn.tree import DecisionTreeClassifier, export_text

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "results" / "tarefa5"
PARAMETROS_T4 = RAIZ / "results" / "tarefa4" / "metricas_validacao.json"
BASELINE = RAIZ / "data" / "processed" / "baseline_por_fluxo.csv"
PISO_RTT_VALIDOS = 1500
CLASSES = ["OK", "RISCO", "FALHA"]
FLUXO_NAO_VISTO = "6420|23.237.111.10"


def carregar(caminho):
    return pd.read_csv(caminho, parse_dates=["timestamp"])


def ler_parametros():
    """Parâmetros, colunas e semente da Tarefa 4 (não reescolhidos nesta tarefa)."""
    dados = json.loads(PARAMETROS_T4.read_text(encoding="utf-8"))
    t4 = dados["tarefa4"]
    return {
        "criterion": t4["criterio"],
        "max_depth": t4["max_depth"],
        "min_samples_leaf": t4["min_samples_leaf"],
        "ccp_alpha": t4["ccp_alpha"],
        "random_state": dados["semente"],
    }, dados["colunas"]


def treinar_final(treino, colunas, parametros):
    arvore = DecisionTreeClassifier(**parametros)
    return arvore.fit(treino[colunas], treino["classe"])


def avaliar(arvore, dados, colunas, classes):
    reais = dados["classe"]
    previstos = arvore.predict(dados[colunas])
    precisao, recall, f1, suporte = precision_recall_fscore_support(
        reais, previstos, labels=classes, zero_division=0
    )
    return {
        "f1_macro": float(f1_score(reais, previstos, labels=classes, average="macro", zero_division=0)),
        "acuracia": float((reais.values == previstos).mean()),
        "por_classe": {
            c: {
                "precisao": float(precisao[i]),
                "recall": float(recall[i]),
                "f1": float(f1[i]),
                "suporte": int(suporte[i]),
            }
            for i, c in enumerate(classes)
        },
        "matriz": confusion_matrix(reais, previstos, labels=classes).tolist(),
    }, previstos


def fluxo_nao_visto(df, colunas, classes, parametros, fluxo_id):
    """Treina sem o fluxo e avalia só nas medições de teste desse fluxo.

    O fluxo só é avaliado se a ficha dele (Período A) tiver o piso de RTT válidos.
    """
    baseline = pd.read_csv(BASELINE)
    ficha = baseline[baseline["fluxo_id"] == fluxo_id]
    if ficha.empty:
        return {"fluxo_id": fluxo_id, "avaliado": False, "motivo": "sem ficha de baseline"}
    n_validos = int(ficha["n_rtt_validos_A"].iloc[0])
    if n_validos < PISO_RTT_VALIDOS:
        return {"fluxo_id": fluxo_id, "avaliado": False, "n_rtt_validos_A": n_validos,
                "motivo": f"abaixo do piso de {PISO_RTT_VALIDOS} RTT válidos"}

    treino = df[(df["bloco"] == "treino") & (df["fluxo_id"] != fluxo_id)]
    teste_fluxo = df[(df["bloco"] == "teste") & (df["fluxo_id"] == fluxo_id)]
    if len(teste_fluxo) == 0:
        return {"fluxo_id": fluxo_id, "avaliado": False, "motivo": "sem medições no teste"}

    arvore = treinar_final(treino, colunas, parametros)
    metricas, previstos = avaliar(arvore, teste_fluxo, colunas, classes)
    return {
        "fluxo_id": fluxo_id,
        "avaliado": True,
        "n_rtt_validos_A": n_validos,
        "mediana_A": float(ficha["mediana"].iloc[0]),
        "MAD_A": float(ficha["MAD"].iloc[0]),
        "fora_do_treino": bool((treino["fluxo_id"] != fluxo_id).all()),
        "n_teste": int(len(teste_fluxo)),
        "reais": teste_fluxo["classe"].value_counts().to_dict(),
        "previstos": pd.Series(previstos).value_counts().to_dict(),
        "metricas": metricas,
    }


def descrever(linha, previsto, colunas):
    caso = {
        "fluxo_id": linha["fluxo_id"],
        "timestamp": str(linha["timestamp"]),
        "mediana_ms": float(linha["mediana"]),
        "latencia_ms": None if pd.isna(linha["latencia_ms"]) else float(linha["latencia_ms"]),
        "classe_real": linha["classe"],
        "classe_prevista": previsto,
        "regra_rotulo": linha["regra"],
    }
    caso.update({c: float(linha[c]) for c in colunas})
    return caso


def escolher_casos(teste, previstos, colunas):
    """Acerto OK em caminho longo e em caminho curto (maior/menor mediana) e todos os erros."""
    teste = teste.assign(previsto=previstos)
    medianas = teste.groupby("fluxo_id")["mediana"].first()
    casos = {}
    for nome, fluxo in (("longo_ok", medianas.idxmax()), ("curto_ok", medianas.idxmin())):
        acertos = teste[(teste["fluxo_id"] == fluxo) & (teste["classe"] == "OK") & (teste["previsto"] == "OK")]
        linha = acertos.loc[acertos["z_robusto"].abs().idxmin()]
        casos[nome] = descrever(linha, linha["previsto"], colunas)
    erros = teste[teste["classe"] != teste["previsto"]]
    casos["erros"] = [descrever(l, l["previsto"], colunas) for _, l in erros.iterrows()]
    return casos


def main():
    entrada = RAIZ / "data" / "processed" / "dataset_rotulado_B.csv.gz"
    df = carregar(entrada)
    parametros, colunas = ler_parametros()

    treino = df[df["bloco"] == "treino"].copy()
    teste = df[df["bloco"] == "teste"].copy()

    print(f"Treino: {len(treino):,} | Teste: {len(teste):,}")
    print(f"Parâmetros (Tarefa 4): {parametros}")

    arvore = treinar_final(treino, colunas, parametros)
    metricas, previstos = avaliar(arvore, teste, colunas, CLASSES)

    print("\n=== Matriz de confusão (contagem) ===")
    print("        OK    RISCO   FALHA")
    for i, c in enumerate(CLASSES):
        print(f"{c:6s} {metricas['matriz'][i]}")

    print(f"\nF1 macro: {metricas['f1_macro']:.4f}")
    print("\nPor classe:")
    for c in CLASSES:
        m = metricas["por_classe"][c]
        print(f"  {c}: P={m['precisao']:.4f}  R={m['recall']:.4f}  F1={m['f1']:.4f}  n={m['suporte']}")

    casos = escolher_casos(teste, previstos, colunas)
    print(f"\nCaso longo: {casos['longo_ok']['fluxo_id']} {casos['longo_ok']['timestamp']}")
    print(f"Caso curto: {casos['curto_ok']['fluxo_id']} {casos['curto_ok']['timestamp']}")
    print(f"Erros: {len(casos['erros'])}")

    resultado_fluxo = fluxo_nao_visto(df, colunas, CLASSES, parametros, FLUXO_NAO_VISTO)
    print(f"\n=== Fluxo não visto: {FLUXO_NAO_VISTO} ===")
    if resultado_fluxo["avaliado"]:
        print(f"RTT válidos no Período A: {resultado_fluxo['n_rtt_validos_A']}")
        print(f"Medições no teste: {resultado_fluxo['n_teste']}")
        print(f"Acurácia: {resultado_fluxo['metricas']['acuracia']:.4f}")
    else:
        print(f"Não avaliado: {resultado_fluxo['motivo']}")

    SAIDA.mkdir(parents=True, exist_ok=True)
    (SAIDA / "arvore_final.txt").write_text(export_text(arvore, feature_names=colunas), encoding="utf-8")
    saida_json = SAIDA / "metricas_teste.json"
    saida_json.write_text(
        json.dumps(
            {
                "parametros": parametros,
                "colunas": colunas,
                "profundidade_real": int(arvore.get_depth()),
                "folhas": int(arvore.get_n_leaves()),
                "n_treino": int(len(treino)),
                "n_teste": int(len(teste)),
                "teste": metricas,
                "casos": casos,
                "fluxo_nao_visto": resultado_fluxo,
            },
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )
    print(f"\nResultados salvos em {saida_json}")


if __name__ == "__main__":
    main()
