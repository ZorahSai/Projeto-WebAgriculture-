# Relatório da Tarefa 3 — primeira árvore de decisão

Gerado por `src/treinar_arvore.py` com `config/arvore.json`. Entrada: `data/processed/dataset_rotulado_B.csv.gz` da Tarefa 2 (mesmo baseline, mesmo rótulo, mesmo corte). A ficha de baseline não foi recalculada.

## 1. Colunas da árvore oficial

`z_robusto`, `aumento_pct`, `jitter_relativo`, `perda_pct`, `timeout_atual`, `n5_timeout`, `n5_aumento80`, `n5_risco`

O alvo é `classe` (OK, RISCO, FALHA), que não é coluna de entrada. Ficam de fora: `pais_origem`, `regiao`, `dst_addr`, `destino_fqdn`, `probe_id`, `fluxo_id`, `latencia_ms`, `jitter_ms`, `mediana`.

Treino: 115.804 medições. Validação: 45.842 medições. **O bloco de teste não foi carregado.**

## 2. A árvore

| Item | Valor |
|---|---|
| Algoritmo | Árvore de decisão CART (`DecisionTreeClassifier`, scikit-learn) |
| Critério | gini |
| `max_depth` escolhido | 6 |
| `min_samples_leaf` escolhido | 1 |
| Profundidade obtida | 6 |
| Folhas | 17 |
| Semente | 42 |
| Ajuste (`fit`) | só no treino |

Como os parâmetros foram escolhidos: 32 combinações de `max_depth` × `min_samples_leaf`, treinadas no treino e comparadas pela F1 macro **na validação**. Entre as que ficaram a até 0,005 da melhor F1 macro, ficou a árvore com menos folhas, que é a mais fácil de ler. As 8 melhores:

| max_depth | min_samples_leaf | profundidade_real | folhas | f1_macro_validacao | recall_falha_validacao | recall_risco_validacao |
|---|---|---|---|---|---|---|
| 10 | 1 | 9 | 25 | 1,0000 | 1,0000 | 1,0000 |
| 10 | 10 | 9 | 25 | 1,0000 | 1,0000 | 1,0000 |
| 12 | 10 | 9 | 25 | 1,0000 | 1,0000 | 1,0000 |
| 12 | 1 | 9 | 25 | 1,0000 | 1,0000 | 1,0000 |
| 8 | 1 | 8 | 24 | 1,0000 | 1,0000 | 1,0000 |
| 8 | 10 | 8 | 23 | 1,0000 | 1,0000 | 1,0000 |
| 6 | 10 | 6 | 17 | 0,9996 | 0,9984 | 1,0000 |
| 6 | 1 | 6 | 17 | 0,9996 | 0,9984 | 1,0000 |

Primeiras divisões:

- `z_robusto ≤ 3.5` (115.804 amostras)
-   sim → `n5_risco ≤ 1.5` (103.845 amostras)

Regras lidas da árvore (a folha com mais amostras de cada classe). A árvore completa está em `results/tarefa3/arvore_oficial.txt`.

1. se z_robusto ≤ 3.5 e n5_risco ≤ 1.5 e perda_pct ≤ 16.7 e n5_aumento80 ≤ 1.5 e n5_timeout ≤ 2.5, então **OK** (88.757 amostras do treino, 100% dessa classe)
2. se z_robusto ≤ 3.5 e n5_risco > 1.5 e jitter_relativo > 3 e perda_pct ≤ 16.7 e n5_aumento80 ≤ 1.5 e n5_timeout ≤ 2.5, então **RISCO** (4.366 amostras do treino, 100% dessa classe)
3. se z_robusto > 3.5 (ou vazio), então **FALHA** (11.959 amostras do treino, 100% dessa classe)

## 3. Leitura do erro (validação)

Matriz 3×3 (contagem):

| real \ previsto | OK | RISCO | FALHA |
|---|---|---|---|
| **OK** | 35.837 | 1 | 0 |
| **RISCO** | 0 | 3.687 | 0 |
| **FALHA** | 10 | 0 | 6.307 |

| Classe | Precisão | Recall | F1 | Suporte |
|---|---|---|---|---|
| OK | 1,000 | 1,000 | 1,000 | 35.838 |
| RISCO | 1,000 | 1,000 | 1,000 | 3.687 |
| FALHA | 1,000 | 0,998 | 0,999 | 6.317 |
| **F1 macro** | | | **1,000** | |

Referência: prever sempre `OK` dá F1 macro **0,293** e acurácia 78,2%. A acurácia da árvore é 100,0%, mas ela não decide nada aqui: com maioria OK, ela fica alta mesmo errando FALHA.

**Por que a F1 macro fica tão alta:** o rótulo da Tarefa 2 é uma regra fixa calculada com estas mesmas 8 colunas. A árvore reaprende essa política: seus cortes caem sobre os limiares da tabela de rótulo (`z_robusto` 2 e 3,5, perda de 10%, `n5_*`). Isso mostra que ela segue o critério relativo, e não a distância. Mas ela aprende a política de rotulagem, não uma falha confirmada de equipamento.

Medições OK de caminho longo (quartil de maior mediana) que a árvore oficial marcou como FALHA: 0,0%.

**Caminho longo estável (OK) que a árvore marcou como FALHA:** o caso não apareceu na validação.

**FALHA de caminho curto que a árvore marcou como OK:** 6 casos na validação. Exemplo:

| timestamp | fluxo_id | mediana | latencia_ms | z_robusto | aumento_pct | jitter_relativo | perda_pct | n5_timeout | n5_aumento80 | n5_risco | classe | previsto |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 17/09 11:53:48 | 6509\|85.236.41.237 | 23,02 | 22,85 | -2,59 | -0,72 | 1,54 | 0,00 | 0 | 2 | 4 | FALHA | OK |

## 4. Árvore de contraste (não é o modelo)

Treinadas no mesmo treino e com os mesmos parâmetros, só para mostrar o atalho da distância. **Ficam fora da entrega final.**

### Contraste: relativas + RTT absoluto

- **Divisão na raiz:** `z_robusto ≤ 3.5`
- **Primeiras divisões:**
  - `z_robusto ≤ 3.5` (115.804 amostras)
  -   sim → `n5_risco ≤ 1.5` (103.845 amostras)
- **Importância dos atributos:** `z_robusto` 0,66, `n5_risco` 0,20, `jitter_relativo` 0,08, `perda_pct` 0,03, `aumento_pct` 0,03, `n5_aumento80` 0,00, `n5_timeout` 0,00
- **F1 macro na validação:** 1,000
- **Medições OK de caminho longo marcadas como FALHA:** 0,0%
- **O que ela aprendeu:** com as métricas relativas disponíveis, a árvore não usou nenhuma coluna em milissegundos (F1 macro 1,000, contra 1,000 da árvore oficial). O RTT absoluto não acrescenta nada quando o desvio em relação ao baseline já está presente.

### Contraste: só medidas absolutas

- **Divisão na raiz:** `jitter_ms ≤ 0.342`
- **Primeiras divisões:**
  - `jitter_ms ≤ 0.342` (115.804 amostras)
  -   sim → `latencia_ms ≤ 149` (89.571 amostras)
  -   não → `perda_pct ≤ 16.7` (26.233 amostras)
- **Importância dos atributos:** `latencia_ms` 0,62, `jitter_ms` 0,29, `perda_pct` 0,09
- **F1 macro na validação:** 0,510
- **Medições OK de caminho longo marcadas como FALHA:** 1,2%
- **O que ela aprendeu:** sem o desvio em relação ao baseline, a árvore passa a cortar em milissegundos fixos (`jitter_ms ≤ 0.342`, no nível 1), ou seja, aprende o comprimento do caminho em vez da degradação de cada fluxo (F1 macro 0,510, contra 1,000 da árvore oficial).
