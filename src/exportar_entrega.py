"""Pacote de entrega — modelo, metadados, baseline e carregador.

Uso (na raiz do repositório):
    python src/exportar_entrega.py

Treina a árvore final como na Tarefa 5 (mesmos parâmetros e mesmo bloco de treino)
e grava em entrega/:
    modelo.joblib        dict {modelo, features, familia, params}
    metadados.json       entradas, fórmulas, faltantes, saídas, horizonte, versões, exemplo
    baseline.csv         ficha por fluxo do Período A com flag de validade
    carregar_modelo.py   exemplo de carga e previsão
    <grupo>.zip          os quatro arquivos acima
"""
import json
import platform
import sys
import zipfile
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contrato_entrega import completar_metadados

from arvore_final import (  # noqa: E402
    BASELINE, CLASSES, PISO_RTT_VALIDOS, RAIZ, carregar, ler_parametros, treinar_final,
)

SAIDA = RAIZ / "entrega"
NOME_ZIP = "WebAgriculture.zip"

FORMULAS = {
    "z_robusto": "(latencia_ms - mediana_A) / (1.4826 * MAD_A); NaN quando não há RTT",
    "aumento_pct": "(latencia_ms - mediana_A) / mediana_A * 100",
    "jitter_relativo": "jitter_ms / jitter típico do fluxo no Período A; inf quando o típico é 0 (tratado como >= 3)",
    "perda_pct": "pacotes perdidos / pacotes enviados * 100 na medição",
    "timeout_atual": "1 se a medição não tem RTT ou a perda é 100%, senão 0",
    "n5_timeout": "soma de timeout_atual nas últimas 5 medições do fluxo (inclui a atual)",
    "n5_aumento80": "quantas das últimas 5 medições do fluxo tiveram aumento_pct >= 80",
    "n5_risco": "quantas das últimas 5 medições do fluxo foram rotuladas RISCO",
}

CARREGADOR = '''"""Carga validada e exemplo de inferência. Execute no ambiente de requirements.txt.

Somente carregar artefatos joblib de origem confiável: o formato executa código.
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent


def carregar():
    pacote = joblib.load(AQUI / "modelo.joblib")
    meta = json.loads((AQUI / "metadados.json").read_text(encoding="utf-8"))
    obrigatorias = {"modelo", "features", "familia", "params"}
    if not obrigatorias.issubset(pacote):
        raise ValueError("Pacote sem as quatro chaves obrigatórias")
    features = pacote["features"]
    descritas = [e["nome"] for e in sorted(meta["entradas"], key=lambda e: e["ordem"])]
    if features != descritas or list(pacote["modelo"].feature_names_in_) != features:
        raise ValueError("Ordem das features incompatível entre pacote, modelo e metadados")
    if list(pacote["modelo"].classes_) != meta["saidas"]["ordem_classes"]:
        raise ValueError("Ordem de classes incompatível")
    return pacote, meta


def prever(entrada, pacote):
    features = pacote["features"]
    if set(entrada) != set(features):
        raise ValueError("Informe exatamente as oito features do contrato")
    try:
        quadro = pd.DataFrame([entrada], columns=features).astype(float)
    except (ValueError, TypeError) as exc:
        raise ValueError("Todas as features devem ser numéricas") from exc
    if not np.isfinite(quadro.to_numpy()).all():
        raise ValueError("Medição sem classificação: contém NaN ou infinito; não imputar silenciosamente")
    return str(pacote["modelo"].predict(quadro)[0])


def main():
    pacote, meta = carregar()
    previsto = prever(meta["exemplo_real"]["entrada"], pacote)
    esperado = meta["exemplo_real"]["classe_prevista"]
    print("Modelo:", meta["nome_modelo"], meta["versao_modelo"])
    print("Classes:", list(pacote["modelo"].classes_))
    print("Previsto:", previsto, "| referência:", esperado)
    if previsto != esperado:
        raise SystemExit("A previsão difere da referência registrada")


if __name__ == "__main__":
    main()
'''


def json_seguro(valor):
    if isinstance(valor, float) and not np.isfinite(valor):
        return None if np.isnan(valor) else ("inf" if valor > 0 else "-inf")
    return valor


def main():
    df = carregar(RAIZ / "data" / "processed" / "dataset_rotulado_B.csv.gz")
    parametros, colunas = ler_parametros()
    treino = df[df["bloco"] == "treino"]
    teste = df[df["bloco"] == "teste"]
    modelo = treinar_final(treino, colunas, parametros)

    SAIDA.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {"modelo": modelo, "features": colunas, "familia": "DecisionTreeClassifier", "params": parametros},
        SAIDA / "modelo.joblib",
    )

    linha = teste[np.isfinite(teste[colunas]).all(axis=1)].iloc[0]
    entrada = {c: json_seguro(float(linha[c])) for c in colunas}
    previsto = modelo.predict(linha[colunas].to_frame().T.astype(float))[0]

    baseline = pd.read_csv(BASELINE)
    baseline["periodo"] = "A"
    baseline["valido"] = baseline["n_rtt_validos_A"] >= PISO_RTT_VALIDOS
    baseline["recomendacao"] = np.where(
        baseline["valido"], "usar", f"não usar: abaixo de {PISO_RTT_VALIDOS} RTT válidos no Período A"
    )
    baseline.to_csv(SAIDA / "baseline.csv", index=False)

    metadados = {
        "projeto": "WebAgriculture",
        "familia": "DecisionTreeClassifier (scikit-learn, CART)",
        "params": parametros,
        "entradas": [{"nome": c, "tipo": "float", "ordem": i, "formula": FORMULAS.get(c, "")}
                     for i, c in enumerate(colunas)],
        "faltantes_e_divisao_por_zero": {
            "sem_rtt": "z_robusto e aumento_pct ficam NaN; timeout_atual = 1",
            "jitter_tipico_zero": "jitter_relativo = inf (tratado como >= 3)",
            "observacao": "o modelo não imputa: preencha NaN antes de prever ou descarte a linha",
        },
        "saidas": {"alvo": "classe", "ordem_classes": [str(c) for c in modelo.classes_],
                   "classes_do_projeto": CLASSES},
        "horizonte": "classifica a medição atual de cada fluxo (sem previsão futura)",
        "historico_necessario": "últimas 5 medições do mesmo fluxo para as colunas n5_*; "
                                "as 4 primeiras medições de cada fluxo em validação e teste ficam em embargo",
        "regras_baseline": {
            "periodo": "A",
            "estatisticas": "mediana e MAD do RTT por fluxo_id",
            "piso_rtt_validos": PISO_RTT_VALIDOS,
            "arquivo": "baseline.csv",
        },
        "colunas_proibidas": json.loads((RAIZ / "config" / "arvore.json").read_text(encoding="utf-8"))["colunas_proibidas"],
        "versoes": {"python": platform.python_version(), "scikit-learn": sklearn.__version__,
                    "pandas": pd.__version__, "numpy": np.__version__, "joblib": joblib.__version__},
        "metricas": {"n_treino": int(len(treino)), "n_teste": int(len(teste)),
                     "profundidade": int(modelo.get_depth()), "folhas": int(modelo.get_n_leaves())},
        "exemplo_real": {"fluxo_id": linha["fluxo_id"], "timestamp": str(linha["timestamp"]),
                         "entrada": entrada, "classe_real": linha["classe"], "classe_prevista": previsto},
    }
    (SAIDA / "metadados.json").write_text(json.dumps(completar_metadados(metadados), indent=2, ensure_ascii=False, default=str),
                                          encoding="utf-8")
    (SAIDA / "carregar_modelo.py").write_text(CARREGADOR, encoding="utf-8")

    with zipfile.ZipFile(SAIDA / NOME_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for nome in ("modelo.joblib", "metadados.json", "baseline.csv", "carregar_modelo.py", "requirements.txt", "LEIA-ME.md"):
            zf.write(SAIDA / nome, nome)
    print(f"Pacote gravado em {SAIDA / NOME_ZIP} | exemplo: real={linha['classe']} previsto={previsto}")


if __name__ == "__main__":
    main()
