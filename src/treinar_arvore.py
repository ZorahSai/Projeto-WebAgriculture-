"""Tarefa 3 — primeira árvore de decisão e árvore de contraste.

Uso (na raiz do repositório):
    python src/treinar_arvore.py [--sobrescrever]

Entrada: data/processed/dataset_rotulado_B.csv.gz (Tarefa 2: mesmo rótulo e mesmo corte) e config/arvore.json.
Saídas em results/tarefa3/ e o relatório docs/relatorio_tarefa3.md.

Regras seguidas:
- Árvore de decisão CART (scikit-learn), critério declarado no config.
- A árvore oficial só vê métricas relativas ao baseline do fluxo.
- fit só no treino; max_depth e min_samples_leaf escolhidos pela F1 macro da validação.
- O bloco de teste não é carregado: fica fechado até a Tarefa 5.
- A árvore de contraste (com RTT absoluto) só mostra o atalho da distância e não é o modelo.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, f1_score, precision_recall_fscore_support
from sklearn.tree import DecisionTreeClassifier, export_text

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "results" / "tarefa3"
PODE_SER_VAZIO = {"z_robusto", "aumento_pct", "jitter_relativo", "latencia_ms", "jitter_ms"}


def n(valor):
    return f"{int(valor):,}".replace(",", ".")


def dec(valor):
    return f"{valor:.3f}".replace(".", ",")


def fluxos_longos(dados):
    """Medições de fluxos no quartil de maior mediana do baseline (caminhos longos)."""
    medianas = dados.groupby("fluxo_id")["mediana"].first()
    return dados["fluxo_id"].isin(medianas[medianas >= medianas.quantile(0.75)].index)


def fluxos_curtos(dados):
    medianas = dados.groupby("fluxo_id")["mediana"].first()
    return dados["fluxo_id"].isin(medianas[medianas <= medianas.quantile(0.25)].index)


def carregar(caminho):
    df = pd.read_csv(caminho, parse_dates=["timestamp"])
    df = df[df["bloco"].isin(["treino", "validacao"])].copy()  # o teste não entra nesta tarefa
    assert not (df["bloco"] == "teste").any()
    return df[df["bloco"] == "treino"], df[df["bloco"] == "validacao"]


def treinar(treino, colunas, cfg, max_depth, min_samples_leaf):
    arvore = DecisionTreeClassifier(criterion=cfg["criterio"], max_depth=max_depth,
                                    min_samples_leaf=min_samples_leaf, random_state=cfg["semente"])
    return arvore.fit(treino[colunas], treino[cfg["alvo"]])


def avaliar(arvore, dados, colunas, cfg):
    reais = dados[cfg["alvo"]]
    previstos = arvore.predict(dados[colunas])
    classes = cfg["classes"]
    precisao, recall, f1, suporte = precision_recall_fscore_support(reais, previstos, labels=classes, zero_division=0)
    return {
        "f1_macro": f1_score(reais, previstos, labels=classes, average="macro", zero_division=0),
        "acuracia": float((reais.values == previstos).mean()),
        "por_classe": {c: {"precisao": precisao[i], "recall": recall[i], "f1": f1[i], "suporte": int(suporte[i])}
                       for i, c in enumerate(classes)},
        "matriz": confusion_matrix(reais, previstos, labels=classes).tolist(),
    }, previstos


def regras_das_folhas(arvore, colunas):
    """Uma regra por folha: caminho da raiz até a folha, em português."""
    t = arvore.tree_
    classes = arvore.classes_
    regras = []

    def descer(no, condicoes):
        if t.children_left[no] == -1:
            contagem = t.value[no][0] * t.n_node_samples[no]  # value guarda frações por classe
            classe = classes[int(np.argmax(contagem))]
            regras.append({"condicoes": condicoes, "classe": classe, "amostras": int(t.n_node_samples[no]),
                           "pureza": float(contagem.max() / contagem.sum())})
            return
        nome = colunas[t.feature[no]]
        limiar = t.threshold[no]
        vazio_esq = bool(t.missing_go_to_left[no]) if nome in PODE_SER_VAZIO else None
        esq = f"{nome} ≤ {limiar:.3g}" + (" (ou vazio)" if vazio_esq is True else "")
        dir_ = f"{nome} > {limiar:.3g}" + (" (ou vazio)" if vazio_esq is False else "")
        descer(t.children_left[no], condicoes + [esq])
        descer(t.children_right[no], condicoes + [dir_])

    descer(0, [])
    return regras


def texto_regra(regra):
    return f"se {' e '.join(regra['condicoes'])}, então **{regra['classe']}** " \
           f"({n(regra['amostras'])} amostras do treino, {regra['pureza']:.0%} dessa classe)"


def primeiras_divisoes(arvore, colunas, niveis=2):
    t = arvore.tree_
    linhas = []

    def descer(no, nivel, prefixo):
        if nivel > niveis or t.children_left[no] == -1:
            return
        linhas.append(f"{prefixo}`{colunas[t.feature[no]]} ≤ {t.threshold[no]:.3g}` ({n(t.n_node_samples[no])} amostras)")
        descer(t.children_left[no], nivel + 1, prefixo + "  sim → ")
        descer(t.children_right[no], nivel + 1, prefixo + "  não → ")

    descer(0, 1, "")
    return linhas


def primeiro_corte(arvore, colunas, colunas_ms):
    """Primeira divisão (em largura, da raiz para baixo) que usa uma coluna em milissegundos."""
    t = arvore.tree_
    fila = [(0, 1)]
    while fila:
        no, nivel = fila.pop(0)
        if t.children_left[no] == -1:
            continue
        if colunas[t.feature[no]] in colunas_ms:
            return {"divisao": f"{colunas[t.feature[no]]} ≤ {t.threshold[no]:.3g}", "nivel": nivel}
        fila += [(t.children_left[no], nivel + 1), (t.children_right[no], nivel + 1)]
    return None


def tabela_metricas(resultado, classes):
    linhas = ["| Classe | Precisão | Recall | F1 | Suporte |", "|---|---|---|---|---|"]
    for c in classes:
        m = resultado["por_classe"][c]
        linhas.append(f"| {c} | {dec(m['precisao'])} | {dec(m['recall'])} | {dec(m['f1'])} | {n(m['suporte'])} |")
    linhas.append(f"| **F1 macro** | | | **{dec(resultado['f1_macro'])}** | |")
    return "\n".join(linhas)


def tabela_matriz(matriz, classes):
    linhas = ["| real \\ previsto | " + " | ".join(classes) + " |", "|---|" + "---|" * len(classes)]
    for c, linha in zip(classes, matriz):
        linhas.append(f"| **{c}** | " + " | ".join(n(v) for v in linha) + " |")
    return "\n".join(linhas)


def erros_concretos(validacao, previstos, cfg):
    v = validacao.assign(previsto=previstos)
    colunas = ["timestamp", "fluxo_id", "mediana", "latencia_ms", "z_robusto", "aumento_pct", "jitter_relativo",
               "perda_pct", "n5_timeout", "n5_aumento80", "n5_risco", "classe", "previsto"]
    longo_falha = v[fluxos_longos(v) & (v["classe"] == "OK") & (v["previsto"] == "FALHA")]
    curto_ok = v[fluxos_curtos(v) & (v["classe"] == "FALHA") & (v["previsto"] == "OK")]
    casos = {
        "Caminho longo estável (OK) que a árvore marcou como FALHA": longo_falha,
        "FALHA de caminho curto que a árvore marcou como OK": curto_ok,
    }
    return {titulo: (len(df), df[colunas].head(1)) for titulo, df in casos.items()}


def md(df, casas=2):
    def fmt(v):
        if isinstance(v, pd.Timestamp):
            return v.strftime("%d/%m %H:%M:%S")
        if isinstance(v, (float, np.floating)):
            return "" if pd.isna(v) else f"{v:.{casas}f}".replace(".", ",")
        return str(v).replace("|", "\\|")
    linhas = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    linhas += ["| " + " | ".join(fmt(v) for v in linha) + " |" for linha in df.itertuples(index=False)]
    return "\n".join(linhas)


def main():
    parser = argparse.ArgumentParser(description="Tarefa 3: primeira árvore de decisão.")
    parser.add_argument("--entrada", type=Path, default=RAIZ / "data" / "processed" / "dataset_rotulado_B.csv.gz")
    parser.add_argument("--config", type=Path, default=RAIZ / "config" / "arvore.json")
    parser.add_argument("--sobrescrever", action="store_true")
    args = parser.parse_args()

    if SAIDA.exists() and any(SAIDA.iterdir()) and not args.sobrescrever:
        raise SystemExit(f"{SAIDA} já tem resultados. Use --sobrescrever para refazer.")

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    colunas = cfg["colunas_oficiais"]
    assert not set(colunas) & set(cfg["colunas_proibidas"]), "Coluna proibida na árvore oficial."
    assert cfg["alvo"] not in colunas, "A classe é o alvo, não uma coluna de entrada."
    treino, validacao = carregar(args.entrada)

    # 1. Grade de hiperparâmetros avaliada só na validação
    grade = []
    for max_depth in cfg["grade"]["max_depth"]:
        for min_leaf in cfg["grade"]["min_samples_leaf"]:
            arvore = treinar(treino, colunas, cfg, max_depth, min_leaf)
            resultado, _ = avaliar(arvore, validacao, colunas, cfg)
            grade.append({"max_depth": max_depth, "min_samples_leaf": min_leaf,
                          "profundidade_real": arvore.get_depth(), "folhas": arvore.get_n_leaves(),
                          "f1_macro_validacao": round(resultado["f1_macro"], 4),
                          "recall_falha_validacao": round(resultado["por_classe"]["FALHA"]["recall"], 4),
                          "recall_risco_validacao": round(resultado["por_classe"]["RISCO"]["recall"], 4)})
    grade = pd.DataFrame(grade)
    # Parcimônia: entre as combinações a até `tolerancia_f1` da melhor F1 macro, fica a de menos folhas
    proximas = grade[grade["f1_macro_validacao"] >= grade["f1_macro_validacao"].max() - cfg["tolerancia_f1"]]
    melhor = proximas.sort_values(["folhas", "profundidade_real", "f1_macro_validacao"],
                                  ascending=[True, True, False]).iloc[0]

    # 2. Árvore oficial com os parâmetros escolhidos
    oficial = treinar(treino, colunas, cfg, int(melhor["max_depth"]), int(melhor["min_samples_leaf"]))
    res_oficial, previstos = avaliar(oficial, validacao, colunas, cfg)
    regras = regras_das_folhas(oficial, colunas)
    principais = [max((r for r in regras if r["classe"] == c), key=lambda r: r["amostras"], default=None)
                  for c in cfg["classes"]]
    principais = [r for r in principais if r]

    # Referência: sempre a classe mais comum do treino
    majoritaria = treino[cfg["alvo"]].mode()[0]
    f1_majoritaria = f1_score(validacao[cfg["alvo"]], [majoritaria] * len(validacao),
                              labels=cfg["classes"], average="macro", zero_division=0)

    # 3. Árvores de contraste (não são o modelo)
    contrastes = {}
    for nome, cols in {
        "relativas + RTT absoluto": colunas + cfg["colunas_contraste_extra"],
        "só medidas absolutas": cfg["colunas_contraste_so_absolutas"],
    }.items():
        arvore = treinar(treino, cols, cfg, int(melhor["max_depth"]), int(melhor["min_samples_leaf"]))
        resultado, prev = avaliar(arvore, validacao, cols, cfg)
        importancias = pd.Series(arvore.feature_importances_, index=cols).sort_values(ascending=False)
        ok_longo = fluxos_longos(validacao) & (validacao["classe"] == "OK")
        contrastes[nome] = {
            "raiz": f"{cols[arvore.tree_.feature[0]]} ≤ {arvore.tree_.threshold[0]:.3g}",
            "primeiras": primeiras_divisoes(arvore, cols),
            "f1_macro_validacao": resultado["f1_macro"],
            "importancias": importancias[importancias > 0].round(3).to_dict(),
            "ok_longo_virou_falha": float((prev[ok_longo.values] == "FALHA").mean()) if ok_longo.any() else None,
            "primeiro_corte_em_ms": primeiro_corte(arvore, cols, cfg["colunas_contraste_extra"]),
        }
    ok_longo = fluxos_longos(validacao) & (validacao["classe"] == "OK")
    oficial_ok_longo_falha = float((previstos[ok_longo.values] == "FALHA").mean()) if ok_longo.any() else None

    # 4. Gravação
    SAIDA.mkdir(parents=True, exist_ok=True)
    grade.to_csv(SAIDA / "grade_validacao.csv", index=False)
    (SAIDA / "arvore_oficial.txt").write_text(export_text(oficial, feature_names=colunas, decimals=3), encoding="utf-8")
    metricas = {
        "criterio": cfg["criterio"], "semente": cfg["semente"], "colunas": colunas,
        "max_depth": int(melhor["max_depth"]), "min_samples_leaf": int(melhor["min_samples_leaf"]),
        "profundidade_real": int(oficial.get_depth()), "folhas": int(oficial.get_n_leaves()),
        "n_treino": len(treino), "n_validacao": len(validacao),
        "validacao": res_oficial, "f1_macro_classe_majoritaria": f1_majoritaria,
        "contrastes": contrastes,
    }
    (SAIDA / "metricas_validacao.json").write_text(
        json.dumps(metricas, ensure_ascii=False, indent=2, default=float) + "\n", encoding="utf-8")

    erros = erros_concretos(validacao, previstos, cfg)
    escrever_relatorio(cfg, colunas, treino, validacao, grade, melhor, oficial, res_oficial, regras, principais,
                       f1_majoritaria, majoritaria, contrastes, oficial_ok_longo_falha, erros)
    print(f"Árvore oficial: max_depth={int(melhor['max_depth'])}, min_samples_leaf={int(melhor['min_samples_leaf'])}, "
          f"profundidade {oficial.get_depth()}, {oficial.get_n_leaves()} folhas")
    print(f"F1 macro na validação: {res_oficial['f1_macro']:.3f} (classe majoritária: {f1_majoritaria:.3f})")
    for nome, c in contrastes.items():
        print(f"Contraste '{nome}': raiz {c['raiz']}, F1 macro {c['f1_macro_validacao']:.3f}")


def frase_contraste(c, f1_oficial):
    corte = c["primeiro_corte_em_ms"]
    queda = f"F1 macro {dec(c['f1_macro_validacao'])}, contra {dec(f1_oficial)} da árvore oficial"
    if corte is None:
        return (f"com as métricas relativas disponíveis, a árvore não usou nenhuma coluna em milissegundos ({queda}). "
                "O RTT absoluto não acrescenta nada quando o desvio em relação ao baseline já está presente.")
    return (f"sem o desvio em relação ao baseline, a árvore passa a cortar em milissegundos fixos "
            f"(`{corte['divisao']}`, no nível {corte['nivel']}), ou seja, aprende o comprimento do caminho "
            f"em vez da degradação de cada fluxo ({queda}).")


def escrever_relatorio(cfg, colunas, treino, validacao, grade, melhor, oficial, res, regras, principais,
                       f1_majoritaria, majoritaria, contrastes, oficial_ok_longo_falha, erros):
    classes = cfg["classes"]
    fmt_pct = lambda v: "—" if v is None else f"{v:.1%}".replace(".", ",")
    grade_top = grade.sort_values("f1_macro_validacao", ascending=False).head(8)
    texto_erros = []
    for titulo, (quantidade, exemplo) in erros.items():
        if quantidade:
            texto_erros.append(f"**{titulo}:** {quantidade} casos na validação. Exemplo:\n\n{md(exemplo)}")
        else:
            texto_erros.append(f"**{titulo}:** o caso não apareceu na validação.")
    texto_contraste = []
    for nome, c in contrastes.items():
        imp = ", ".join(f"`{k}` {v:.2f}".replace(".", ",") for k, v in c["importancias"].items())
        texto_contraste.append(
            f"### Contraste: {nome}\n\n"
            f"- **Divisão na raiz:** `{c['raiz']}`\n"
            f"- **Primeiras divisões:**\n" + "\n".join(f"  - {l}" for l in c["primeiras"]) + "\n"
            f"- **Importância dos atributos:** {imp}\n"
            f"- **F1 macro na validação:** {c['f1_macro_validacao']:.3f}".replace(".", ",") + "\n"
            f"- **Medições OK de caminho longo marcadas como FALHA:** {fmt_pct(c['ok_longo_virou_falha'])}\n"
            f"- **O que ela aprendeu:** {frase_contraste(c, res['f1_macro'])}"
        )

    texto = f"""# Relatório da Tarefa 3 — primeira árvore de decisão

Gerado por `src/treinar_arvore.py` com `config/arvore.json`. Entrada: `data/processed/dataset_rotulado_B.csv.gz` da Tarefa 2 (mesmo baseline, mesmo rótulo, mesmo corte). A ficha de baseline não foi recalculada.

## 1. Colunas da árvore oficial

{", ".join(f"`{c}`" for c in colunas)}

O alvo é `classe` (OK, RISCO, FALHA), que não é coluna de entrada. Ficam de fora: {", ".join(f"`{c}`" for c in cfg["colunas_proibidas"])}.

Treino: {n(len(treino))} medições. Validação: {n(len(validacao))} medições. **O bloco de teste não foi carregado.**

## 2. A árvore

| Item | Valor |
|---|---|
| Algoritmo | Árvore de decisão CART (`DecisionTreeClassifier`, scikit-learn) |
| Critério | {cfg["criterio"]} |
| `max_depth` escolhido | {int(melhor["max_depth"])} |
| `min_samples_leaf` escolhido | {int(melhor["min_samples_leaf"])} |
| Profundidade obtida | {oficial.get_depth()} |
| Folhas | {oficial.get_n_leaves()} |
| Semente | {cfg["semente"]} |
| Ajuste (`fit`) | só no treino |

Como os parâmetros foram escolhidos: {len(grade)} combinações de `max_depth` × `min_samples_leaf`, treinadas no treino e comparadas pela F1 macro **na validação**. Entre as que ficaram a até {dec(cfg["tolerancia_f1"])} da melhor F1 macro, ficou a árvore com menos folhas, que é a mais fácil de ler. As 8 melhores:

{md(grade_top, casas=4)}

Primeiras divisões:

{chr(10).join("- " + l for l in primeiras_divisoes(oficial, colunas))}

Regras lidas da árvore (a folha com mais amostras de cada classe). A árvore completa está em `results/tarefa3/arvore_oficial.txt`.

{chr(10).join(f"{i}. {texto_regra(r)}" for i, r in enumerate(principais, 1))}

## 3. Leitura do erro (validação)

Matriz 3×3 (contagem):

{tabela_matriz(res["matriz"], classes)}

{tabela_metricas(res, classes)}

Referência: prever sempre `{majoritaria}` dá F1 macro **{dec(f1_majoritaria)}** e acurácia {fmt_pct(res["por_classe"][majoritaria]["suporte"] / len(validacao))}. A acurácia da árvore é {fmt_pct(res["acuracia"])}, mas ela não decide nada aqui: com maioria OK, ela fica alta mesmo errando FALHA.

**Por que a F1 macro fica tão alta:** o rótulo da Tarefa 2 é uma regra fixa calculada com estas mesmas 8 colunas. A árvore reaprende essa política: seus cortes caem sobre os limiares da tabela de rótulo (`z_robusto` 2 e 3,5, perda de 10%, `n5_*`). Isso mostra que ela segue o critério relativo, e não a distância. Mas ela aprende a política de rotulagem, não uma falha confirmada de equipamento.

Medições OK de caminho longo (quartil de maior mediana) que a árvore oficial marcou como FALHA: {fmt_pct(oficial_ok_longo_falha)}.

{(chr(10) * 2).join(texto_erros)}

## 4. Árvore de contraste (não é o modelo)

Treinadas no mesmo treino e com os mesmos parâmetros, só para mostrar o atalho da distância. **Ficam fora da entrega final.**

{(chr(10) * 2).join(texto_contraste)}
"""
    (RAIZ / "docs" / "relatorio_tarefa3.md").write_text(texto, encoding="utf-8")


if __name__ == "__main__":
    main()
