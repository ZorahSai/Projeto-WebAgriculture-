"""Exemplo de carga do modelo de entrega."""
import json
from pathlib import Path

import joblib
import pandas as pd

AQUI = Path(__file__).resolve().parent
pacote = joblib.load(AQUI / "modelo.joblib")
meta = json.loads((AQUI / "metadados.json").read_text(encoding="utf-8"))

modelo, features = pacote["modelo"], pacote["features"]
exemplo = pd.DataFrame([meta["exemplo_real"]["entrada"]])[features]
print("Classes:", list(modelo.classes_))
print("Previsto:", modelo.predict(exemplo)[0], "| esperado:", meta["exemplo_real"]["classe_real"])
