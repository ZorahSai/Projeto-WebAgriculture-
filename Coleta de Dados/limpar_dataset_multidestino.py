"""Limpeza do dataset multidestino gerado por " dados_ripe_atlas_.ipynb".

Uso:
    python limpar_dataset_multidestino.py <csv_de_entrada> [csv_de_saida]

O script não sobrescreve um arquivo de saída que já exista.

Correções aplicadas:
- regiao_destino: o arquivo original teve os acentos corrompidos e o texto cortado
  ("Am??rica do", "??sia"). A região é recalculada a partir do país do destino
  (prefixo do FQDN), com o mesmo mapa REGIOES do notebook de coleta.
- Perda total (perda_pacotes_pct == 100): o RIPE Atlas devolve avg = -1 quando nenhum
  pacote volta, e o jitter fica 0 por falta de RTTs. Os dois viram vazio (NaN),
  porque não são medições reais. O status_real continua FALHA por causa da perda.
- A âncora co-bog-as273103 (offline durante toda a janela) é mantida, por decisão
  da equipe, como exemplos de FALHA.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REGIOES = {
    "América do Sul": ["AR", "BO", "BR", "CL", "CO", "EC", "GY", "PY", "PE", "SR", "UY", "VE"],
    "América do Norte": ["US", "CA", "MX", "GT", "CR", "PA", "HN", "SV", "NI", "BZ", "CU", "DO", "JM", "PR", "BS"],
    "Europa": ["AL", "AT", "BA", "BE", "BG", "BY", "CH", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FR",
               "GB", "GR", "HR", "HU", "IE", "IS", "IT", "LI", "LT", "LU", "LV", "MD", "ME", "MK", "MT",
               "NL", "NO", "PL", "PT", "RO", "RS", "SE", "SI", "SK", "UA", "XK"],
    "Ásia": ["JP", "CN", "KR", "IN", "SG", "TH", "ID", "MY", "VN", "PH", "HK", "TW", "BD", "PK", "LK",
             "NP", "KH", "LA", "MM", "MN", "AE", "IL", "SA", "QA", "KW", "IR", "IQ", "JO", "LB", "OM",
             "BH", "AM", "AZ", "GE"],
    "Oceania": ["AU", "NZ", "FJ", "NC", "PG", "PF", "WS", "TO", "VU", "GU"],
    "África": ["ZA", "EG", "NG", "KE", "MA", "TN", "DZ", "GH", "TZ", "UG", "SN", "MU", "RW", "ZM", "ZW",
               "MZ", "CI", "CM"],
}
REGIAO_POR_PAIS = {pais: regiao for regiao, paises in REGIOES.items() for pais in paises}

COLUNAS = ["timestamp", "par_id", "destino_fqdn", "regiao_destino", "prb_id", "pais_origem", "ip",
           "latencia_ms", "perda_pacotes_pct", "jitter_ms", "status_real"]


def limpar(df):
    df = df.copy()

    pais_destino = df["destino_fqdn"].str.split("-").str[0].str.upper()
    df["regiao_destino"] = pais_destino.map(REGIAO_POR_PAIS)
    assert df["regiao_destino"].notna().all(), "Há destino com país fora do mapa REGIOES."
    assert (df["pais_origem"].map(REGIAO_POR_PAIS) == df["regiao_destino"]).all(), \
        "Há origem fora da região do destino."

    perda_total = df["perda_pacotes_pct"] == 100
    df.loc[perda_total, ["latencia_ms", "jitter_ms"]] = np.nan
    assert (df.loc[perda_total, "status_real"] == "FALHA").all()
    assert (df["latencia_ms"].dropna() >= 0).all(), "Ainda há latência negativa."

    return df[COLUNAS].sort_values(["destino_fqdn", "par_id", "timestamp"]).reset_index(drop=True)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    entrada = Path(sys.argv[1])
    saida = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).parent / "RAW" / "dataset_pares_multidestino.csv"
    if saida.exists():
        sys.exit(f"{saida} já existe. Apague o arquivo ou informe outro caminho de saída para não sobrescrever.")

    # O arquivo original não é UTF-8 válido (acentos corrompidos); latin-1 lê qualquer byte.
    df = limpar(pd.read_csv(entrada, encoding="latin-1"))
    df.to_csv(saida, index=False, encoding="utf-8", lineterminator="\n")

    print("CSV limpo salvo em:", saida)
    print("Linhas:", len(df), "| Pares:", df["par_id"].nunique(), "| Destinos:", df["destino_fqdn"].nunique())
    print("Perda total (latência/jitter vazios):", int(df["latencia_ms"].isna().sum()))
    print(df["regiao_destino"].value_counts().to_string())
    print(df["status_real"].value_counts().to_string())


if __name__ == "__main__":
    main()
