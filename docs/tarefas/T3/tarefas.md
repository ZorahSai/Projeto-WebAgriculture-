> Registro organizado para a entrega final em 31/10/2026. Conteúdo preservado do diário existente `docs/diarios/Tarefa3_Arvore_Inicial.md`; não representa um novo histórico de execução.

# Diário da Tarefa 3 — Primeira árvore de decisão

**Período:** 28/09/2026 a 04/10/2026  
**Projeto:** Preditor de degradação de rede com RTT normalizado (independente da rota)

**Equipe:** WebAgriculture (Apollo Moura De Sousa, Icaro Luiz Dellalo Silva, Ieda de Oliveira, João Pedro C. de Morais, Lucas Matteus Baptista de Godoy)  
**Scrum Master da tarefa:** Ieda de Oliveira  
**Repositório GitHub:** https://github.com/ZorahSai/Projeto-WebAgriculture-

### Contrato desta tarefa

| | Artefato | Onde está |
|---|---|---|
| **Entra** | Ficha de baseline, dataset rotulado e corte temporal | `data/processed/` (Tarefa 2, **os mesmos**) |
| **Sai** | Árvore treinada só no treino, com profundidade e critério registrados | `results/tarefa3/arvore_oficial.txt`, `results/tarefa3/metricas_validacao.json` |
| **Sai** | Regras em texto e matriz 3×3 | Seções 2 e 3 abaixo; [`docs/relatorio_tarefa3.md`](../relatorio_tarefa3.md) |
| **Sai** | Árvore de contraste e a frase do que ela aprendeu | Seção 4 abaixo |

Código: `src/treinar_arvore.py`. Parâmetros: `config/arvore.json`.

- [x] **Treino, validação e teste são os da Tarefa 2:** o script usa a coluna `bloco` de `dataset_rotulado_B.csv.gz` sem refazer o corte.
- [x] **A ficha de baseline não foi recalculada com o Período B:** esta tarefa só lê o dataset da Tarefa 2.

---

## 1. Colunas que a árvore oficial pode usar

- [x] **Lista de colunas do treino:**

**Colunas usadas:** `z_robusto`, `aumento_pct`, `jitter_relativo`, `perda_pct`, `timeout_atual`, `n5_timeout`, `n5_aumento80`, `n5_risco`.

**Colunas que não entram:** `pais_origem`, `regiao`, `dst_addr`, `destino_fqdn`, `probe_id`, `fluxo_id`, `latencia_ms`, `jitter_ms`, `mediana`. O script interrompe a execução se alguma delas aparecer na lista da árvore oficial.

- [x] **A classe é o alvo, não uma feature:** `classe` (OK, RISCO, FALHA) é o alvo, e o script confere que ela não está entre as colunas de entrada.

Os valores vazios ficaram vazios, sem trocar por 0:
- `z_robusto` e `aumento_pct` ficam vazios quando há timeout.
- `jitter_relativo` fica vazio quando a rajada teve menos de 2 respostas.

A árvore do scikit-learn trata o valor vazio na divisão e manda a medição para um dos lados. Nas regras, isso aparece como "(ou vazio)".

## 2. A árvore

- [x] **Uma árvore de decisão CART**, com o critério **Gini** (`DecisionTreeClassifier` do scikit-learn).
- [x] **`max_depth` e `min_samples_leaf` escolhidos olhando só a validação:**
  - Foram testadas 32 combinações: `max_depth` em 2, 3, 4, 5, 6, 8, 10 e 12, e `min_samples_leaf` em 1, 10, 50 e 200.
  - Entre as combinações a até 0,005 da melhor F1 macro de validação, ficou a de menos folhas, que é a mais legível.
  - A grade completa está em `results/tarefa3/grade_validacao.csv`.
- [x] **Semente registrada:** `random_state` = 42.
- [x] **`fit` só no treino:** foram 115.804 medições. O bloco de teste **nem é carregado** pelo script.
- [x] **Profundidade real, folhas e primeiras divisões:**
  - Profundidade 6, com 17 folhas.
  - A raiz divide em `z_robusto ≤ 3,5`. Do lado "não", a árvore vai direto para FALHA.
  - Do lado "sim", a próxima divisão é `n5_risco ≤ 1,5`, que separa OK de RISCO.
- [x] **Regras copiadas da árvore**, uma para a maior folha de cada classe.

**Critério, profundidade máxima pedida, profundidade obtida, folhas:** Gini; `max_depth` = 6 e `min_samples_leaf` = 1; profundidade 6; 17 folhas.

**Regras lidas da árvore:**

1. Se `z_robusto` ≤ 3,5 e `n5_risco` ≤ 1,5 e `perda_pct` ≤ 16,7 e `n5_aumento80` ≤ 1,5 e `n5_timeout` ≤ 2,5, então **OK**. São 88.757 medições do treino, 100% OK. Ou seja: RTT dentro de 3,5 desvios do normal do fluxo, sem perda nesta medição e sem sequência de desvios ou timeouts nas últimas 5 medições.
2. Se `z_robusto` ≤ 3,5 e `n5_risco` > 1,5 e `jitter_relativo` > 3 e `perda_pct` ≤ 16,7 e `n5_aumento80` ≤ 1,5 e `n5_timeout` ≤ 2,5, então **RISCO**. São 4.366 medições do treino, 100% RISCO. Ou seja: sem desvio extremo, mas o jitter está mais de 3 vezes acima do típico e o desvio moderado se repetiu nas últimas 5 medições.
3. Se `z_robusto` > 3,5 (ou vazio), então **FALHA**. São 11.959 medições do treino, 100% FALHA. Ou seja: RTT a mais de 3,5 desvios robustos do normal do fluxo, ou sem resposta.

## 3. Leitura do erro

Medido no bloco de **validação** (45.842 medições). O teste continua fechado até a Tarefa 5.

- [x] **Matriz 3×3 com contagem:**

| real \ previsto | OK | RISCO | FALHA |
|---|---|---|---|
| **OK** | 35.837 | 1 | 0 |
| **RISCO** | 0 | 3.687 | 0 |
| **FALHA** | 10 | 0 | 6.307 |

- [x] **Precisão, recall e F1 por classe:**

| Classe | Precisão | Recall | F1 | Suporte |
|---|---|---|---|---|
| OK | 1,000 | 1,000 | 1,000 | 35.838 |
| RISCO | 1,000 | 1,000 | 1,000 | 3.687 |
| FALHA | 1,000 | 0,998 | 0,999 | 6.317 |

- [x] **F1 macro:** 0,9996. Como referência, prever sempre OK dá F1 macro de 0,293.
- [x] **A acurácia sozinha não decide:** prever sempre OK já daria 78,2% de acurácia sem detectar nenhuma FALHA. Por isso a escolha foi pela F1 macro.

**Por que a F1 macro ficou perto de 1:** o rótulo da Tarefa 2 é uma regra fixa calculada com as mesmas 8 colunas que a árvore lê. A árvore reaprende essa política, e seus cortes caem sobre os limiares da tabela de rótulo (`z_robusto` 3,5, `jitter_relativo` 3, `n5_*`). Isso mostra que ela segue o critério relativo, e não a distância. Mas ela aprende a política de rotulagem, não uma falha confirmada em equipamento.

- [x] **Dois erros concretos:**

**Erros concretos:**

1. **Caminho longo estável que caiu em FALHA:** o caso **não apareceu** na validação. Nenhuma medição OK dos fluxos mais longos (quartil de maior mediana) foi marcada como FALHA.
2. **FALHA de caminho curto que caiu em OK:** foram 6 casos na validação. Exemplo:

| Fluxo | Timestamp (UTC) | Mediana do fluxo | RTT | `z_robusto` | `aumento_pct` | `n5_aumento80` | `n5_risco` | Classe verdadeira | Classe da árvore |
|---|---|---|---|---|---|---|---|---|---|
| `6509\|85.236.41.237` (IT → de-muc) | 17/09 11:53:48 | 23,02 ms | 22,85 ms | −2,59 | −0,72 | 2 | 4 | FALHA | OK |

O RTT desta medição está normal. Ela é FALHA pela linha 4 da tabela, porque duas das últimas 5 medições tiveram aumento acima de 80%. A árvore oficial, limitada à profundidade 6, não reproduz essa combinação em todos os casos. Esse é um ponto para a Tarefa 4 olhar, junto com os 10 FALHA que viraram OK.

## 4. Árvore de contraste (não é o modelo)

Duas árvores treinadas no mesmo treino e com os mesmos parâmetros da oficial.

- [x] **Divisão perto da raiz:**
  - **Contraste A, métricas relativas mais RTT e jitter absolutos:** a raiz continua `z_robusto ≤ 3,5`, e a árvore **não usou** nenhuma coluna em milissegundos (importância 0). Com o desvio em relação ao baseline disponível, o RTT absoluto não acrescenta nada. A F1 macro na validação é de 1,000.
  - **Contraste B, só medidas absolutas** (`latencia_ms`, `jitter_ms`, `perda_pct` e `timeout_atual`, como na regra antiga): a raiz é `jitter_ms ≤ 0,342 ms` e o nível seguinte é `latencia_ms ≤ 149 ms`. São cortes fixos em milissegundos. A `latencia_ms` sozinha responde por 62% da importância, e a F1 macro na validação cai para **0,510**.
- [x] **Essa árvore fica fora da entrega final.** As duas árvores de contraste servem só para mostrar o atalho da distância.

**O que a árvore de contraste usou na raiz:** sem o desvio em relação ao baseline, a árvore passa a cortar em milissegundos fixos (`jitter_ms ≤ 0,342`, depois `latencia_ms ≤ 149`). Ela aprende o comprimento do caminho em vez da degradação de cada fluxo, e a F1 macro cai de 0,9996 para 0,510.

## 5. Scrum e diário

- [ ] Board atualizado [a preencher pela equipe]

| Integrante | O que fiz nesta tarefa | Dificuldades | O que pretendo manter/ajustar |
|---|---|---|---|
| Apollo Moura De Sousa | [a preencher] | [a preencher] | [a preencher] |
| Icaro Luiz Dellalo Silva | [a preencher] | [a preencher] | [a preencher] |
| Ieda de Oliveira | [a preencher] | [a preencher] | [a preencher] |
| João Pedro C. de Morais | [a preencher] | [a preencher] | [a preencher] |
| Lucas Matteus Baptista de Godoy | [a preencher] | [a preencher] | [a preencher] |

Pontos técnicos para a equipe aproveitar no diário:
- A F1 próxima de 1 se explica pelo rótulo ter sido feito com as mesmas métricas.
- Mudanças de patamar de rota (por exemplo `7399 → de-mdt`) viram FALHA pela regra, como discutido na Tarefa 2.
- A Tarefa 4 pode atacar os 10 FALHA que viraram OK, ligados à linha 4 da tabela (`n5_aumento80`).
