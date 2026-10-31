"""Descrições do contrato do modelo, compartilhadas pelo exportador e pela revisão."""
from copy import deepcopy


def completar_metadados(originais):
    meta = deepcopy(originais)
    meta.update({
        "nome_modelo": "WebAgri-RTT-CART-T5",
        "versao_modelo": "1.0.0",
        "versao_contrato": "1.0.0",
        "identificacao_artefato": "árvore final T5 com parâmetros congelados escolhidos na validação; nome do artefato: modelo.joblib",
    })
    formulas = {
        "z_robusto": "desvio = latencia_ms - mediana_A; denominador = 1.4826*MAD_A se MAD_A>0, senão max(IQR_A/1.349, 1.0 ms); z = desvio/denominador. Se MAD_A=0 e desvio=0, z=0; sem RTT, NaN",
        "aumento_pct": "(latencia_ms - mediana_A) / mediana_A * 100; requer mediana_A > 0 e finita para a interface de entrega",
        "jitter_relativo": "jitter_ms / jitter_tipico_A; se ambos são 0, retorna 1.0; se típico=0 e atual>0, retorna +inf; se jitter atual ausente, NaN",
        "perda_pct": "pacotes perdidos / pacotes enviados * 100; pacotes enviados deve ser >0; sem denominador válido, não classificar",
        "timeout_atual": "1 se a medição não tem RTT ou perda_pct=100, senão 0",
        "n5_timeout": "soma de timeout_atual nas últimas 5 medições ordenadas do mesmo fluxo, incluindo a atual; min_periods=1 no pipeline",
        "n5_aumento80": "contagem de aumento_pct > 80 nas últimas 5 medições do fluxo, incluindo a atual; corte estrito, não >=80",
        "n5_risco": "soma do critério moderado, ANTES do rótulo final, nas últimas 5 medições do fluxo: (2<=z_robusto<3.5) OU (30<=aumento_pct<=80) OU (jitter_relativo>=3); inclui a atual",
    }
    for entrada in meta["entradas"]:
        entrada["formula"] = formulas[entrada["nome"]]
    meta["faltantes_e_divisao_por_zero"] = {
        "sem_rtt": "z_robusto e aumento_pct ficam NaN; timeout_atual=1. A interface carregar_modelo.py rejeita entradas não finitas sem substituir por zero ou imputar",
        "mad_zero": "usar max(IQR_A/1.349, 1.0 ms); se também desvio=0, z_robusto=0",
        "mediana_zero_ou_invalida": "não classificar pela interface de entrega; requer baseline válido com mediana positiva",
        "jitter_tipico_zero": "jitter atual zero: 1.0; positivo: +inf; atual ausente: NaN",
        "inf_nan_na_interface": "rejeitar a medição com ValueError e manter sem classificação; não transformar +inf em zero nem fabricar rótulo. O script exemplifica inferência somente para vetores finitos. Isso não redefine o cálculo de features do pipeline",
        "pacotes_enviados_zero": "não calcular perda nem classificar essa medição",
        "baseline_ausente_ou_invalido": "não classificar pelo modelo normalizado; coletar/calibrar antes e respeitar a recomendação do baseline.csv",
    }
    meta["historico_necessario"] = "5 medições ordenadas por timestamp de um mesmo fluxo, incluindo a atual. No dataset, rolling(5,min_periods=1); as 4 primeiras medições de validação/teste ficam em embargo. Para uso operacional com janela completa, aguardar 5 medições antes de classificar"
    meta["regras_baseline"]["periodo_utc"] = {"inicio": "2026-09-06T04:32:00Z", "fim": "2026-09-13T04:32:00Z"}
    meta["regras_baseline"]["validacao_interface"] = "valido=true, recomendacao=usar, mediana positiva e referências necessárias finitas; manter ficha congelada para não vazar informação futura"
    meta["preparacao"] = ["Identificar fluxo e ordenar timestamps", "Consultar ficha válida do Período A", "Calcular as métricas relativas conforme fórmulas de entradas", "Calcular critério de risco moderado e janelas por fluxo", "Preservar nomes e ordem das oito entradas", "Rejeitar entradas não finitas na interface de entrega", "Aplicar modelo.predict e interpretar classe atual"]
    meta["interpretacao"] = "OK: nenhuma ação pela política; RISCO: observar; FALHA: investigar. Classes heurísticas de degradação atual, não confirmação de defeito físico nem previsão futura"
    return meta
