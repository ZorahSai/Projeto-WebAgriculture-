"""Carga validada e exemplo de inferência. Execute no ambiente de requirements.txt.

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
