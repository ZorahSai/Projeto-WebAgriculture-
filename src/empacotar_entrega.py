"""Reempacota artefatos existentes; não treina e não abre os dados de teste."""
from pathlib import Path
import zipfile

RAIZ = Path(__file__).resolve().parents[1]
ARQUIVOS = ("modelo.joblib", "metadados.json", "baseline.csv", "carregar_modelo.py", "requirements.txt", "LEIA-ME.md")


def main():
    pasta = RAIZ / "entrega"
    for nome in ARQUIVOS:
        if not (pasta / nome).is_file():
            raise SystemExit(f"Falta o arquivo de entrega: {nome}")
    with zipfile.ZipFile(pasta / "WebAgriculture.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for nome in ARQUIVOS:
            z.write(pasta / nome, nome)
    print("Pacote atualizado:", pasta / "WebAgriculture.zip")


if __name__ == "__main__":
    main()
