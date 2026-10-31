# Pacote de entrega — WebAgriculture

Ciência da Computação · Universidade Brás Cubas.

O arquivo `WebAgriculture.zip` deve ser enviado ao Blackboard até **04/11/2026**, conforme o PDF da professora. Este arquivo não confirma envio.

- `modelo.joblib`: dicionário com `modelo`, `features`, `familia`, `params`.
- `metadados.json`: nome/versão, entradas em ordem, fórmulas, casos especiais, saídas/classes, horizonte atual, histórico, baseline e exemplo real.
- `baseline.csv`: ficha de cada fluxo, validade e recomendação.
- `carregar_modelo.py`: valida o contrato e executa o exemplo de inferência, sem retreinar.
- `requirements.txt`: versões das bibliotecas da entrega.

Use **Python 3.14.7**, em um ambiente virtual limpo:

```sh
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python carregar_modelo.py
```

Resultado esperado do exemplo: `OK`. Use somente arquivos joblib de origem confiável.

A interface de exemplo rejeita entradas faltantes, NaN e infinitos, sem preencher com zero e sem fabricar classe. O cálculo bruto de jitter pode produzir infinito quando o típico é zero; esse caso deve permanecer sem classificação por esta interface. A validação do baseline e o aquecimento de cinco medições devem ocorrer antes da inferência operacional. O pacote não inclui um dashboard de monitoramento ao vivo.

O modelo já existente foi preservado. As correções desta entrega são de contrato, documentação e validação da carga; não houve novo treino nem nova escolha pelo bloco de teste.
