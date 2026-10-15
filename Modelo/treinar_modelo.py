"""Treina e avalia a árvore de decisão a partir de um CSV no formato do Contrato de Dados.

Uso:
    python treinar_modelo.py [csv] [--max-profundidade 4] [--min-amostras 5] [--semente 42] [--salvar modelo.json]

Sem o caminho do CSV, usa o dataset sintético (dataset_sintetico.csv). O CSV pode ter colunas
além do contrato (como o dataset real multidestino); só latencia_ms, perda_pacotes_pct,
jitter_ms e status_real são usadas. Valores vazios viram None (ver arvore_decisao.py).
"""
import argparse
import csv
import json
from pathlib import Path

import arvore_decisao as ad

CLASSES = ["OK", "RISCO", "FALHA"]


def ler_csv(caminho):
    registros = []
    with open(caminho, newline="", encoding="utf-8") as arquivo:
        for linha in csv.DictReader(arquivo):
            registro = {atributo: float(linha[atributo]) if linha[atributo] != "" else None
                        for atributo in ad.ATRIBUTOS}
            registro["status_real"] = linha["status_real"]
            registros.append(registro)
    return registros


def imprimir_distribuicao(titulo, rotulos):
    print(f"{titulo}: {len(rotulos)} registros")
    for classe in CLASSES:
        quantidade = rotulos.count(classe)
        print(f"  {classe:<6} {quantidade:>7} ({quantidade / len(rotulos):.1%})")


def imprimir_matriz(matriz):
    cabecalho = "real \\ previsto"
    print(f"{cabecalho:<16}" + "".join(f"{classe:>8}" for classe in CLASSES) + f"{'acerto':>9}")
    for real in CLASSES:
        linha = matriz[real]
        total = sum(linha.values())
        acerto = linha[real] / total if total else 0.0
        print(f"{real:<16}" + "".join(f"{linha[previsto]:>8}" for previsto in CLASSES) + f"{acerto:>9.1%}")


def main():
    parser = argparse.ArgumentParser(description="Treina a árvore de decisão e calcula a acurácia no teste.")
    parser.add_argument("csv", type=Path, nargs="?", default=Path(__file__).parent / "dataset_sintetico.csv")
    parser.add_argument("--max-profundidade", type=int, default=4)
    parser.add_argument("--min-amostras", type=int, default=5)
    parser.add_argument("--proporcao-treino", type=float, default=0.7)
    parser.add_argument("--semente", type=int, default=42)
    parser.add_argument("--salvar", type=Path, help="salva a árvore treinada em JSON (para o dashboard)")
    args = parser.parse_args()

    registros = ler_csv(args.csv)
    treino, teste = ad.dividir_treino_teste(registros, args.proporcao_treino, args.semente)
    rotulos_treino = [r["status_real"] for r in treino]
    rotulos_teste = [r["status_real"] for r in teste]

    print(f"Arquivo: {args.csv}\n")
    imprimir_distribuicao("Treino", rotulos_treino)
    imprimir_distribuicao("Teste", rotulos_teste)

    arvore = ad.construir(treino, rotulos_treino, max_profundidade=args.max_profundidade,
                          min_amostras=args.min_amostras)

    print(f"\nÁrvore (profundidade {ad.profundidade(arvore)}, {ad.contar_folhas(arvore)} folhas):")
    print("\n".join(ad.descrever(arvore)))

    previstos_treino = [ad.classificar(arvore, r) for r in treino]
    previstos_teste = [ad.classificar(arvore, r) for r in teste]
    classe_mais_comum = ad.classe_majoritaria(ad.contar(rotulos_treino))
    referencia = rotulos_teste.count(classe_mais_comum) / len(rotulos_teste)

    print(f"\nAcurácia no treino: {ad.acuracia(rotulos_treino, previstos_treino):.2%}")
    print(f"Acurácia no teste:  {ad.acuracia(rotulos_teste, previstos_teste):.2%}")
    print(f"Referência (sempre prever {classe_mais_comum}): {referencia:.2%}")
    print("\nMatriz de confusão (teste):")
    imprimir_matriz(ad.matriz_confusao(rotulos_teste, previstos_teste, CLASSES))

    if args.salvar:
        if args.salvar.exists():
            raise SystemExit(f"{args.salvar} já existe. Apague o arquivo ou escolha outro nome.")
        args.salvar.write_text(json.dumps(ad.para_dict(arvore), ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nÁrvore salva em {args.salvar}")


if __name__ == "__main__":
    main()
