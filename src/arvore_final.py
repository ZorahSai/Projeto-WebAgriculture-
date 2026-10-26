"""Tarefa 5 — Árvore final e teste único.

Uso (na raiz do repositório):
    python src/avaliar_arvore.py

Entra a árvore da Tarefa 4 (parâmetros fixos, escolhidos só na validação)
e o dataset rotulado da Tarefa 2. O bloco de teste é medido uma única vez.
Não há reescolha de hiperparâmetros olhando o teste.
"""
import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import (
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)
from sklearn.tree import DecisionTreeClassifier

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "results" / "tarefa5"


def carregar(caminho):
    return pd.read_csv(caminho, parse_dates=["timestamp"])


def treinar_final(treino, colunas, semente=42):
    """Árvore com os parâmetros da Tarefa 4 (não reescolhidos nesta tarefa)."""
    arvore = DecisionTreeClassifier(
        criterion="gini",
        max_depth=8,
        min_samples_leaf=10,
        ccp_alpha=0.0001,
        random_state=semente,
    )
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


def fluxo_nao_visto(df, colunas, classes, fluxo_id):
    """Treina sem o fluxo e avalia só nas medições de teste desse fluxo."""
    treino = df[(df["bloco"] == "treino") & (df["fluxo_id"] != fluxo_id)]
    teste_fluxo = df[(df["bloco"] == "teste") & (df["fluxo_id"] == fluxo_id)]
    if len(teste_fluxo) == 0:
        return None

    arvore = treinar_final(treino, colunas)
    metricas, _ = avaliar(arvore, teste_fluxo, colunas, classes)
    return {
        "fluxo_id": fluxo_id,
        "n_teste": int(len(teste_fluxo)),
        "metricas": metricas,
    }


def main():
    entrada = RAIZ / "data" / "processed" / "dataset_rotulado_B.csv.gz"
    df = carregar(entrada)

    colunas = [
        "z_robusto",
        "aumento_pct",
        "jitter_relativo",
        "perda_pct",
        "timeout_atual",
        "n5_timeout",
        "n5_aumento80",
        "n5_risco",
    ]
    classes = ["OK", "RISCO", "FALHA"]

    treino = df[df["bloco"] == "treino"].copy()
    teste = df[df["bloco"] == "teste"].copy()

    print(f"Treino: {len(treino):,} | Teste: {len(teste):,}")

    arvore = treinar_final(treino, colunas)
    metricas, _ = avaliar(arvore, teste, colunas, classes)

    print("\n=== Matriz de confusão (contagem) ===")
    print("        OK    RISCO   FALHA")
    for i, c in enumerate(classes):
        print(f"{c:6s} {metricas['matriz'][i]}")

    print(f"\nF1 macro: {metricas['f1_macro']:.4f}")
    print("\nPor classe:")
    for c in classes:
        m = metricas["por_classe"][c]
        print(f"  {c}: P={m['precisao']:.4f}  R={m['recall']:.4f}  F1={m['f1']:.4f}  n={m['suporte']}")

    # Fluxo não visto (exemplo usado no diário)
    fluxo_exemplo = "6420|23.237.111.10"
    resultado_fluxo = fluxo_nao_visto(df, colunas, classes, fluxo_exemplo)
    if resultado_fluxo:
        print(f"\n=== Fluxo não visto: {fluxo_exemplo} ===")
        print(f"Medições no teste: {resultado_fluxo['n_teste']}")
        print(f"F1 macro: {resultado_fluxo['metricas']['f1_macro']:.4f}")

    # Salva resultados
    SAIDA.mkdir(parents=True, exist_ok=True)
    saida_json = SAIDA / "metricas_teste.json"
    saida_json.write_text(
        json.dumps(
            {
                "teste": metricas,
                "fluxo_nao_visto": resultado_fluxo,
                "parametros": {
                    "criterion": "gini",
                    "max_depth": 8,
                    "min_samples_leaf": 10,
                    "ccp_alpha": 0.0001,
                    "random_state": 42,
                    "colunas": colunas,
                },
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"\nResultados salvos em {saida_json}")


if __name__ == "__main__":
    main()
