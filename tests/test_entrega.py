"""Valida o contrato de entrega e o exemplo real sem treinar ou reabrir o teste."""
import importlib.util
import json
import unittest
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("carregador", RAIZ / "entrega/carregar_modelo.py")
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class EntregaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pacote, cls.meta = MOD.carregar()

    def test_exemplo_real_e_ordem_das_features(self):
        entrada = self.meta["exemplo_real"]["entrada"]
        invertida = dict(reversed(list(entrada.items())))
        self.assertEqual(MOD.prever(invertida, self.pacote), self.meta["exemplo_real"]["classe_prevista"])
        self.assertEqual(self.pacote["modelo"].get_depth(), self.meta["metricas"]["profundidade"])
        self.assertEqual(self.pacote["modelo"].get_n_leaves(), self.meta["metricas"]["folhas"])

    def test_rejeita_features_ausentes_extras_e_nao_finitas(self):
        exemplo = self.meta["exemplo_real"]["entrada"]
        faltante = dict(exemplo)
        faltante.pop("n5_risco")
        for entrada in [faltante, dict(exemplo, extra=1), dict(exemplo, z_robusto=float("nan")),
                        dict(exemplo, jitter_relativo=float("inf")), dict(exemplo, perda_pct="inválido")]:
            with self.subTest(entrada=entrada), self.assertRaises(ValueError):
                MOD.prever(entrada, self.pacote)

    def test_baseline_valido_e_unico_por_fluxo(self):
        import pandas as pd
        baseline = pd.read_csv(RAIZ / "entrega/baseline.csv")
        self.assertFalse(baseline["fluxo_id"].duplicated().any())
        validos = baseline[baseline["valido"]]
        self.assertTrue((validos["n_rtt_validos_A"] >= 1500).all())
        self.assertTrue((validos["mediana"] > 0).all())
        self.assertTrue((validos["recomendacao"] == "usar").all())

    def test_zip_reflete_os_arquivos_da_entrega(self):
        with zipfile.ZipFile(RAIZ / "entrega/WebAgriculture.zip") as z:
            for nome in ["modelo.joblib", "metadados.json", "baseline.csv", "carregar_modelo.py", "requirements.txt", "LEIA-ME.md"]:
                self.assertEqual(z.read(nome), (RAIZ / "entrega" / nome).read_bytes())
            self.assertEqual(json.loads(z.read("metadados.json"))["versao_modelo"], "1.0.0")


if __name__ == "__main__":
    unittest.main()
