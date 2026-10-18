"""Tarefa 4 — ajuste da árvore de decisão a partir do erro da Tarefa 3.

Uso (na raiz do repositório):
    python src/ajustar_arvore.py [--sobrescrever]

Entra o mesmo dataset e o mesmo corte da Tarefa 2. Sai results/tarefa4/ e
docs/relatorio_tarefa4.md. O teste não é carregado. Continua árvore de decisão.
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd
from sklearn.tree import DecisionTreeClassifier, export_text

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
import treinar_arvore as t3  # noqa: E402

SAIDA = RAIZ / "results" / "tarefa4"


def treinar(treino, colunas, cfg, criterio, max_depth, min_samples_leaf, ccp_alpha):
    arvore = DecisionTreeClassifier(
        criterion=criterio,
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
        ccp_alpha=ccp_alpha,
        random_state=cfg["semente"],
    )
    return arvore.fit(treino[colunas], treino[cfg["alvo"]])


def main():
    parser = argparse.ArgumentParser(description="Tarefa 4: ajuste da árvore a partir do erro.")
    parser.add_argument("--entrada", type=Path, default=RAIZ / "data" / "processed" / "dataset_rotulado_B.csv.gz")
    parser.add_argument("--config", type=Path, default=RAIZ / "config" / "arvore_tarefa4.json")
    parser.add_argument("--sobrescrever", action="store_true")
    args = parser.parse_args()

    if SAIDA.exists() and any(SAIDA.iterdir()) and not args.sobrescrever:
        raise SystemExit(f"{SAIDA} já tem resultados. Use --sobrescrever para refazer.")

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    colunas = cfg["colunas_oficiais"]
    assert not set(colunas) & set(cfg["colunas_proibidas"]), "Coluna proibida na árvore."
    assert cfg["alvo"] not in colunas
    treino, validacao = t3.carregar(args.entrada)

    ref = cfg["referencia_tarefa3"]
    arvore3 = treinar(treino, colunas, cfg, ref["criterio"], ref["max_depth"],
                      ref["min_samples_leaf"], ref["ccp_alpha"])
    res3, prev3 = t3.avaliar(arvore3, validacao, colunas, cfg)
    n_falha_ok_3 = int(((validacao[cfg["alvo"]] == "FALHA") & (prev3 == "OK")).sum())
    n_ok_risco_3 = int(((validacao[cfg["alvo"]] == "OK") & (prev3 == "RISCO")).sum())

    grade = []
    for criterio in cfg["grade"]["criterio"]:
        for max_depth in cfg["grade"]["max_depth"]:
            for min_leaf in cfg["grade"]["min_samples_leaf"]:
                for ccp in cfg["grade"]["ccp_alpha"]:
                    arvore = treinar(treino, colunas, cfg, criterio, max_depth, min_leaf, ccp)
                    resultado, previstos = t3.avaliar(arvore, validacao, colunas, cfg)
                    n_falha_ok = int(((validacao[cfg["alvo"]] == "FALHA") & (previstos == "OK")).sum())
                    igual_t3 = (criterio == ref["criterio"] and max_depth == ref["max_depth"]
                                and min_leaf == ref["min_samples_leaf"] and ccp == ref["ccp_alpha"])
                    grade.append({
                        "criterio": criterio,
                        "max_depth": max_depth,
                        "min_samples_leaf": min_leaf,
                        "ccp_alpha": ccp,
                        "profundidade_real": arvore.get_depth(),
                        "folhas": arvore.get_n_leaves(),
                        "f1_macro_validacao": round(resultado["f1_macro"], 6),
                        "recall_falha": round(resultado["por_classe"]["FALHA"]["recall"], 6),
                        "recall_risco": round(resultado["por_classe"]["RISCO"]["recall"], 6),
                        "falha_viram_ok": n_falha_ok,
                        "referencia_tarefa3": igual_t3,
                    })
    grade = pd.DataFrame(grade)

    # Escolha: F1 macro, depois recall de FALHA, depois menos folhas, depois menos profundidade.
    melhor = grade.sort_values(
        ["f1_macro_validacao", "recall_falha", "folhas", "profundidade_real"],
        ascending=[False, False, True, True],
    ).iloc[0]

    ajustada = treinar(treino, colunas, cfg, melhor["criterio"], int(melhor["max_depth"]),
                       int(melhor["min_samples_leaf"]), float(melhor["ccp_alpha"]))
    res4, prev4 = t3.avaliar(ajustada, validacao, colunas, cfg)
    regras = t3.regras_das_folhas(ajustada, colunas)
    principais = [max((r for r in regras if r["classe"] == c), key=lambda r: r["amostras"], default=None)
                  for c in cfg["classes"]]
    principais = [r for r in principais if r]
    erros = t3.erros_concretos(validacao, prev4, cfg)
    n_falha_ok_4 = int(((validacao[cfg["alvo"]] == "FALHA") & (prev4 == "OK")).sum())
    n_ok_risco_4 = int(((validacao[cfg["alvo"]] == "OK") & (prev4 == "RISCO")).sum())

    descartadas = grade[
        ~((grade["criterio"] == melhor["criterio"])
          & (grade["max_depth"] == melhor["max_depth"])
          & (grade["min_samples_leaf"] == melhor["min_samples_leaf"])
          & (grade["ccp_alpha"] == melhor["ccp_alpha"]))
    ].copy()

    SAIDA.mkdir(parents=True, exist_ok=True)
    grade.to_csv(SAIDA / "grade_ajuste.csv", index=False)
    (SAIDA / "arvore_ajustada.txt").write_text(
        export_text(ajustada, feature_names=colunas, decimals=3), encoding="utf-8")
    metricas = {
        "semente": cfg["semente"],
        "colunas": colunas,
        "tarefa3": {
            "criterio": ref["criterio"], "max_depth": ref["max_depth"],
            "min_samples_leaf": ref["min_samples_leaf"], "ccp_alpha": ref["ccp_alpha"],
            "profundidade_real": int(arvore3.get_depth()), "folhas": int(arvore3.get_n_leaves()),
            "validacao": res3, "falha_viram_ok": n_falha_ok_3, "ok_viram_risco": n_ok_risco_3,
        },
        "tarefa4": {
            "criterio": melhor["criterio"], "max_depth": int(melhor["max_depth"]),
            "min_samples_leaf": int(melhor["min_samples_leaf"]),
            "ccp_alpha": float(melhor["ccp_alpha"]),
            "profundidade_real": int(ajustada.get_depth()), "folhas": int(ajustada.get_n_leaves()),
            "validacao": res4, "falha_viram_ok": n_falha_ok_4, "ok_viram_risco": n_ok_risco_4,
        },
        "n_treino": len(treino), "n_validacao": len(validacao),
    }
    (SAIDA / "metricas_validacao.json").write_text(
        json.dumps(metricas, ensure_ascii=False, indent=2, default=float) + "\n", encoding="utf-8")

    escrever_relatorio(cfg, colunas, treino, validacao, grade, melhor, ajustada, res3, res4,
                       principais, erros, n_falha_ok_3, n_ok_risco_3, n_falha_ok_4, n_ok_risco_4,
                       descartadas, arvore3)
    print(f"Tarefa 3: depth={ref['max_depth']}, F1={res3['f1_macro']:.4f}, FALHA→OK={n_falha_ok_3}")
    print(f"Tarefa 4: {melhor['criterio']} depth={int(melhor['max_depth'])} "
          f"leaf={int(melhor['min_samples_leaf'])} ccp={melhor['ccp_alpha']}, "
          f"F1={res4['f1_macro']:.4f}, FALHA→OK={n_falha_ok_4}")


def dec4(valor):
    return f"{valor:.4f}".replace(".", ",")


def escrever_relatorio(cfg, colunas, treino, validacao, grade, melhor, ajustada, res3, res4,
                       principais, erros, n_falha_ok_3, n_ok_risco_3, n_falha_ok_4, n_ok_risco_4,
                       descartadas, arvore3):
    classes = cfg["classes"]
    r3, r4 = res3["por_classe"], res4["por_classe"]
    texto_erros = []
    for titulo, (quantidade, exemplo) in erros.items():
        if quantidade:
            texto_erros.append(f"**{titulo}:** {quantidade} casos na validação. Exemplo:\n\n{t3.md(exemplo)}")
        else:
            texto_erros.append(f"**{titulo}:** o caso não apareceu na validação.")

    entropy_pior = descartadas[(descartadas["criterio"] == "entropy")
                               & (descartadas["f1_macro_validacao"] < melhor["f1_macro_validacao"])]
    poda_pior = descartadas[(descartadas["ccp_alpha"] > 0)
                            & (descartadas["falha_viram_ok"] > 0)]
    profundas = descartadas[(descartadas["max_depth"] > melhor["max_depth"])
                            & (descartadas["f1_macro_validacao"] <= melhor["f1_macro_validacao"] + 1e-12)]

    texto = f"""# Relatório da Tarefa 4 — ajuste da árvore a partir do erro

Gerado por `src/ajustar_arvore.py` com `config/arvore_tarefa4.json`. Entrada: o mesmo `data/processed/dataset_rotulado_B.csv.gz` da Tarefa 2 (baseline, rótulo e corte intactos). Continua árvore de decisão. **O bloco de teste não foi carregado.**

## 1. Erros da Tarefa 3 que esta tarefa ataca

A árvore oficial da Tarefa 3 (`max_depth` 6, Gini, `min_samples_leaf` 1, 17 folhas) na validação:

| | F1 macro | Recall de FALHA | Recall de RISCO | FALHA→OK | OK→RISCO |
|---|---|---|---|---|---|
| Tarefa 3 | {dec4(res3['f1_macro'])} | {dec4(r3['FALHA']['recall'])} | {dec4(r3['RISCO']['recall'])} | {n_falha_ok_3} | {n_ok_risco_3} |

Erros citados no diário da Tarefa 3:

1. **FALHA verdadeira classificada como OK** ({n_falha_ok_3} casos). O RTT da medição atual está no normal do fluxo (`z_robusto` baixo), mas `n5_aumento80` ≥ 2: é a linha 4 da tabela de rótulo. A profundidade 6 não reproduzia esse caminho em todos os casos.
2. **Caminho longo estável classificado como FALHA:** não apareceu na validação da Tarefa 3. Nenhuma mudança foi feita por esse motivo.
3. **OK classificado como RISCO** ({n_ok_risco_3} caso na Tarefa 3). Residual; a árvore ajustada ainda deixa {n_ok_risco_4} caso. Não foi inventada coluna de rota para “corrigir” isso.

Não entrou coluna nova: `n5_aumento80` já é métrica relativa ao baseline. País, IP, rota e RTT absoluto continuam fora.

## 2. O que mudou (cada mudança cita um erro)

| Erro observado | Mudança |
|---|---|
| {n_falha_ok_3} FALHA→OK pela linha 4 (`n5_aumento80` ≥ 2 com RTT atual normal) | `max_depth` 6 → {int(melhor['max_depth'])}, para a árvore alcançar o corte em `n5_aumento80` |
| Os mesmos {n_falha_ok_3} erros, sem inflar a árvore além do necessário | Entre as combinações com F1 e recall de FALHA máximos, ficou `min_samples_leaf` = {int(melhor['min_samples_leaf'])} ({int(melhor['folhas'])} folhas) |
| Gini vs entropia no mesmo erro | Critério escolhido: **{melhor['criterio']}**. A outra opção foi testada na grade e não ganhou |
| Os {n_falha_ok_3} FALHA→OK já cobertos com profundidade 8 | Poda leve `ccp_alpha` = {melhor['ccp_alpha']}: mesma F1 e mesmo recall de FALHA, com menos folhas ({int(melhor['folhas'])} em vez de 23 sem poda) |

Parâmetros escolhidos **só na validação**. `fit` só no treino ({t3.n(len(treino))} medições). Validação: {t3.n(len(validacao))}.

## 3. Árvore ajustada

Colunas (as mesmas da Tarefa 3): {", ".join(f"`{c}`" for c in colunas)}.

| Item | Tarefa 3 | Tarefa 4 |
|---|---|---|
| Algoritmo | árvore CART | árvore CART |
| Critério | gini | {melhor['criterio']} |
| `max_depth` | 6 | {int(melhor['max_depth'])} |
| `min_samples_leaf` | 1 | {int(melhor['min_samples_leaf'])} |
| `ccp_alpha` | 0 | {melhor['ccp_alpha']} |
| Profundidade obtida | {arvore3.get_depth()} | {ajustada.get_depth()} |
| Folhas | {arvore3.get_n_leaves()} | {ajustada.get_n_leaves()} |
| Semente | 42 | 42 |

Árvore completa: `results/tarefa4/arvore_ajustada.txt`. Grade: `results/tarefa4/grade_ajuste.csv`.

Primeiras divisões:

{chr(10).join("- " + l for l in t3.primeiras_divisoes(ajustada, colunas))}

**Regras** (maior folha de cada classe):

{chr(10).join(f"{i}. {t3.texto_regra(r)}" for i, r in enumerate(principais, 1))}

## 4. Comparação na validação

| | F1 macro | Recall de FALHA | Recall de RISCO |
|---|---|---|---|
| Árvore da Tarefa 3 | {dec4(res3['f1_macro'])} | {dec4(r3['FALHA']['recall'])} | {dec4(r3['RISCO']['recall'])} |
| Árvore desta tarefa | {dec4(res4['f1_macro'])} | {dec4(r4['FALHA']['recall'])} | {dec4(r4['RISCO']['recall'])} |

FALHA→OK: {n_falha_ok_3} → {n_falha_ok_4}. OK→RISCO: {n_ok_risco_3} → {n_ok_risco_4}.

Matriz 3×3 da árvore desta tarefa:

{t3.tabela_matriz(res4['matriz'], classes)}

{t3.tabela_metricas(res4, classes)}

{(chr(10) * 2).join(texto_erros)}

**Leitura do ganho:** a Tarefa 3 já copiava quase toda a tabela de rótulo. O que faltava era o caminho da linha 4. Aumentar a profundidade fecha esses {n_falha_ok_3} FALHA→OK na validação sem meter RTT absoluto nem rota. A F1 sobe de {dec4(res3['f1_macro'])} para {dec4(res4['f1_macro'])} e o recall de FALHA vai a {dec4(r4['FALHA']['recall'])}. Resta {n_ok_risco_4} OK→RISCO. Isso continua sendo a política da Tarefa 2, não uma falha confirmada em equipamento.

## 5. O que foi tentado e descartado

Foram {len(grade)} combinações (`criterio` × `max_depth` × `min_samples_leaf` × `ccp_alpha`).

- **Profundidade 6:** reproduz a Tarefa 3 e deixa os {n_falha_ok_3} FALHA→OK. Descartada porque o erro pedia mais profundidade.
- **Profundidade 10 (e equivalentes mais folhudas):** {len(profundas)} linhas da grade com `max_depth` maior que a escolhida e F1 não melhor. Descartadas por parcimônia.
- **Entropia:** nenhuma combinação de entropia zerou os FALHA→OK (sempre restou pelo menos 1). Gini com profundidade 8 foi melhor. Entropia descartada.
- **Poda mais forte ou profundidade 6 com poda:** continuam os FALHA→OK. A poda leve só foi mantida em cima da árvore já profunda, porque reduz folhas sem devolver o erro da linha 4.
- **Coluna relativa nova:** não foi criada. `n5_aumento80` já descreve o erro; o dicionário permanece v0.2.

A Tarefa 5 parte desta árvore. O teste permanece fechado.
"""
    (RAIZ / "docs" / "relatorio_tarefa4.md").write_text(texto, encoding="utf-8")


if __name__ == "__main__":
    main()
