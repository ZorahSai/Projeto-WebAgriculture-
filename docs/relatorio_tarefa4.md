# Relatório da Tarefa 4 — ajuste da árvore a partir do erro

Gerado por `src/ajustar_arvore.py` com `config/arvore_tarefa4.json`. Entrada: o mesmo `data/processed/dataset_rotulado_B.csv.gz` da Tarefa 2 (baseline, rótulo e corte intactos). Continua árvore de decisão. **O bloco de teste não foi carregado.**

## 1. Erros da Tarefa 3 que esta tarefa ataca

A árvore oficial da Tarefa 3 (`max_depth` 6, Gini, `min_samples_leaf` 1, 17 folhas) na validação:

| | F1 macro | Recall de FALHA | Recall de RISCO | FALHA→OK | OK→RISCO |
|---|---|---|---|---|---|
| Tarefa 3 | 0,9996 | 0,9984 | 1,0000 | 10 | 1 |

Erros citados no diário da Tarefa 3:

1. **FALHA verdadeira classificada como OK** (10 casos). O RTT da medição atual está no normal do fluxo (`z_robusto` baixo), mas `n5_aumento80` ≥ 2: é a linha 4 da tabela de rótulo. A profundidade 6 não reproduzia esse caminho em todos os casos.
2. **Caminho longo estável classificado como FALHA:** não apareceu na validação da Tarefa 3. Nenhuma mudança foi feita por esse motivo.
3. **OK classificado como RISCO** (1 caso na Tarefa 3). Residual; a árvore ajustada ainda deixa 1 caso. Não foi inventada coluna de rota para “corrigir” isso.

Não entrou coluna nova: `n5_aumento80` já é métrica relativa ao baseline. País, IP, rota e RTT absoluto continuam fora.

## 2. O que mudou (cada mudança cita um erro)

| Erro observado | Mudança |
|---|---|
| 10 FALHA→OK pela linha 4 (`n5_aumento80` ≥ 2 com RTT atual normal) | `max_depth` 6 → 8, para a árvore alcançar o corte em `n5_aumento80` |
| Os mesmos 10 erros, sem inflar a árvore além do necessário | Entre as combinações com F1 e recall de FALHA máximos, ficou `min_samples_leaf` = 10 (19 folhas) |
| Gini vs entropia no mesmo erro | Critério escolhido: **gini**. A outra opção foi testada na grade e não ganhou |
| Os 10 FALHA→OK já cobertos com profundidade 8 | Poda leve `ccp_alpha` = 0.0001: mesma F1 e mesmo recall de FALHA, com menos folhas (19 em vez de 23 sem poda) |

Parâmetros escolhidos **só na validação**. `fit` só no treino (115.804 medições). Validação: 45.842.

## 3. Árvore ajustada

Colunas (as mesmas da Tarefa 3): `z_robusto`, `aumento_pct`, `jitter_relativo`, `perda_pct`, `timeout_atual`, `n5_timeout`, `n5_aumento80`, `n5_risco`.

| Item | Tarefa 3 | Tarefa 4 |
|---|---|---|
| Algoritmo | árvore CART | árvore CART |
| Critério | gini | gini |
| `max_depth` | 6 | 8 |
| `min_samples_leaf` | 1 | 10 |
| `ccp_alpha` | 0 | 0.0001 |
| Profundidade obtida | 6 | 7 |
| Folhas | 17 | 19 |
| Semente | 42 | 42 |

Árvore completa: `results/tarefa4/arvore_ajustada.txt`. Grade: `results/tarefa4/grade_ajuste.csv`.

Primeiras divisões:

- `z_robusto ≤ 3.5` (115.804 amostras)
-   sim → `n5_risco ≤ 1.5` (103.845 amostras)

**Regras** (maior folha de cada classe):

1. se z_robusto ≤ 3.5 e n5_risco ≤ 1.5 e perda_pct ≤ 16.7 e n5_aumento80 ≤ 1.5 e n5_timeout ≤ 2.5, então **OK** (88.757 amostras do treino, 100% dessa classe)
2. se z_robusto ≤ 3.5 e n5_risco > 1.5 e jitter_relativo > 3 e perda_pct ≤ 16.7 e n5_aumento80 ≤ 1.5, então **RISCO** (4.371 amostras do treino, 100% dessa classe)
3. se z_robusto > 3.5 (ou vazio), então **FALHA** (11.959 amostras do treino, 100% dessa classe)

## 4. Comparação na validação

| | F1 macro | Recall de FALHA | Recall de RISCO |
|---|---|---|---|
| Árvore da Tarefa 3 | 0,9996 | 0,9984 | 1,0000 |
| Árvore desta tarefa | 1,0000 | 1,0000 | 1,0000 |

FALHA→OK: 10 → 0. OK→RISCO: 1 → 1.

Matriz 3×3 da árvore desta tarefa:

| real \ previsto | OK | RISCO | FALHA |
|---|---|---|---|
| **OK** | 35.837 | 1 | 0 |
| **RISCO** | 0 | 3.687 | 0 |
| **FALHA** | 0 | 0 | 6.317 |

| Classe | Precisão | Recall | F1 | Suporte |
|---|---|---|---|---|
| OK | 1,000 | 1,000 | 1,000 | 35.838 |
| RISCO | 1,000 | 1,000 | 1,000 | 3.687 |
| FALHA | 1,000 | 1,000 | 1,000 | 6.317 |
| **F1 macro** | | | **1,000** | |

**Caminho longo estável (OK) que a árvore marcou como FALHA:** o caso não apareceu na validação.

**FALHA de caminho curto que a árvore marcou como OK:** o caso não apareceu na validação.

**Leitura do ganho:** a Tarefa 3 já copiava quase toda a tabela de rótulo. O que faltava era o caminho da linha 4. Aumentar a profundidade fecha esses 10 FALHA→OK na validação sem meter RTT absoluto nem rota. A F1 sobe de 0,9996 para 1,0000 e o recall de FALHA vai a 1,0000. Resta 1 OK→RISCO. Isso continua sendo a política da Tarefa 2, não uma falha confirmada em equipamento.

## 5. O que foi tentado e descartado

Foram 24 combinações (`criterio` × `max_depth` × `min_samples_leaf` × `ccp_alpha`).

- **Profundidade 6:** reproduz a Tarefa 3 e deixa os 10 FALHA→OK. Descartada porque o erro pedia mais profundidade.
- **Profundidade 10 (e equivalentes mais folhudas):** 8 linhas da grade com `max_depth` maior que a escolhida e F1 não melhor. Descartadas por parcimônia.
- **Entropia:** nenhuma combinação de entropia zerou os FALHA→OK (sempre restou pelo menos 1). Gini com profundidade 8 foi melhor. Entropia descartada.
- **Poda mais forte ou profundidade 6 com poda:** continuam os FALHA→OK. A poda leve só foi mantida em cima da árvore já profunda, porque reduz folhas sem devolver o erro da linha 4.
- **Coluna relativa nova:** não foi criada. `n5_aumento80` já descreve o erro; o dicionário permanece v0.2.

A Tarefa 5 parte desta árvore. O teste permanece fechado.
